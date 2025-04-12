# Automatisierte Ping-Erkennung in League of Legends

## Projektübersicht

Dieses Projekt basiert auf **[DeeperLeague](https://github.com/davidweatherall/DeeperLeague)** und erweitert dessen Funktionalität:  
Neben der Erkennung der **Champion-Positionen auf der Minimap** wird nun auch die **automatische Identifikation von Smart-Pings** ermöglicht.

Ziel ist es, ein **ganzheitliches System zur Analyse von Replay-Daten in League of Legends** zu entwickeln. Dieses soll:
- die **Position von Champions** über den Spielverlauf verfolgen,
- die **Nutzung von Pings** automatisch erkennen und auswerten,
- und diese Informationen mit **kontextbezogenen Match-Daten** (z. B. Item-Builds und Gold-Differenz) verbinden.

Die Ergebnisse werden visuell über eine interaktive **Streamlit-Weboberfläche** dargestellt.

## Funktionen

- **Automatische Erkennung von Smart-Pings** auf der Minimap mithilfe von YOLOv8  
- **Präzise Champion-Positionen** auf Frame-Basis im Videomaterial  
- **Ergänzung durch Webdaten** wie Runen, Item-Build-Timelines und Gold-Differenz  
- **Interaktive Visualisierung** der Predictions mit Zeitslider, Events und Overlay  
- **Nutzung von Twitch-VODs** als Inputquelle für Matchanalysen

## Setup

**Modell trainieren und testen**
- Um ein neues YOLOv8-Modell zu trainieren, kann mit ```generateTestingData.py``` ein Datensatz erzeugt werden. Abhängig von den gewählten Parametern werden verschiedene Minimap-Bilder mit Champion- und Ping-Icons generiert.
- ```prepTraining.py``` bereitet die Daten auf, indem sie in Trainings- und Validierungsdatensätze aufgeteilt werden.
- Das Training wird mit ```train_with_pings.py``` gestartet. Standardmässig sind 64 Epochen mit einer Patience von 10 definiert. Das Ergebnis ist das trainierte Modell ```best.pt``` sowie diverse Leistungsmetriken.
- Um das Modell nach dem Training zu testen, kann mit ```generateTestingImages.py``` ein Testdatensatz erzeugt und evaluiert werden. Beispiel:
  ```yolo val model=runs/detect/train12/weights/best.pt data=minimap.yaml split=test save_json=True```

**Video Prediction**
- Mit ```twitch_vod_download.py``` kann ein bestimmter Ausschnitt aus einem Twitch-VOD heruntergeladen werden. Dafür wird der **[TwitchDownloaderCLI](https://github.com/lay295/TwitchDownloader)** verwendet, der lokal installiert und konfiguriert sein muss. *(Hinweis: Unter Windows wurde dieser als Umgebungsvariable hinterlegt, um ihn systemweit nutzen zu können.)*
- Benötigte Parameter: *VOD-URL oder ID*, *Startzeit (HH:MM:SS)* und *Endzeit (HH:MM:SS)*.
- Achte darauf, dass der gewählte Zeitraum genau dem Spiel entspricht – also mit Spielbeginn (00:00) startet und kurz nach der Zerstörung des Nexus endet – um fehlerhafte Predictions zu vermeiden.
- ```predict_video.py``` analysiert das Video, extrahiert die Minimap aus jedem Frame, wendet darauf das YOLOv8-Modell an und speichert die Prediction-Ergebnisse mit Zeitstempeln in einer JSON-Datei. Voraussetzungen:
  - Das trainierte Modell ```best.pt```
  - Heruntergeladenes Video
  - Installiertes ```ffmpeg```

**Datenextraktion aus dem Web**
- Mit ```scrapeWebData.py``` werden Match-Daten von **[leagueofgraphs.com](https://www.leagueofgraphs.com/)** für einen bestimmten Spieler extrahiert. Erfasst werden:
  - Item-Builds mit Zeitstempeln
  - Gold-Differenz-Verlauf
  - Verwendete Runen  
- Die entsprechende Match-URL und die ```participantId``` müssen aktuell noch manuell im Skript gesetzt werden.

**Visualisierung in Streamlit**
- Die Visualisierung erfolgt mit Streamlit. Die Web-App zeigt die Predictions aus einem Match interaktiv auf einer Minimap an. Dabei werden die Ergebnisse der YOLO-Videovorhersage mit den extrahierten Webdaten (Items, Gold-Differenz) kombiniert und übersichtlich dargestellt.
- Die App wird mit folgendem Befehl gestartet: ```streamlit run viewer.py```

## Links und weiteres
- **[Google Drive](https://drive.google.com/drive/folders/1Pwm0Mcg50vX-ixz6fGrneHgVgbUvo9yX?usp=drive_link)** für den Zeitplan und die Disposition (wird regelmässig geupdated)
- **[Taks Management Board](https://miro.com/app/board/uXjVIdhHWqI=/?share_link_id=811328732684)**
