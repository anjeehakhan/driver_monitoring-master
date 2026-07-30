import cv2
import numpy as np

class SeatbeltHeuristic:
    def check_seatbelt(self, frame, shoulder_left, shoulder_right, hip_left, hip_right):
        """
        shoulder_left, shoulder_right, hip_left, hip_right: (x, y) pixel tuples
        Returns True if seatbelt-like diagonal line detected, False otherwise
        """
        h, w = frame.shape[:2]

        x1 = min(shoulder_left[0], shoulder_right[0], hip_left[0], hip_right[0])
        x2 = max(shoulder_left[0], shoulder_right[0], hip_left[0], hip_right[0])
        y1 = min(shoulder_left[1], shoulder_right[1])
        y2 = max(hip_left[1], hip_right[1])

        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return None

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return None

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 40, 120)

        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180,
            threshold=30, minLineLength=int(roi.shape[0] * 0.3),
            maxLineGap=15
        )

        if lines is None:
            return False

        for line in lines:
            lx1, ly1, lx2, ly2 = line[0]
            angle = abs(np.degrees(np.arctan2(ly2 - ly1, lx2 - lx1)))
            if 20 < angle < 70 or 110 < angle < 160:
                return True

        return False