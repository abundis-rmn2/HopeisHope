# Step 1: Install Required Libraries
# Ensure you have the necessary libraries installed:
# pip install opencv-python opencv-python-headless numpy ultralytics

# Step 2: Import Libraries
import cv2
import numpy as np
import os
from ultralytics import YOLO

# Step 3: Load the Video
video_path = './mp4/prueba.mp4'
cap = cv2.VideoCapture(video_path)

# Step 4: Initialize Object Detection Model
# Load YOLOv8
#model = YOLO('yolov8n.pt')  # Use the appropriate YOLOv8 model file
model = YOLO("yolo11n-seg.pt")  # load an official model

# Ensure the /img/ directory exists
os.makedirs('./img', exist_ok=True)

# Step 5: Process Each Frame
catalog = {}
frame_skip = 25  # Number of frames to skip
frame_count = 0
percentage = 0.333  # Percentage of the video to process (0.5 means 50%)
screenshot_count = 0

# Get the total number of frames in the video
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frames_to_process = int(total_frames * percentage)

while cap.isOpened() and frame_count < frames_to_process:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue

    height, width, _ = frame.shape

    # Prepare the frame for object detection
    results = model(frame)

    # Process detections
    for result in results:
        for detection in result.boxes:
            class_id = int(detection.cls)
            confidence = detection.conf

            if confidence > 0.7:  # Confidence threshold
                label = model.names[class_id]
                if label not in catalog:
                    catalog[label] = 0
                catalog[label] += 1

                # Optionally, draw bounding boxes and labels
                x1, y1, x2, y2 = map(int, detection.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Save screenshot
                screenshot_path = f'./img/screenshot_{screenshot_count}_yolo11.jpg'
                cv2.imwrite(screenshot_path, frame)
                screenshot_count += 1

    # Display the frame (optional)
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Step 6: Display the Catalog
for item, count in catalog.items():
    print(f"{item}: {count}")

# Step 7: Save the Catalog (Optional)
with open("catalog.txt", "w") as f:
    for item, count in catalog.items():
        f.write(f"{item}: {count}\n")
