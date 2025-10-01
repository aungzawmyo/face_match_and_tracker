# FaceApp (CPU • Tkinter)

A starter repo for **face detection + tracking + recognition** on **CPU only**, with:
- Tkinter UI (People & Live tabs)
- SQLite storage (people, embeddings, events)
- Enrollment CLI: `python enroll.py --name Alice ./photos/alice/`
- Working pipeline using **InsightFace (SCRFD + ArcFace)** for detection/embeddings and **DeepSORT** for tracking

## Features
- **People tab**: import a folder of images (≥5), extract embeddings, and save to SQLite
- **Live tab**: start/stop webcam or RTSP; draws boxes + names; shows FPS/known/unknown/track counts
- **Events**: unknown/match snapshots saved to `storage/unknowns/YYYY-MM-DD/` and recorded in DB

## Install (Python 3.10+ recommended)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> On first run, InsightFace will download model weights (SCRFD detector + ArcFace) to your user cache directory.

## Initialize DB
```bash
python -c "from db import init_db; init_db(); print('DB ready')"
```

## Enroll People (CLI)
Expect **5–15** images per person (front/left/right; glasses on/off; varied lighting).
```bash
python enroll.py --name Alice /path/to/alice_images/
python enroll.py --name Bob   /path/to/bob_images/
```
If a person already exists, new embeddings are appended.

## Run the App
```bash
python app.py
```
- **Video Source**: enter `0` for default webcam, or a file path/RTSP URL; click **Start**.
- Stats show **FPS | Known | Unknown | Tracks**.

## How it works
- **Detection + Embedding**: `insightface.app.FaceAnalysis('buffalo_l')` (CPU, onnxruntime).
- **Tracking**: DeepSORT (CPU) using detector bboxes; we re-embed every N frames to keep identity fresh.
- **Matching**: cosine distance vs stored normalized embeddings; thresholds default to `MATCH_THR=0.45`, `UNKNOWN_THR=0.55`.

## Project Layout
```
face_app/
  app.py              # Tkinter UI (People, Live)
  enroll.py           # CLI enrollment from a folder of images
  pipeline.py         # Video worker (detect→track→embed→match) + DB event logging
  db.py               # SQLite helpers + init
  migrations.sql      # Schema
  storage/people/     # (optional) where you might copy enrolled images if you add that later
  storage/unknowns/   # snapshots of unknown/match events by date
  requirements.txt
  README.md
```

## Tuning & Notes
- CPU tips: lower camera resolution, re-embed every 10–15 frames, skip tiny faces (<80px width).
- Thresholds: adjust in `pipeline.py` (`MATCH_THR`, `UNKNOWN_THR`, `REID_EVERY_N`).
- To add **History**/**Unknowns tab**, read from the `events` table and render thumbnails.

## License
MIT
