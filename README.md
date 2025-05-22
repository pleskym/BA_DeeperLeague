# Automatisierte Ping- und Champion-Erkennung in League of Legends

## Projektübersicht

Dieses Projekt erweitert das ursprüngliche [DeeperLeague](https://github.com/davidweatherall/DeeperLeague)-System um die automatische Erkennung von Smart-Pings in *League of Legends*-Gameplay-Videos. Ziel ist es, ein vollautomatisiertes System zur Visualisierung von Spielereignissen zu schaffen.

Die entwickelte Pipeline kombiniert Videoanalyse, Webdatenextraktion und Texterkennung zu einem einheitlichen Ablauf, gesteuert durch eine zentrale Konfigurationsdatei. Als Ergebnis entsteht eine interaktive Visualisierung, die alle Spielereignisse zeitsynchron darstellt.

## Hauptfunktionen

- Automatische Erkennung von Smart-Pings und Champion-Positionen mittels YOLOv8
- Minimap-Erkennung und -Zuschnitt aus Videoframes
- Texterkennung (OCR) mithilfe des *GameAnonymization*-Tools von Benjamin Kühnis
- Extraktion von Goldverläufen, Item-Käufen und Runen über LeagueOfGraphs
- Interaktive Visualisierung mit Streamlit (Minimap, Zeitstrahl, Eventlog)

## Setup

### Voraussetzungen

- Python ≥ 3.9
- ffmpeg (für Videoverarbeitung)
- YOLOv8 (Ultralytics)
- TwitchDownloaderCLI
- GameAnonymization-Projekt (im Projektverzeichnis erwartet)

## Nutzung

### 1. Konfiguration (`config.json`)

Einzige Eingabe: vollständige Match-URL von **[leagueofgraphs.com](https://www.leagueofgraphs.com/)** (inkl. Teilnehmer, z. B. `#participant5`).

**Beispiel:**
```json
{
  "match_url": "https://www.leagueofgraphs.com/match/euw/7386596918#participant5"
}
```
Die Datei wird im Verzeichnis `configs/` abgelegt.

### 2. Pipeline starten

Die gesamte Pipeline wird mit folgendem Befehl ausgeführt:

```bash
python run_pipeline.py configs/config_123.json
```

Ablauf:

- Download des Twitch-Videos via TwitchDownloaderCLI
- Extraktion der Matchdaten (Gold, Items, Runen)
- Lokalisierung der Minimap im Video
- Objekterkennung von Smart-Pings und Champions mit YOLOv8
- Texterkennung aus dem Ingame-Chat via EasyOCR
- Speicherung der Ergebnisse als JSON/CSV im Match-Ordner

### 4. Visualisierung

Die Ergebnisse können interaktiv mit Streamlit dargestellt werden:

```bash
streamlit run viewer.py
```

Die Oberfläche zeigt:

- Zeitsynchrone Minimap mit Champion- und Ping-Positionen
- Zeitstrahl zur Navigation
- Eventlog mit Item-Käufen, Goldverlauf und Chatnachrichten

### Modell trainieren und testen

- Um ein neues YOLOv8-Modell zu trainieren, kann mit `generateTestingData.py` ein Datensatz erzeugt werden. Abhängig von den gewählten Parametern werden verschiedene Minimap-Bilder mit Champion- und Ping-Icons generiert.
- `prepTraining.py` bereitet die Daten auf, indem sie in Trainings- und Validierungsdatensätze aufgeteilt werden.
- Das Training wird mit `train_with_pings.py` gestartet. Standardmässig sind 64 Epochen mit einer Patience von 10 definiert. Das Ergebnis ist das trainierte Modell `best.pt` sowie diverse Leistungsmetriken.
- Um das Modell nach dem Training zu testen, kann mit `generateTestingImages.py` ein Testdatensatz erzeugt (`generateTestingData.py`) und evaluiert werden. Beispiel:
  ```bash
  yolo val model=runs/detect/train12/weights/best.pt data=minimap.yaml split=test save_json=True
  ```
- Trainingsdaten vorbereiten:
  ```bash
  python prepTraining.py
  ```
- Training starten:
  ```bash
  python train_with_pings.py
  ```
- Modell evaluieren:
  ```bash
  yolo val model=runs/detect/train12/weights/best.pt data=minimap.yaml split=test save_json=True
  ```

## Verwendete Skripte und ihre Funktionen

### Automatisierte Pipeline

- `run_pipeline.py`: Führt alle Schritte der Extraktion automatisch aus, vom Video-Download über die Webdatenextraktion bis hin zur Prediction und Ergebnisaufbereitung. Verwendet eine Konfigurationsdatei (`config.json`) als Eingabe, die die LeagueOfGraphs-Match-URL enthält.

### Video Prediction

- `predict_video.py`: Analysiert das heruntergeladene Video, extrahiert die Minimap aus jedem Frame, wendet das YOLOv8-Modell an und speichert die Vorhersagen mit Zeitstempeln als JSON.
  - Voraussetzungen:
    - trainiertes Modell `best.pt`
    - Videoausschnitt
    - `ffmpeg` installiert

### Datenextraktion aus dem Web

- `scrapeWebData.py`: Extrahiert Match-Daten für einen bestimmten Spieler von [leagueofgraphs.com](https://www.leagueofgraphs.com/), einschliesslich:
  - Item-Build-Timeline
  - Gold-Differenz-Verlauf
  - Verwendete Runen

### Visualisierung

- `viewer.py`: Streamlit-App zur interaktiven Visualisierung der Ergebnisse auf einer Minimap inklusive Zeitstrahl und Eventlog. Kombiniert:
  - Vorhersagedaten (YOLO)
  - Webdaten (Items, Gold, Runen)

## Output

Für jedes analysierte Match wird ein separater Ordner innerhalb des `data/`-Verzeichnisses erstellt. Die Struktur eines solchen Match-Ordners sieht wie folgt aus:

```
data/
└── match_<match_id>/
    ├── chat_text/
    │   └── chat_log_<timestamp>.txt
    │   └── chat_region.png
    ├── frames/                  # Einzelne extrahierte Videoframes
    ├── minimap_position/
    │   └── minimap.png          # Detektierter Minimap-Ausschnitt
    ├── webdata/
    │   ├── champion_teams.json
    │   ├── gold_difference_timeline.csv
    │   ├── player_item_build.csv
    │   └── runes.csv
    ├── results.json             # Prediction-Daten (YOLO) mit Timestamps
    └── video.mp4                # Verwendeter Videoausschnitt
```

## Links und weiteres

- 📁 [Google Drive](https://drive.google.com/drive/folders/1Pwm0Mcg50vX-ixz6fGrneHgVgbUvo9yX?usp=drive_link) – Zeitplan & Arbeit
- 📌 [Task Management Board (Miro)](https://miro.com/app/board/uXjVIdhHWqI=/?share_link_id=811328732684)
