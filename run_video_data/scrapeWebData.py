import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import subprocess

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
        raw_timestamp = int(link.get("data-video-timestamp"))
        # Convert from milliseconds to seconds
        timestamp = raw_timestamp // 1000
        return {
            "vod_id": link.get("data-video-id"),
            "timestamp": timestamp
        }
    return None

def convert_seconds_to_hms(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def extract_game_duration_seconds(soup):
    duration_tag = soup.find("span", class_="gameDuration")
    if duration_tag:
        time_str = duration_tag.text.strip().strip("()")  # remove parentheses
        if ":" in time_str:
            mins, secs = map(int, time_str.split(":"))
            return mins * 60 + secs
    return 1800  # fallback if not found

def download_vod_clip(vod_id, start_seconds, duration, output_path="video_clip.mp4", buffer_seconds=30):
    start_seconds = start_seconds + 30 # Matches start 30 seconds later from timestamp in LeageuOfGraphs
    end_seconds = start_seconds + duration + buffer_seconds
    command = [
        "TwitchDownloaderCLI.exe",
        "videodownload",
        "--id", vod_id,
        "-b", convert_seconds_to_hms(start_seconds),
        "-e", convert_seconds_to_hms(end_seconds),
        "-o", output_path
    ]
    print("Running TwitchDownloaderCLI command:", " ".join(command))
    subprocess.run(command, check=True)
    print(f"VOD clip saved as: {output_path}")

def main():
    url = "https://www.leagueofgraphs.com/match/euw/7360565181#participant8"
    participant_id = url.split("#")[-1]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        item_df = extract_item_build_timeline(soup, participant_id)
        gold_df = extract_gold_difference_timeline(soup)
        runes_df = extract_runes_from_table(soup, participant_id)

        os.makedirs('webdata', exist_ok=True)

        item_df.to_csv("webdata/player_item_build.csv", index=False)
        gold_df.to_csv("webdata/gold_difference_timeline.csv", index=False)
        runes_df.to_csv("webdata/runes.csv", index=False)

        print("Data extracted and saved to 'webdata/'!")

        # Extract VOD info and download
        vod_info = extract_twitch_vod_info(soup)
        game_duration = extract_game_duration_seconds(soup)
        if vod_info:
            download_vod_clip(
                vod_id = vod_info["vod_id"],
                start_seconds = (vod_info["timestamp"]),
                duration = (game_duration),
                output_path = "H:/TwitchDownloaderCLI/Videos/video.mp4"
            )
        else:
            print("No Twitch VOD info found in page.")
    else:
        print(f"Failed to load page: {response.status_code}")

if __name__ == "__main__":
    main()
