import os
import cv2
import json
import subprocess
from ultralytics import YOLO
from PIL import Image as PILImage
import numpy as np
import json

with open("config.json") as f:
    config = json.load(f)

# ---- CONFIGURATION ---- #
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CONFIG_DIR, "data")
VIDEO_PATH = config["video_path"]
TEMPLATE_PATH = os.path.join(DATA_DIR, "minimap.png")
MODEL_PATH = os.path.join(DATA_DIR, "best.pt")
FRAMES_DIR = os.path.join(DATA_DIR, "frames")
MINIMAP_POS_DIR = os.path.join(DATA_DIR, "minimap_position")
FPS = 2  # reduced frames per second to limit data
CONFIDENCE_THRESHOLD = 0.65  # minimum confidence to include a prediction
FRAME_SKIP = 2  # process every Nth frame to reduce output
MINIMAP_SCORE_THRESHOLD = 40000  # Mindestfläche als Score für gültige Minimap-Erkennung

os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(MINIMAP_POS_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

def extract_frames(video_path, output_folder, fps=FPS):
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        os.path.join(output_folder, "frame_%04d.png")
    ]
    subprocess.run(cmd)

def detect_minimap(image):
    image_height, image_width = image.shape[:2]

    roi_width = int(image_width * 0.3)
    roi_height = int(image_height * 0.3)
    roi_x = image_width - roi_width
    roi_y = image_height - roi_height

    roi = image[roi_y:image_height, roi_x:image_width]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 30, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_box = None
    best_score = 0

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        aspect_ratio = w / float(h)

        if 0.85 <= aspect_ratio <= 1.15 and area > 500:  # roughly square
            score = area
            if score > best_score:
                best_score = score
                best_box = (x + roi_x, y + roi_y, w, h)

    if best_score < MINIMAP_SCORE_THRESHOLD:
        raise ValueError(f"Minimap score too low ({best_score}), skipping frame")

    if best_box is None:
        raise ValueError("Minimap not found via contour detection.")
    return best_box  # returns (x, y, w, h)

def get_predictions_from_image(image):
    results = model.predict(image)
    result = results[0]
    output = []
    for box in result.boxes:
        confidence = box.conf[0].item()
        if confidence < CONFIDENCE_THRESHOLD:
            continue
        x1, y1, x2, y2 = [round(x) for x in box.xyxy[0].tolist()]
        class_id = box.cls[0].item()
        prob = round(confidence, 2)
        output.append([x1, y1, x2, y2, result.names[class_id], prob])
    return output

def process_frames():
    results_dict = {}
    frame_files = sorted([f for f in os.listdir(FRAMES_DIR) if f.endswith(".png")])
    if not frame_files:
        print("[ERROR] No frames found.")
        return

    minimap_found_once = False
    x = y = w = h = None
    start_frame = None
    end_frame = None
    start_frame_index = 0
    miss_counter = 0
    max_consecutive_misses = 5
    prediction_miss_counter = 0
    max_prediction_misses = 5
    empty_prediction_buffer = []

    for i, filename in enumerate(frame_files):
        if i % FRAME_SKIP != 0:
            continue

        frame_path = os.path.join(FRAMES_DIR, filename)
        frame = cv2.imread(frame_path)

        try:
            if not minimap_found_once:
                box = detect_minimap(frame)
                print(f"[MINIMAP] Detected in frame {filename} with box {box}")
                x, y, w, h = box
                minimap_crop = frame[y:y+h, x:x+w]
                cv2.imwrite(os.path.join(MINIMAP_POS_DIR, "minimap.png"), minimap_crop)
                print(f"[INFO] First minimap saved: frame {filename} at x={x}, y={y}, w={w}, h={h}")
                minimap_found_once = True
                start_frame = filename
                start_frame_index = i
            else:
                try:
                    _ = detect_minimap(frame)
                    miss_counter = 0
                except:
                    miss_counter += 1
                    print(f"[MISS] Frame {filename}: Minimap not visible ({miss_counter}/{max_consecutive_misses})")

                box = (x, y, w, h)

            minimap = frame[y:y+h, x:x+w]
            timestamp = (i - start_frame_index) / FPS
            predictions = get_predictions_from_image(PILImage.fromarray(cv2.cvtColor(minimap, cv2.COLOR_BGR2RGB)))
            
            if not predictions:
                prediction_miss_counter += 1
                empty_prediction_buffer.append(filename)
                print(f"[NO PRED] Frame {filename}: No predictions ({prediction_miss_counter}/{max_prediction_misses})")
            else:
                prediction_miss_counter = 0
                empty_prediction_buffer = []
            
            results_dict[filename] = {
                "timestamp": f"{int(timestamp // 3600):02}:{int((timestamp % 3600) // 60):02}:{int(timestamp % 60):02}",
                "predictions": predictions
            }
            
            # Matchende wenn beide Bedingungen erfüllt sind
            if miss_counter >= max_consecutive_misses and prediction_miss_counter >= max_prediction_misses:
                end_frame = empty_prediction_buffer[0] if empty_prediction_buffer else filename
                print(f"[END] Match likely ended at frame {end_frame} (via combined condition)")
                break

        except Exception as e:
            print(f"[SKIP] Frame {filename}: {e}")
            continue

    results_dict["__meta__"] = {
        "start_frame": start_frame,
        "end_frame": end_frame if end_frame else frame_files[-1]
    }

    with open(os.path.join(DATA_DIR, "results.json"), "w") as f:
        json.dump(results_dict, f, indent=2)

if __name__ == "__main__":
    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"[ERROR] Video file not found at: {VIDEO_PATH}")
    print("[INFO] Extracting frames...")
    extract_frames(VIDEO_PATH, FRAMES_DIR, FPS)
    print("[INFO] Processing frames...")
    process_frames()
    print(f"[DONE] Saved minimap to {MINIMAP_POS_DIR} and results to results.json")
