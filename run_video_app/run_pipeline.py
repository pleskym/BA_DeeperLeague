import os
import subprocess
import json
import time
import sys

def load_config(config_path):
    with open(config_path, "r") as f:
        return json.load(f), config_path

def run_script(script_name, config_path):
    print(f"[INFO] Running {script_name} with {config_path}")
    result = subprocess.run(["python", script_name, config_path])
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
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <path_to_config>")
        return
    
    config_path = sys.argv[1]
    config, _ = load_config(config_path)
    match_id = config["match_url"].split("/")[-1].split("#")[0]
    video_path = os.path.join("data", f"match_{match_id}", "video.mp4")

    # Schritt 1: scrapeWebData
    run_script("scrapeWebData.py", config_path)

    # Schritt 2: Warte bis das Video da ist
    wait_for_file(video_path)

    # Schritt 3: predict_video
    run_script("predict_video.py", config_path)

    print("[PIPELINE DONE] Alles erfolgreich durchgelaufen.")

if __name__ == "__main__":
    main()
