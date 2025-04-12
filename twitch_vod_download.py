import subprocess
import re

# Using TwitchDownloaderCLI: https://github.com/lay295/TwitchDownloader

def clip_twitch_vod(vod_url, start_time, end_time, output_file="H:/TwitchDownloaderCLI/Videos/video.mp4"):
    command = [
        "TwitchDownloaderCLI.exe",
        "videodownload",
        "--id", vod_url,
        "-b", start_time,
        "-e", end_time,
        "-o", output_file
    ]

    print("Running command:\n", " ".join(command))
    subprocess.run(command, check=True)
    print(f"Clip saved as: {output_file}")

if __name__ == "__main__":
    vod_url = "https://www.twitch.tv/videos/2426322362"
    start = "04:22:46"
    end = "04:52:07"

    clip_twitch_vod(vod_url, start, end)
