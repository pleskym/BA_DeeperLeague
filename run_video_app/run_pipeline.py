import os
import subprocess
import json
import time

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def run_script(script_name):
    print(f"[INFO] Running {script_name} ...")
    result = subprocess.run(["python", script_name])
    if result.returncode != 0:
        raise RuntimeError(f"[ERROR] {script_name} failed with code {result.returncode}")
    print(f"[DONE] {script_name} completed.\n")

def wait_for_file(path, timeout=120):
    print(f"[INFO] Waiting for file: {path}")
    waited = 0
    while not os.path.exists(path):
        time.sleep(1)
        waited += 1
        if waited > timeout:
            raise TimeoutError(f"[ERROR] Timeout: {path} not found after {timeout} seconds.")
    print(f"[INFO] Found file: {path}")

def main():
    config = load_config()
    video_path = config["video_path"]

    # Schritt 1: scrapeWebData
    run_script("scrapeWebData.py")

    # Schritt 2: Warte bis das Video da ist
    wait_for_file(video_path)

    # Schritt 3: predict_video
    run_script("predict_video.py")

    print("[✅ PIPELINE DONE] Alles erfolgreich durchgelaufen.")

if __name__ == "__main__":
    main()
