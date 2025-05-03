import streamlit as st
import os
import json
import pandas as pd
from PIL import Image
import os
import base64
import re

st.set_page_config(page_title="Prediction Viewer", layout="wide")
# ---- CONFIG: Match Selection ---- #
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STYLE_PATH = os.path.join(SCRIPT_DIR, "style", "style.css")
CHAMPION_DIR = os.path.join(SCRIPT_DIR, "..", "champions")
PINGS_DIR = os.path.join(SCRIPT_DIR, "..", "assets", "standard_pings")
MATCHES_DIR = os.path.join(SCRIPT_DIR, "data")
CONFIGS_PATH = os.path.join(SCRIPT_DIR, "configs")
available_matches = sorted([d for d in os.listdir(MATCHES_DIR) if d.startswith("match_")]) # Let user choose a match folder
selected_match = st.selectbox("Select a match", available_matches)
DATA_DIR = os.path.join(MATCHES_DIR, selected_match)
# ---- Paths ---- #
RESULTS_PATH = os.path.join(DATA_DIR, "results.json")
WEBDATA_DIR = os.path.join(DATA_DIR, "webdata")
ITEM_CSV = os.path.join(WEBDATA_DIR, "player_item_build.csv")
GOLD_CSV = os.path.join(WEBDATA_DIR, "gold_difference_timeline.csv")
CHAMPION_TEAMS_JSON = os.path.join(WEBDATA_DIR, "champion_teams.json")
MINIMAP_PATH = os.path.join(DATA_DIR, "..", "minimap.png")
MINIMAP_POSITION = os.path.join(DATA_DIR, "minimap_position")
CHAT_DIR = os.path.join(DATA_DIR, "chat_text")

# Load config based on selected match
match_id = selected_match.split("_")[1]
config_path = os.path.join(CONFIGS_PATH, f"config_{match_id}.json")
with open(config_path) as f:
    config = json.load(f)

# Convert vod_timestamp to twitch-url format
timestamp_ms = config['vod_timestamp']
timestamp =  timestamp_ms // 1000
h = timestamp // 3600
m = (timestamp % 3600) // 60
s = timestamp % 60

# ---- Load Data ---- #
with open(RESULTS_PATH, "r") as f:
    results = json.load(f)

gold_graph = pd.read_csv(GOLD_CSV)
frame_files = sorted(results.keys())

# ---- Team color ---- #
with open(os.path.join(WEBDATA_DIR, "champion_teams.json")) as f:
    champion_team_map = {c["champion"]: c["team"] for c in json.load(f)}

