import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose

class SeatbeltDetector:
    def __init__(self):
        self._create_pose()
        self.shoulders_visible = False

    def _create_pose(self):
        self.pose = mp_pose.Pose(
            static_image_mode=True,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def process_frame(self, frame):
        self.shoulders_visible = False
        try:
            rgb = frame[:, :, ::-1].copy()
            results = self.pose.process(rgb)
        except Exception:
            try:
                self.pose.close()
            except Exception:
                pass
            self._create_pose()
            return None

        if not results.pose_landmarks:
            return None

        lm = results.pose_landmarks.landmark
        left_shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]

        if left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5:
            return None

        self.shoulders_visible = True
        return lm