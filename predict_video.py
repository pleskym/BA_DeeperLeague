import os
import cv2
import json
import subprocess
from ultralytics import YOLO
from PIL import Image as PILImage
import numpy as np

# ---- CONFIGURATION ---- #
CONFIG_DIR = "run_video_data"
VIDEO_PATH = os.path.join(CONFIG_DIR, "video.mp4")
TEMPLATE_PATH = os.path.join(CONFIG_DIR, "minimap.png")
MODEL_PATH = os.path.join(CONFIG_DIR, "best_1530_10032025.pt")

FRAMES_DIR = os.path.join(CONFIG_DIR, "frames")
ANNOTATED_DIR = os.path.join(CONFIG_DIR, "annotated")
FPS = 2  # reduced frames per second to limit data
CONFIDENCE_THRESHOLD = 0.65  # minimum confidence to include a prediction
FRAME_SKIP = 2  # process every Nth frame to reduce output

# ---- SETUP ---- #
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(ANNOTATED_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

def extract_frames(video_path, output_folder, fps=FPS):
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={fps}",
        os.path.join(output_folder, "frame_%04d.png")
    ]
    subprocess.run(cmd)

def detect_minimap(image):
    template = cv2.imread(TEMPLATE_PATH)
    if template is None:
        raise FileNotFoundError(f"Template not found at {TEMPLATE_PATH}")

    image_height, image_width = image.shape[:2]
    template_height, template_width = template.shape[:2]

    roi_width = int(image_width * 0.27)
    roi_height = int(image_height * 0.27)
    roi_x = image_width - roi_width
    roi_y = image_height - roi_height

    roi = image[roi_y:image_height, roi_x:image_width]

    if template_height > roi.shape[0] or template_width > roi.shape[1]:
        scaling_factor = min(roi.shape[0] / template_height, roi.shape[1] / template_width)
        template = cv2.resize(template, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
        template_height, template_width = template.shape[:2]

    result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    top_left = max_loc
    bottom_right = (top_left[0] + template_width, top_left[1] + template_height)

    top_left_original = (int(top_left[0] + roi_x), int(top_left[1] + roi_y))
    bottom_right_original = (int(bottom_right[0] + roi_x), int(bottom_right[1] + roi_y))

    x, y = top_left_original
    w = bottom_right_original[0] - x
    h = bottom_right_original[1] - y

    return int(x), int(y), int(w), int(h)

def draw_predictions(image, predictions):
    for x1, y1, x2, y2, name, prob in predictions:
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        text = f'{name}: {prob:.2f}'
        cv2.putText(image, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return image

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
    results_dict = {}
    frame_files = sorted([f for f in os.listdir(FRAMES_DIR) if f.endswith(".png")])
    if not frame_files:
        print("[ERROR] No frames found.")
        return

    first_frame_path = os.path.join(FRAMES_DIR, frame_files[0])
    first_frame = cv2.imread(first_frame_path)

    try:
        x, y, w, h = detect_minimap(first_frame)
        print(f"[INFO] Minimap detected at: x={x}, y={y}, w={w}, h={h}")
    except Exception as e:
        print(f"[ERROR] Minimap detection failed on first frame: {e}")
        return

    for i, filename in enumerate(frame_files):
        if i % FRAME_SKIP != 0:
            continue
        if i % FRAME_SKIP != 0:
            continue

        frame_path = os.path.join(FRAMES_DIR, filename)
        frame = cv2.imread(frame_path)

        try:
            x, y, w, h = int(x), int(y), int(w), int(h)
            minimap = frame[y:y+h, x:x+w]
            predictions = get_predictions_from_image(PILImage.fromarray(cv2.cvtColor(minimap, cv2.COLOR_BGR2RGB)))
            annotated_minimap = draw_predictions(minimap.copy(), predictions)
            annotated_path = os.path.join(ANNOTATED_DIR, filename)
            cv2.imwrite(annotated_path, annotated_minimap)

            timestamp = i / FPS  # seconds
            results_dict[filename] = {
                "timestamp": f"{int(timestamp // 3600):02}:{int((timestamp % 3600) // 60):02}:{int(timestamp % 60):02}",
                "predictions": predictions
            }

        except Exception as e:
            print(f"[WARN] Failed to process {filename}: {e}")

    with open(os.path.join(CONFIG_DIR, "results.json"), "w") as f:
        json.dump(results_dict, f, indent=2)

if __name__ == "__main__":
    print("[INFO] Extracting frames...")
    extract_frames(VIDEO_PATH, FRAMES_DIR, FPS)
    print("[INFO] Processing frames...")
    process_frames()
    print(f"[DONE] Annotated frames saved to {ANNOTATED_DIR}")
