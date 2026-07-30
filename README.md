# Driver Monitoring System

This project is designed to monitor a driver's status and behavior in real time, including drowsiness, yawning, phone usage, texting, and seatbelt detection using AI and computer vision.

## Architecture

The Driver Monitoring System consists of two main components:

- **Facial Tracking:** Uses MediaPipe to detect facial landmarks and monitor eye status (open/closed), gaze direction (left, right, center), and yawning.
- **Action Detection:** Uses deep learning models to detect driver activities such as phone calls, texting, and seatbelt usage. YOLOv5 is used for object detection to improve accuracy.

## Requirements

```text
python=3.8
tensorflow=2.8.0
torch=1.11.0
opencv-python=4.5.5
mediapipe=0.8.9.1
matplotlib=3.5.1
numpy=1.22.3
scikit-learn=1.0.2
```

## Usage

```bash
# Run the Driver Monitoring System
python dms.py --checkpoint models/model_split.h5 --video <path_to_video>

# OR use webcam
python dms.py --checkpoint models/model_split.h5 --webcam 0

# Run facial tracking only
python facial.py
```

## Features

- Driver drowsiness detection
- Yawning detection
- Eye status monitoring
- Gaze tracking
- Phone call detection
- Texting detection
- Seatbelt detection
- Real-time AI-based monitoring

## Demo

The system processes live webcam input or recorded videos to monitor driver behavior and generate real-time alerts.
