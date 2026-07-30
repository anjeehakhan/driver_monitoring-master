# driver_monitoring-master/dms.py

import winsound
import cv2
import numpy as np
import torch
import tensorflow as tf
from datetime import datetime

from dms_utils.dms_utils import ACTIONS
from net import MobileNet
from facial_tracking.facialTracking import FacialTracker
import facial_tracking.conf as conf


def infer_one_frame(image, model, yolo_model, facial_tracker):
    """Ek frame process karo — detections karo aur result return karo"""

    eyes_status = ''
    yawn_status = ''
    action = ''

    facial_tracker.process_frame(image)

    if facial_tracker.detected:
        eyes_status = facial_tracker.eyes_status
        yawn_status = facial_tracker.yawn_status

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    yolo_result = yolo_model(rgb_image)

    rgb_resized = cv2.resize(rgb_image, (224, 224))
    rgb_resized = tf.expand_dims(rgb_resized, 0)

    y = model.predict(rgb_resized, verbose=0)
    result = np.argmax(y, axis=1)

    if result[0] == 0 and yolo_result.xyxy[0].shape[0] > 0:
        action = list(ACTIONS.keys())[result[0]]
    if result[0] == 1 and eyes_status == 'eye closed':
        action = list(ACTIONS.keys())[result[0]]

    # Screen par text dikhao
    cv2.putText(image, f'Eyes: {eyes_status}',  (30, 40),  0, 0.8, conf.LM_COLOR,   2, cv2.LINE_AA)
    cv2.putText(image, f'Mouth: {yawn_status}', (30, 80),  0, 0.8, conf.CT_COLOR,   2, cv2.LINE_AA)
    cv2.putText(image, f'Action: {action}',     (30, 120), 0, 0.8, conf.WARN_COLOR, 2, cv2.LINE_AA)

    return image, eyes_status, yawn_status, action


def detect_distraction(facial_tracker, frame_width):
    """
    Driver ka chehra center se zyada side mein ho toh distracted maano
    """
    if not facial_tracker.detected:
        return False
    try:
        # Nose landmark ka x position check karo
        nose_x = facial_tracker.landmarks[1].x * frame_width
        center = frame_width / 2
        deviation = abs(nose_x - center)
        # Agar 30% se zyada side mein hai toh distracted
        if deviation > frame_width * 0.30:
            return True
    except Exception:
        pass
    return False


