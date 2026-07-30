from flask import Flask, request, jsonify
from flask_cors import CORS
from database import create_db, add_driver, log_violation, get_violations, get_violation_counts, start_trip, end_trip, get_all_trips, find_driver_by_license
import numpy as np
import cv2
from datetime import datetime
import torch
import tensorflow as tf
from dms_utils.dms_utils import ACTIONS
from net import MobileNet
from facial_tracking.facialTracking import FacialTracker
import facial_tracking.conf as conf
from seatbelt_pose import SeatbeltDetector
from seatbelt_heuristic import SeatbeltHeuristic
import mediapipe as mp
mp_pose = mp.solutions.pose

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

create_db()

print("Loading models...")
model = MobileNet()
model.load_weights("models/model_split.h5")

yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
yolo_model.classes = [67]


facial_tracker = FacialTracker()
seatbelt_detector = SeatbeltDetector()
seatbelt_heuristic = SeatbeltHeuristic()
print("✅ Models loaded!")

current_driver_state = {"state": "Focused"}
detection_results = {
    "sleepy": 0, "phone": 0, "yawn": 0,
    "seatbelt": 0, "total": 0
}
current_driver_id = 1
current_trip_id = None
trip_active = False
trip_start_time = None

closed_eyes_frames = 0
yawn_frames = 0
no_seatbelt_frames = 0


def process_incoming_frame(frame):
    global closed_eyes_frames, yawn_frames, no_seatbelt_frames
    global current_driver_state, detection_results

    state = "Focused"
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]

    facial_tracker.process_frame(frame)

    if facial_tracker.detected:
        try:
            print(f"Mouth ratio: {facial_tracker.lips.mouth_open_ratio:.3f}")
        except:
            pass

    eyes_status = ''
    yawn_status = ''
    if facial_tracker.detected:
        eyes_status = facial_tracker.eyes_status
        yawn_status = facial_tracker.yawn_status

    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ── Drowsiness ──
    if facial_tracker.detected:
        if 'closed' in eyes_status.lower():
            closed_eyes_frames += 2
        else:
            closed_eyes_frames = max(0, closed_eyes_frames - 1)

        if closed_eyes_frames > 1:
            detection_results["sleepy"] += 1
            detection_results["total"] += 1
            closed_eyes_frames = 0
            if state == "Focused":
                state = "drowsiness"
            _log("drowsiness")

    # ── Yawn ──
    if 'yawn' in yawn_status.lower():
        yawn_frames += 2
    else:
        yawn_frames = max(0, yawn_frames - 1)

    if yawn_frames >= 3:
        detection_results["yawn"] += 1
        detection_results["total"] += 1
        yawn_frames = 0
        if state == "Focused":
            state = "yawn"
        _log("yawn")

    # ── Phone ──
    phone_result = yolo_model(rgb_image)
    if phone_result.xyxy[0].shape[0] > 0:
        detection_results["phone"] += 1
        detection_results["total"] += 1
        if state == "Focused":
            state = "phone"
        _log("phone")

    # ── Seatbelt (pose landmarks + edge heuristic) ──
    pose_lm = seatbelt_detector.process_frame(frame)
    seatbelt_result = None

    if pose_lm is not None:
        ls = pose_lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
        rs = pose_lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        lh = pose_lm[mp_pose.PoseLandmark.LEFT_HIP]
        rh = pose_lm[mp_pose.PoseLandmark.RIGHT_HIP]

        shoulder_left_px = (int(ls.x * frame_width), int(ls.y * frame_height))
        shoulder_right_px = (int(rs.x * frame_width), int(rs.y * frame_height))
        hip_left_px = (int(lh.x * frame_width), int(lh.y * frame_height))
        hip_right_px = (int(rh.x * frame_width), int(rh.y * frame_height))

        seatbelt_result = seatbelt_heuristic.check_seatbelt(
            frame, shoulder_left_px, shoulder_right_px, hip_left_px, hip_right_px
        )

    print(f"Seatbelt result: {seatbelt_result}")

    if seatbelt_result is False:
        no_seatbelt_frames += 1
    else:
        no_seatbelt_frames = max(0, no_seatbelt_frames - 1)

    if no_seatbelt_frames >= 3:
        detection_results["seatbelt"] += 1
        detection_results["total"] += 1
        no_seatbelt_frames = 0
        if state == "Focused":
            state = "seatbelt"
        _log("seatbelt")

    current_driver_state["state"] = state


def _log(violation_type):
    if trip_active:
        log_violation(current_driver_id, violation_type, trip_id=current_trip_id)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "state": current_driver_state["state"],
        "results": detection_results,
        "trip_active": trip_active
    })


@app.route('/frame', methods=['POST', 'OPTIONS'])
def receive_frame():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        img_bytes = request.get_data()
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({"error": "Invalid frame"}), 400
        process_incoming_frame(frame)
        return jsonify({"status": "ok"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.get_json()
    name = data.get('name', 'Driver')
    license_no = data.get('license_no', '')

    existing = find_driver_by_license(license_no)
    global current_driver_id

    if existing:
        driver_id = existing['id']
        current_driver_id = driver_id
        return jsonify({
            "driver_id": driver_id,
            "name": existing['name'],
            "message": "Welcome back!",
            "is_new": False
        })
    else:
        driver_id = add_driver(name, license_no)
        current_driver_id = driver_id
        return jsonify({
            "driver_id": driver_id,
            "name": name,
            "message": "Account created!",
            "is_new": True
        })


@app.route('/start_trip', methods=['POST', 'OPTIONS'])
def start_trip_route():
    if request.method == 'OPTIONS':
        return '', 200
    global current_trip_id, trip_active, trip_start_time, detection_results
    data = request.get_json()
    driver_id = data.get('driver_id', current_driver_id)
    trip_id = start_trip(driver_id)
    current_trip_id = trip_id
    trip_active = True
    trip_start_time = datetime.now()
    detection_results = {
        "sleepy": 0, "phone": 0, "yawn": 0,
        "seatbelt": 0, "total": 0
    }
    return jsonify({
        "trip_id": trip_id,
        "start_time": str(trip_start_time),
        "message": "Trip started!"
    })


@app.route('/end_trip', methods=['POST', 'OPTIONS'])
def end_trip_route():
    if request.method == 'OPTIONS':
        return '', 200
    global current_trip_id, trip_active
    if not current_trip_id:
        return jsonify({"error": "No active trip"}), 400
    report = end_trip(current_trip_id)
    trip_active = False
    current_trip_id = None
    return jsonify(report)


@app.route('/history', methods=['GET'])
def get_history():
    driver_id = request.args.get('driver_id', current_driver_id)
    violations = get_violations(int(driver_id))
    counts = get_violation_counts(int(driver_id))
    trips = get_all_trips(int(driver_id))
    return jsonify({"violations": violations, "counts": counts, "trips": trips})


def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    run_server()