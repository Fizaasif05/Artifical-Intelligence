import os
import sys
import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance as dist
import time
import simpleaudio as sa
import threading

# Print the current working directory
print("Current working directory:", os.getcwd())

# List the files in the current working directory
print("Files in the current working directory:", os.listdir(os.getcwd()))

# Check if alarm.wav exists in the current directory
if not os.path.isfile("alarm.wav"):
    print("Error: alarm.wav file not found in the current directory.")
    sys.exit(1)

# Alarm function
def sound_alarm():
    wave_obj = sa.WaveObject.from_wave_file("alarm.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

def eye_aspect_ratio(eye):
    # Vertical distances
    A = dist.euclidean(eye[1], eye[3])
    B = dist.euclidean(eye[2], eye[3])
    C = dist.euclidean(eye[3], eye[5])
    D = dist.euclidean(eye[0], eye[4])
    
    # Horizontal distance
    E = dist.euclidean(eye[0], eye[2])
    F = dist.euclidean(eye[6], eye[8])

    # EAR calculation using additional points
    ear = (A + B + C + D) / (4.0 * (E + F))
    
    return ear

# Mouth aspect ratio
def mouth_aspect_ratio(mouth):
    A = dist.euclidean(mouth[13], mouth[19])
    B = dist.euclidean(mouth[14], mouth[18])
    C = dist.euclidean(mouth[12], mouth[16])
    mar = (A + B) / (2.45 * C)
    return mar

# Constants
EYE_AR_THRESH = 0.658  # Adjusted threshold for better sensitivity
EYE_AR_CONSEC_FRAMES = 15  # Adjusted for more frames
MAR_THRESH = 0.74  # Adjusted to detect yawning more accurately
YAWN_CONSEC_FRAMES = 15  # Adjusted for quicker detection
EYE_CLOSED_THRESH = 3.0  # Duration threshold for closed eyes to trigger alarm

# Initialize the frame counters and the total number of blinks
COUNTER = 0
YAWN_COUNTER = 0
EYE_CLOSED_TIMER = 0
ALARM_ON = False

# Mediapipe face mesh detector
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Function to handle alarm in a separate thread
def alarm_handler():
    global ALARM_ON
    while True:
        if ALARM_ON:
            sound_alarm()
            ALARM_ON = False
        time.sleep(1)  # Adjust delay as needed

# Start the alarm handler thread
alarm_thread = threading.Thread(target=alarm_handler, daemon=True)
alarm_thread.start()

# Start the video stream
print("[INFO] starting video stream...")
vs = cv2.VideoCapture(0)
time.sleep(1.0)

# Loop over frames from the video stream
while True:
    ret, frame = vs.read()
    if not ret:
        break

    frame = cv2.resize(frame, (450, 450))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect face landmarks
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            landmarks = face_landmarks.landmark

            # Extract the coordinates for the eyes
            left_eye = [
    (landmarks[i].x, landmarks[i].y) for i in [33, 246, 161, 160, 159, 158, 157, 173, 133, 155]
]
            right_eye = [
    (landmarks[i].x, landmarks[i].y) for i in [362, 385, 386, 387, 388, 466, 263, 249, 255, 256]
]

            # Extract the coordinates for the mouth
            mouth = [(landmarks[i].x, landmarks[i].y) for i in [61, 81, 78, 191, 80, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 88, 178, 87]]

            # Convert normalized coordinates to pixel values
            h, w, _ = frame.shape
            left_eye = np.array(left_eye) * np.array([w, h])
            right_eye = np.array(right_eye) * np.array([w, h])
            mouth = np.array(mouth) * np.array([w, h])

            # Calculate EAR and MAR
            leftEAR = eye_aspect_ratio(left_eye)
            rightEAR = eye_aspect_ratio(right_eye)
            ear = (leftEAR + rightEAR) / 2.0
            mar = mouth_aspect_ratio(mouth)

            # Draw contours
            cv2.polylines(frame, [np.int32(left_eye)], True, (0, 255, 0), 1)
            cv2.polylines(frame, [np.int32(right_eye)], True, (0, 255, 0), 1)
            cv2.polylines(frame, [np.int32(mouth)], True, (0, 255, 0), 1)

            # Check if the eye aspect ratio is below the blink threshold
            if ear < EYE_AR_THRESH:
                COUNTER += 1
                EYE_CLOSED_TIMER += 1

                # If the eyes were closed for a sufficient number of frames, sound the alarm
                if EYE_CLOSED_TIMER >= EYE_AR_CONSEC_FRAMES or (EYE_CLOSED_TIMER / 30) > EYE_CLOSED_THRESH:
                    if not ALARM_ON:
                        ALARM_ON = True
                    cv2.putText(frame, "DROWSINESS ALERT!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                COUNTER = 0
                EYE_CLOSED_TIMER = 0

            # Check if the mouth aspect ratio is above the yawn threshold
            if mar > MAR_THRESH:
                YAWN_COUNTER += 1

                # If the mouth was open for a sufficient number of frames, sound the alarm
                if YAWN_COUNTER >= YAWN_CONSEC_FRAMES:
                    if not ALARM_ON:
                        ALARM_ON = True
                    cv2.putText(frame, "YAWNING ALERT!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                YAWN_COUNTER = 0

            # Display the EAR and MAR
            cv2.putText(frame, f"EAR: {ear:.2f}", (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"MAR: {mar:.2f}", (300, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Show the frame
    cv2.imshow("Frame", frame)

    # Process events and wait for a key press
    key = cv2.waitKey(1) & 0xFF

    # If the q key was pressed, break from the loop
    if key == ord("q"):
        break

# Cleanup
cv2.destroyAllWindows()
vs.release()