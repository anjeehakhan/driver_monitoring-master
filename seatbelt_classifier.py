import cv2
import numpy as np
import torch
import tensorflow as tf
from tensorflow.keras.models import load_model

CLASS_NAMES = {0: "No Seatbelt worn", 1: "Seatbelt Worn"}
THRESHOLD_SCORE = 0.90

class SeatbeltClassifier:
    def __init__(self):
        self.detector = torch.hub.load(
            "ultralytics/yolov5", "custom",
            path="seatbelt_model/best.pt",
            force_reload=False
        )
        self.predictor = load_model(
            "seatbelt_model/converted_keras/keras_model.h5",
            compile=False
        )

    def _predict_crop(self, img_crop):
        img = cv2.resize(img_crop, (224, 224), interpolation=cv2.INTER_AREA)
        img = (img / 127.5) - 1
        img = tf.expand_dims(img, axis=0)
        pred = self.predictor.predict(img, verbose=0)
        index = int(np.argmax(pred))
        class_name = CLASS_NAMES[index]
        confidence = float(pred[0][index])
        return index, class_name, confidence

    def check_seatbelt(self, frame):
        """Returns True if seatbelt worn, False if not, None if no person detected"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.detector(rgb)
        boxes = results.xyxy[0].cpu().numpy()

        if len(boxes) == 0:
            return None

        best_box = boxes[0]
        x1, y1, x2, y2 = int(best_box[0]), int(best_box[1]), int(best_box[2]), int(best_box[3])
        img_crop = rgb[y1:y2, x1:x2]

        if img_crop.size == 0:
            return None

        index, class_name, confidence = self._predict_crop(img_crop)

        if confidence < THRESHOLD_SCORE:
            return None

        return index == 1