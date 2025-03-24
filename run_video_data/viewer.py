import streamlit as st
import os
import json
import pandas as pd
from PIL import Image
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- CONFIG ---- #
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ANNOTATED_DIR = os.path.join(SCRIPT_DIR, "annotated")
RESULTS_PATH = os.path.join(SCRIPT_DIR, "results.json")
ITEM_CSV = os.path.join(SCRIPT_DIR, "player_item_build.csv")
GOLD_CSV = os.path.join(SCRIPT_DIR, "gold_difference_timeline.csv")

# ---- Load Data ---- #
frame_files = sorted([f for f in os.listdir(ANNOTATED_DIR) if f.endswith(".png")])

with open(RESULTS_PATH, "r") as f:
    results = json.load(f)

item_df = pd.read_csv(ITEM_CSV)
gold_df = pd.read_csv(GOLD_CSV)

# ---- Streamlit UI ---- #
st.set_page_config(page_title="Prediction Viewer", layout="wide")
st.title("Minimap Prediction Viewer")

frame_index = st.slider("Select Frame", 0, len(frame_files) - 1, 0)
selected_frame = frame_files[frame_index]

# Layout with 2 columns
left_col, right_col = st.columns([1, 2])

with right_col:
    image_path = os.path.join(ANNOTATED_DIR, selected_frame)
    image = Image.open(image_path)
    st.image(image, caption=f"Frame: {selected_frame}", width=500)

    data = results.get(selected_frame, {})
    preds = data.get("predictions", [])
    timestamp = data.get("timestamp", "Unknown")

    st.markdown(f"**Timestamp:** {timestamp}")

    if preds:
        st.markdown("### Predictions")
        for pred in preds:
            x1, y1, x2, y2, name, conf = pred
            st.write(f"- {name} ({conf:.2f}) at [{x1}, {y1}, {x2}, {y2}]")
    else:
        st.info("No predictions for this frame.")

with left_col:
    timestamp = data.get("timestamp", "Unknown")
    seconds = 0
    if timestamp != "Unknown":
        time_parts = list(map(int, timestamp.split(":")))
        seconds = time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]

    st.markdown("### Gold Difference")
    gold_value = gold_df[gold_df['timestamp'] <= seconds].tail(1)
    if not gold_value.empty:
        diff = gold_value.iloc[0]['gold_diff']
        st.metric(label="Gold Diff (Blue - Red)", value=f"{diff:+}")
    else:
        st.write("No gold data available.")

    st.markdown("### Event Log")
    event_log = []

    if timestamp != "Unknown":
        time_parts = list(map(int, timestamp.split(":")))
        seconds = time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]

        item_events = item_df[item_df['timestamp'] <= seconds]
        # gold_events = gold_df[gold_df['timestamp'] == seconds]  # temporarily disabled

        if not item_events.empty:
            for _, row in item_events.iterrows():
                event_log.append(f"[Minute {row['timestamp']}]: Player bought {row['item_name']}")

    if event_log:
        for event in event_log:
            st.markdown(f"- {event}")
    else:
        st.write("No events at this time.")