event_log = []
# ---- Clean Chat-Textfile ---- #
if os.path.exists(CHAT_DIR):
    chat_files = sorted([f for f in os.listdir(CHAT_DIR) if f.endswith(".txt")])
    if chat_files:
        first_chat_file = chat_files[0]
        chat_path = os.path.join(CHAT_DIR, first_chat_file)

        with open(chat_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            lines = lines[1:]  # Skip header
            for line in lines:
                line = line.strip()
                import re
                match = re.match(r"^(\d{2}[:.]\d{2})\s+(.*?),", line)
                if match:
                    timestamp = match.group(1).replace(".", ":")
                    text = match.group(2).strip()
                    event_log.append({"timestamp": timestamp, "text": text})
    else:
        st.error("No chat text file found in chat_text folder.")
else:
    st.error("chat_text folder does not exist!")

# ---- Filter by start/end frame from metadata ---- #
meta = results.get("__meta__", {})
start_frame = meta.get("start_frame")
end_frame = meta.get("end_frame")

if start_frame and end_frame and start_frame in frame_files and end_frame in frame_files:
    start_index = frame_files.index(start_frame)
    end_index = frame_files.index(end_frame)
    frame_files = frame_files[start_index:end_index + 1]
else:
    st.warning("Start or end frame not found in results.json — displaying full timeline.")

# Convert MM:SS timestamps to seconds
def mmss_to_seconds(ts):
    try:
        minutes, seconds = map(int, ts.split(":"))
        return minutes * 60 + seconds
    except:
        return None
    
# ---- Dataframes ---- #
item_df = pd.read_csv(ITEM_CSV)
if 'timestamp' in item_df.columns: #Transfrom item timestamps
    item_df['timestamp'] = item_df['timestamp'].apply(mmss_to_seconds)
    item_df = item_df.dropna(subset=['timestamp'])  # remove any malformed
    item_df['timestamp'] = item_df['timestamp'].astype(int)

gold_df = pd.read_csv(GOLD_CSV)
if 'timestamp' in gold_df.columns: # Convert 'timestamp' from minutes to seconds for alignment
    gold_df['timestamp'] = pd.to_numeric(gold_df['timestamp'], errors='coerce')  # handle any non-numeric gracefully
    gold_df = gold_df.dropna(subset=['timestamp'])  # remove rows with invalid timestamps
    gold_df['timestamp'] = gold_df['timestamp'].astype(int) * 60

# ---- Streamlit UI ---- #
st.markdown("---")

# ---- Load CSS ---- #
with open(STYLE_PATH, "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load the static minimap image to get its display size
image = Image.open(MINIMAP_PATH)
image_width, image_height = image.size

# Load the first annotated frame to get the original minimap size
if os.path.exists(MINIMAP_POSITION):
    first_annotated = sorted([f for f in os.listdir(MINIMAP_POSITION) if f.endswith(".png")])[0]
    annotated_path = os.path.join(MINIMAP_POSITION, first_annotated)
    annotated_img = Image.open(annotated_path)
    original_width, original_height = annotated_img.size
else:
    original_width, original_height = image_width, image_height  # fallback

#Scale to correct minimap size
scale_x = 640 / original_width
scale_y = 640 / original_height

# Set frame_index here to 0 and create the slider at the end
if "frame_index" not in st.session_state:
    st.session_state.frame_index = 0
    
frame_index = st.session_state.frame_index
selected_frame = frame_files[frame_index]

# Layout with 2 columns
left_col, spacer, right_col = st.columns([2,0.2,2])

with right_col:
    st.subheader("LegaueOfGraphs-URL and the Twitch-VOD:")
    st.link_button("🔗 LeagueOfGraphs Match", url=config["match_url"])
    st.link_button("🎥 Watch Twitch VOD", url=f"https://www.twitch.tv/videos/{config['vod_id']}?t={h}h{m}m{s}s")

    def image_to_base64(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    data = results.get(selected_frame, {})
    preds = data.get("predictions", [])
    timestamp = data.get("timestamp", "Unknown")

    base64_image = image_to_base64(MINIMAP_PATH)
    html = f"<div class='container'style=width:640px; position: relative;><img src='data:image/png;base64,{base64_image}' width='640'>"

    with st.expander("Display Filters", expanded=True):
        show_champions = st.checkbox("Show Champions", value=True)
        show_pings = st.checkbox("Show Pings", value=True)
    
    for pred in preds:
        x1, y1, x2, y2, name, conf = pred
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        scaled_x = int(cx * scale_x)
        scaled_y = int(cy * scale_y)

        icon_path = os.path.join(CHAMPION_DIR, name, "1.png")
        ping_path = os.path.join(PINGS_DIR, name, "1.png")
        
        if os.path.exists(icon_path):
            if show_champions:
                team = champion_team_map.get(name, "unknown")
                team_class = "blue-team" if team == "blue" else "red-team"
                base64_icon = image_to_base64(icon_path)
                html += f"<img class='icon icon-hover {team_class}' src='data:image/png;base64,{base64_icon}' style='left:{scaled_x}px;top:{scaled_y}px;' data-label='{name} ({conf:.2f})'>"
            else:
                continue
        elif os.path.exists(ping_path):
            if show_pings:
                base64_icon = image_to_base64(ping_path)
                html += f"<img class='icon icon-hover' src='data:image/png;base64,{base64_icon}' style='left:{scaled_x}px;top:{scaled_y}px;' data-label='{name} ({conf:.2f})'>"
            else:
                continue

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    
with left_col:
    timestamp = data.get("timestamp", "Unknown")
    event_seconds = 0
    
    if timestamp != "Unknown":
        time_parts = list(map(int, timestamp.split(":")))
        event_seconds = time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]

    # Get the gold difference row
    gold_value = gold_df[gold_df['timestamp'] <= event_seconds].tail(1)

    # Prepare data
    if not gold_value.empty:
        diff = gold_value.iloc[0]['gold_diff']
        table_data = {
            "Timestamp": [timestamp],
            "Gold Difference (Blue - Red)": [f"{diff:+}"]
        }

    # Display as table
    st.dataframe(pd.DataFrame(table_data), hide_index=True)
    
    # Gold Graph
    st.line_chart(gold_graph, x="timestamp", y="gold_diff",x_label="Minutes", y_label="")
    
    st.markdown("### Event Log")
    # ---- Prepare unified event log ---- #
    full_event_log = []

    # Add item purchases
    if not item_df.empty:
        for _, row in item_df.iterrows():
            if pd.notnull(row['timestamp']):
                full_event_log.append({
                    "time_seconds": int(row['timestamp']),
                    "text": f"Player bought {row['item_name']}"
                })

    # Add chat events
    for event in event_log:
        if "timestamp" in event and "text" in event:
            minutes, seconds = map(int, event["timestamp"].split(":"))
            total_seconds = minutes * 60 + seconds
            full_event_log.append({
                "time_seconds": total_seconds,
                "text": event["text"]
            })

    # Sort all events by time
    full_event_log = sorted(full_event_log, key=lambda x: x["time_seconds"])

     # --- Find closest event to the current frame time ---
    current_event = None
    for event in full_event_log:
        if event["time_seconds"] <= event_seconds:
            current_event = event

    # Display event log
    with st.container(height=450):
        if full_event_log:
            for id, event in enumerate(full_event_log):
                mm = event["time_seconds"] // 60
                ss = event["time_seconds"] % 60
                time_label = f"{mm:02}:{ss:02}"

                element_id = f"event-{id}"

                if event == current_event:
                    st.markdown(f"<div class='event_log_highlight'>[{time_label}] {event['text']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"[{time_label}] {event['text']}", unsafe_allow_html=True)
        else:
            st.write("No events at this time.")

# --- Slider am unteren Rand ---
st.slider("Select Frame", 0, len(frame_files) - 1, key="frame_index")