def run_detection(checkpoint, driver_id=1, on_violation=None):
    """
    Main detection loop.

    Parameters:
    - checkpoint  : model weights ka path
    - driver_id   : logged-in driver ka DB id
    - on_violation: callback — jab violation ho toh call ho
                    on_violation(driver_id, violation_type)
    """

    # ── Models Load karo ──
    model = MobileNet()
    model.load_weights(checkpoint)

    # Phone detection
    yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    yolo_model.classes = [67]  # 67 = cell phone

    # Seatbelt detection (alag instance, sab classes)
    seatbelt_yolo = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    seatbelt_yolo.classes = None

    facial_tracker = FacialTracker()

    # ── Counts ──
    sleepy_count        = 0
    phone_count         = 0
    yawn_count          = 0
    seatbelt_count      = 0
    distraction_count   = 0
    alert_count         = 0
    closed_eyes_frames  = 0
    yawn_frames         = 0   # yawn fix — frames count
    distraction_frames  = 0   # distraction frames count

    # ── Camera ──
    cap = cv2.VideoCapture(0)
    cap.set(3, conf.FRAME_W)
    cap.set(4, conf.FRAME_H)

    frame_width = int(cap.get(3))

    print("✅ Detection shuru ho gayi — 'q' press karo band karne ke liye")

    while True:
        success, image = cap.read()
        if not success:
            break

        image = cv2.flip(image, 1)

        # Frame process karo
        image, eyes_status, yawn_status, action = infer_one_frame(
            image, model, yolo_model, facial_tracker
        )

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # ── Drowsiness Check ──
        if facial_tracker.detected:
            if 'closed' in eyes_status.lower():
                closed_eyes_frames += 1
            else:
                closed_eyes_frames = 0

            if closed_eyes_frames > 15:
                sleepy_count       += 1
                alert_count        += 1
                closed_eyes_frames  = 0
                winsound.Beep(1500, 700)
                if on_violation:
                    on_violation(driver_id, "drowsiness")

        # ── Yawn Check (FIX — frames count karo) ──
        if 'yawn' in yawn_status.lower():
            yawn_frames += 1
        else:
            yawn_frames = 0

        if yawn_frames == 10:  # 10 frames tak yawning rahi toh count karo
            yawn_count  += 1
            alert_count += 1
            winsound.Beep(700, 400)
            if on_violation:
                on_violation(driver_id, "yawn")

        # ── Phone Check ──
        phone_result = yolo_model(rgb)
        if phone_result.xyxy[0].shape[0] > 0:
            phone_count += 1
            alert_count += 1
            winsound.Beep(900, 400)
            if on_violation:
                on_violation(driver_id, "phone")

        # ── Seatbelt Check ──
        if facial_tracker.detected:  # driver present hai
            seatbelt_result  = seatbelt_yolo(rgb)
            seatbelt_worn    = False

            for *box, conf_score, cls in seatbelt_result.xyxy[0]:
                # COCO class 27 = tie (seatbelt proxy)
                if int(cls) == 27:
                    seatbelt_worn = True
                    break

            if not seatbelt_worn:
                seatbelt_count += 1
                alert_count    += 1
                winsound.Beep(600, 300)
                if on_violation:
                    on_violation(driver_id, "seatbelt")

        # ── Distraction Check ──
        if detect_distraction(facial_tracker, frame_width):
            distraction_frames += 1
        else:
            distraction_frames = 0

        if distraction_frames == 20:  # 20 frames tak side mein dekha
            distraction_count  += 1
            alert_count        += 1
            winsound.Beep(1000, 500)
            if on_violation:
                on_violation(driver_id, "distraction")

        # ── Counts Display ──
        cv2.putText(image, f'Sleepy:      {sleepy_count}',      (30, 160), 0, 0.7, (0, 255, 255), 2)
        cv2.putText(image, f'Phone:       {phone_count}',       (30, 195), 0, 0.7, (0, 255, 255), 2)
        cv2.putText(image, f'Yawn:        {yawn_count}',        (30, 230), 0, 0.7, (0, 255, 255), 2)
        cv2.putText(image, f'Seatbelt:    {seatbelt_count}',    (30, 265), 0, 0.7, (0, 165, 255), 2)
        cv2.putText(image, f'Distraction: {distraction_count}', (30, 300), 0, 0.7, (0, 165, 255), 2)
        cv2.putText(image, f'Alerts:      {alert_count}',       (30, 335), 0, 0.7, (0, 0,   255), 2)

        cv2.imshow('DMS — Driver Monitor', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # ── Final Summary ──
    print("\n===== SESSION REPORT =====")
    print(f"Sleepy Alerts      : {sleepy_count}")
    print(f"Phone Alerts       : {phone_count}")
    print(f"Yawn Alerts        : {yawn_count}")
    print(f"Seatbelt Alerts    : {seatbelt_count}")
    print(f"Distraction Alerts : {distraction_count}")
    print(f"Total Alerts       : {alert_count}")

    return {
        "sleepy":       sleepy_count,
        "phone":        phone_count,
        "yawn":         yawn_count,
        "seatbelt":     seatbelt_count,
        "distraction":  distraction_count,
        "total":        alert_count
    }


# ── Direct run karne ke liye (testing) ──
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', type=str, required=True)
    args = parser.parse_args()
    run_detection(checkpoint=args.checkpoint)