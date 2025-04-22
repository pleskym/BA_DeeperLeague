import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import subprocess
import json
import sys

config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
with open(config_path) as f:
    config = json.load(f)

def extract_item_build_timeline(soup, participant_id):
    participant_items = []
    participant_section = soup.find("div", {"data-tab-id": participant_id})
    if participant_section:
        item_purchase_table = participant_section.find("table", class_="data_table match_items_table")
        if item_purchase_table:
            for row in item_purchase_table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    timestamp = cols[0].text.strip()
                    item_imgs = cols[1].find_all("img")
                    items = [img["alt"] for img in item_imgs if "alt" in img.attrs]
                    if items:
                        participant_items.append({
                            "timestamp": timestamp,
                            "item_name": ", ".join(items)
                        })
    return pd.DataFrame(participant_items)

def extract_gold_difference_timeline(soup):
    gold_data = []
    script_tag = soup.find("script", string=lambda text: text and "data: [[" in text)
    if script_tag:
        script_text = script_tag.text
        data_start = script_text.find("data: [[") + len("data: [[")
        data_end = script_text.find("]]", data_start)
        gold_data_raw = script_text[data_start:data_end]
        for entry in gold_data_raw.split("],["):
            time_gold = entry.split(",")
            if len(time_gold) == 2:
                try:
                    gold_data.append({
                        "timestamp": int(time_gold[0]),
                        "gold_diff": int(time_gold[1])
                    })
                except ValueError:
                    pass
    return pd.DataFrame(gold_data)

def extract_runes_from_table(soup, participant_id):
    runes = []
    participant_section = soup.find("div", {"data-tab-id": participant_id})
    if participant_section:
        runes_header = participant_section.find("h3", string="Runes")
        if runes_header:
            runes_table = runes_header.find_next("table", class_="data_table")
            if runes_table:
                rune_imgs = runes_table.find_all("img")
                runes = [img["alt"].strip() for img in rune_imgs if img.has_attr("alt")]
    return pd.DataFrame(runes, columns=["Runes"])

def extract_twitch_vod_info(soup):
    link = soup.find("a", class_="twitchSpectatePopupLink", attrs={"data-rel": "twitchSpectatePopup"})
    if link:
        timestamp = int(link.get("data-video-timestamp"))
        return {
            "vod_id": link.get("data-video-id"),
            "timestamp": timestamp + 30000
        }
    return None

def convert_milliseconds_to_hms(ms):
    total_seconds = ms // 1000
    h, remainder = divmod(total_seconds, 3600)
    m, s = divmod(remainder, 60)

    return f"{h:02}:{m:02}:{s:02}"

def extract_game_duration_ms(soup):
    duration_tag = soup.find("span", class_="gameDuration")
    if duration_tag:
        time_str = duration_tag.text.strip().strip("()")  # remove parentheses
        if ":" in time_str:
            mins, secs = map(int, time_str.split(":"))
            print("Minutes: ", mins, "Seconds: ", secs) 
            return (mins * 60 + secs) * 1000
    return 1800  # fallback if not found

def download_vod_clip(vod_id, start_ms, duration, output_path="video_clip.mp4", buffer_ms=60000):
    end_ms = start_ms + duration + buffer_ms
    print("START SECONDS: ", start_ms)
    command = [
        "TwitchDownloaderCLI.exe",
        "videodownload",
        "--id", vod_id,
        "-b", convert_milliseconds_to_hms(start_ms),
        "-e", convert_milliseconds_to_hms(end_ms),
        "-o", output_path
    ]
    print("Running TwitchDownloaderCLI command:", " ".join(command))
    subprocess.run(command, check=True)
    print(f"VOD clip saved as: {output_path}")

def extract_champion_teams(soup):
    champions = []
    tab_imgs = soup.select(".matchPlayersTabs .tab img")
    
    for img in tab_imgs:
        champ = img.get("alt")
        classes = img.get("class", [])
        team = "blue" if "blueShadow" in classes else "red"
        champions.append({"champion": champ, "team": team})
    
    return champions

def main():
    url = config["match_url"]
    participant_id = url.split("#")[-1]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        # Make match specific folder
        match_id = url.split("/")[-1].split("#")[0]
        match_dir = os.path.join("data", f"match_{match_id}")
        webdata_dir = os.path.join(match_dir, "webdata")
        os.makedirs(webdata_dir, exist_ok=True)

        # Video path
        video_path = os.path.join(match_dir, "video.mp4")

        item_df = extract_item_build_timeline(soup, participant_id)
        gold_df = extract_gold_difference_timeline(soup)
        runes_df = extract_runes_from_table(soup, participant_id)

        item_df.to_csv(os.path.join(webdata_dir, "player_item_build.csv"), index=False)
        gold_df.to_csv(os.path.join(webdata_dir, "gold_difference_timeline.csv"), index=False)
        runes_df.to_csv(os.path.join(webdata_dir, "runes.csv"), index=False)

        #Save champions per team
        champion_team_data = extract_champion_teams(soup)
        with open(os.path.join(webdata_dir, "champion_teams.json"), "w") as f:
            json.dump(champion_team_data, f, indent=2)
        
        print("Data extracted and saved to the specific match 'webdata/'!")

        # Extract VOD info and download
        vod_info = extract_twitch_vod_info(soup)
        game_duration = extract_game_duration_ms(soup)
        print("Game Duration: ", game_duration)
        if vod_info:
            # Save VOD ID to config.json
            config["vod_id"] = vod_info["vod_id"]
            config["vod_timestamp"] = vod_info["timestamp"]
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)

            #Download VOD
            download_vod_clip(
                vod_id = vod_info["vod_id"],
                start_ms = (vod_info["timestamp"]),
                duration = game_duration,
                output_path = video_path
            )
        else:
            print("No Twitch VOD info found in page.")
    else:
        print(f"Failed to load page: {response.status_code}")

if __name__ == "__main__":
    main()
