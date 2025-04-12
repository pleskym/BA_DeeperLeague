import streamlit as st
import os
import json
import pandas as pd
from PIL import Image
import os
import base64

# ---- CONFIG ---- #
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(SCRIPT_DIR, "results.json")
WEBDATA_DIR = os.path.join(SCRIPT_DIR, "webdata")
ITEM_CSV = os.path.join(WEBDATA_DIR, "player_item_build.csv")
GOLD_CSV = os.path.join(WEBDATA_DIR, "gold_difference_timeline.csv")
MINIMAP_PATH = os.path.join(SCRIPT_DIR, "minimap.png")
CHAMPION_DIR = os.path.join(SCRIPT_DIR, "..", "champions")
MINIMAP_POSITION = os.path.join(SCRIPT_DIR, "minimap_position")
PINGS_DIR = os.path.join(SCRIPT_DIR, "..", "assets", "standard_pings")
STYLE_PATH = os.path.join(SCRIPT_DIR, "style.css")

# ---- Load Data ---- #
with open(RESULTS_PATH, "r") as f:
    results = json.load(f)
frame_files = sorted(results.keys())

# Convert MM:SS timestamps to seconds
def mmss_to_seconds(ts):
    try:
        minutes, seconds = map(int, ts.split(":"))
        return minutes * 60 + seconds
    except:
        return None

item_df = pd.read_csv(ITEM_CSV)
#Transfrom item timestamps
if 'timestamp' in item_df.columns:
    item_df['timestamp'] = item_df['timestamp'].apply(mmss_to_seconds)
    item_df = item_df.dropna(subset=['timestamp'])  # remove any malformed
    item_df['timestamp'] = item_df['timestamp'].astype(int)

gold_df = pd.read_csv(GOLD_CSV)
# Convert 'timestamp' from minutes to seconds for alignment
if 'timestamp' in gold_df.columns:
    gold_df['timestamp'] = pd.to_numeric(gold_df['timestamp'], errors='coerce')  # handle any non-numeric gracefully
    gold_df = gold_df.dropna(subset=['timestamp'])  # remove rows with invalid timestamps
    gold_df['timestamp'] = gold_df['timestamp'].astype(int) * 60

# ---- Streamlit UI ---- #
st.set_page_config(page_title="Prediction Viewer", layout="wide")
st.title("Minimap Prediction Viewer")

#Load CSS
with open(STYLE_PATH, "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load the static minimap image to get its display size
image = Image.open(MINIMAP_PATH)
image_width, image_height = image.size  # displayed size

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
left_col, right_col = st.columns([1, 2])

with right_col:
    def image_to_base64(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    data = results.get(selected_frame, {})
    preds = data.get("predictions", [])
    timestamp = data.get("timestamp", "Unknown")

    base64_image = image_to_base64(MINIMAP_PATH)
    html = f"<div class='container'><img src='data:image/png;base64,{base64_image}' width='640'>"

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
                base64_icon = image_to_base64(icon_path)
                html += f"<img class='icon icon-hover' src='data:image/png;base64,{base64_icon}' style='left:{scaled_x}px;top:{scaled_y}px;' data-label='{name} ({conf:.2f})'>"
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
    seconds = 0
    
    if timestamp != "Unknown":
        time_parts = list(map(int, timestamp.split(":")))
        seconds = time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]

    # Get the gold difference row
    gold_value = gold_df[gold_df['timestamp'] <= seconds].tail(1)

    # Prepare data
    if not gold_value.empty:
        diff = gold_value.iloc[0]['gold_diff']
        table_data = {
            "Timestamp": [timestamp],
            "Gold Difference (Blue - Red)": [f"{diff:+}"]
        }

    # Display as table
    st.dataframe(pd.DataFrame(table_data), hide_index=True)

    st.markdown("### Event Log")
    with st.container(height=640):
        event_log = []

        item_events = item_df[item_df['timestamp'] <= seconds]  # or any condition

        if not item_events.empty:
            for _, row in item_events.iterrows():
                mm = row['timestamp'] // 60
                ss = row['timestamp'] % 60
                event_log.append(f"[{mm:02}:{ss:02}]: Player bought {row['item_name']}")

        if event_log:
            for event in event_log:
                st.markdown(event)
        else:
            st.write("No events at this time.")

# --- Slider am unteren Rand ---
st.slider("Select Frame", 0, len(frame_files) - 1, key="frame_index")
