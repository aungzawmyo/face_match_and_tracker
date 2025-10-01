Great—let’s tailor the plan for a **CPU-only, Tkinter desktop app** that does: enroll faces (≥5 imgs/person), live tracking + recognition, list unknowns, counts, history, and manages people in **SQLite**.

# High-level architecture

* **UI (Tkinter)**: tabs = **People**, **Live**, **Unknowns**, **History**, **Settings**.
* **Pipeline (CPU)**:

  * **Detector**: YOLOv8n-face **or** SCRFD (InsightFace) → face boxes
  * **Tracker**: DeepSORT → stable track IDs
  * **Embedder**: InsightFace ArcFace (`buffalo_l`) on **onnxruntime (CPU)** → 512-D vectors
  * **Matcher**: cosine distance vs embeddings in SQLite (multi-sample per person)
* **Storage (SQLite)**: people, embeddings, events (history), unknown snapshots (optional files), app settings.

# Dependencies (CPU-only)

```bash
pip install ultralytics==8.* insightface onnxruntime opencv-python deep-sort-realtime numpy pillow tk
# If SCRFD (InsightFace) for detection: you can skip YOLO; otherwise keep YOLOv8n-face.pt.
```

# Project layout

```
face_app/
  app.py                 # Tkinter main
  pipeline.py            # detect/track/embed/match (threaded)
  db.py                  # SQLite helpers
  models/                # downloaded ONNX/pt weights
  storage/
    people/              # saved enrolled images per person
    unknowns/            # snapshots of unknown faces by day
  migrations.sql         # schema
```

# SQLite schema (migrations.sql)

```sql
CREATE TABLE IF NOT EXISTS people (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  note TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS embeddings (
  id INTEGER PRIMARY KEY,
  person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
  vec BLOB NOT NULL,          -- 512 x float32 as bytes
  norm REAL NOT NULL,         -- optional; store L2 norm (=1.0 if normalized)
  src_path TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (  -- recognition & tracking history
  id INTEGER PRIMARY KEY,
  timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
  track_id INTEGER,           -- DeepSORT track
  person_id INTEGER,          -- NULL if unknown
  name TEXT,                  -- cached at event time
  confidence REAL,            -- 1 - cosine_distance (or similar)
  frame_path TEXT,            -- optional snapshot for audit
  kind TEXT CHECK(kind IN ('appear','update','disappear','match','unknown')) NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);
```

# Matching logic (clear + CPU-friendly)

* Compute **normalized 512-D** ArcFace embeddings (`normed_embedding` from InsightFace).
* Store **5–15 vectors/person** (front/left/right, glasses/no-glasses, varied lighting).
* For a live embedding **e**, compute **cosine distance** to all vectors of each person and take **min** (or median of K-nearest).
* Thresholds (start points):

  * **MATCH\_THR = 0.45** (distance < 0.45 ⇒ accept)
  * **UNKNOWN\_THR = 0.55** (distance > 0.55 ⇒ Unknown)
  * **grey zone** in between ⇒ “Maybe: X”
* Require **2 consecutive frames** below MATCH\_THR before confirming a label (reduces false accepts on CPU noise).

# Tkinter UI plan (simple + responsive)

* **People tab**

  * Listbox of people; buttons: **Add**, **Import Images (≥5)**, **Extract Embeddings**, **Delete**, **Preview**.
  * When importing: copy images into `storage/people/<name>/`, compute embeddings, persist to DB.
* **Live tab**

  * Video canvas (using `PIL.ImageTk`) + overlays (names/IDs).
  * Stats row: **Known count**, **Unknown count**, **FPS**, **Active tracks**.
  * Buttons: **Start**, **Stop**, **Save Snapshot**, **Clear Unknowns**, **Settings**.
* **Unknowns tab**

  * Grid of unknown face thumbnails collected today. Button: **Promote to Person** → opens enrollment flow with selected images.
* **History tab**

  * Table (Treeview): time, name/Unknown, confidence, event type. Filters by date/name.
* **Settings tab**

  * Threshold sliders, `max_age`, `n_init`, **REID\_EVERY\_N**, “Store unknown snapshots” toggle, camera index/RTSP URL.

> Keep the **video loop in a background thread**; use `root.after(16, redraw)` to update the canvas. Never block Tk’s mainloop.

# Core pipelines (concise code patterns)

## DB helpers (db.py)

```python
import sqlite3, numpy as np, os, json

DB_PATH = "face.db"

def connect(): 
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("PRAGMA foreign_keys=ON")
    return con

def to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()

def from_blob(b: bytes) -> np.ndarray:
    return np.frombuffer(b, dtype=np.float32)

def add_person(con, name, note=""):
    cur = con.cursor()
    cur.execute("INSERT INTO people(name, note) VALUES (?,?)", (name, note))
    con.commit(); return cur.lastrowid

def add_embedding(con, person_id, vec, src_path=None):
    cur = con.cursor()
    cur.execute("INSERT INTO embeddings(person_id, vec, norm, src_path) VALUES (?,?,?,?)",
                (person_id, to_blob(vec), float(np.linalg.norm(vec)), src_path))
    con.commit()

def load_gallery(con):
    people = {}
    for pid, name in con.execute("SELECT id,name FROM people"):
        vecs = [from_blob(b) for (b,) in con.execute(
            "SELECT vec FROM embeddings WHERE person_id=?", (pid,))]
        # Ensure L2-normalized
        vecs = [v / (np.linalg.norm(v)+1e-8) for v in vecs]
        people[name] = (pid, vecs)
    return people  # name -> (person_id, [np.array])
```

## Enrollment (extract embeddings from ≥5 images)

```python
import cv2, glob, os, numpy as np
import insightface
from ultralytics import YOLO  # if you use YOLO for detection

fa = insightface.app.FaceAnalysis(name="buffalo_l"); fa.prepare(ctx_id=-1)  # CPU

def enroll_person(con, name, img_dir):
    pid = add_person(con, name)
    imgs = sorted(glob.glob(os.path.join(img_dir, "*.*")))
    ok = 0
    for p in imgs:
        im = cv2.imread(p)
        faces = fa.get(im)  # returns aligned faces + normed_embedding
        if not faces: continue
        emb = faces[0].normed_embedding  # already L2-normalized
        add_embedding(con, pid, emb, src_path=p); ok += 1
    assert ok >= 5, "Need ≥5 usable faces"
```

## Live loop (detect → track → embed → match)

```python
import cv2, time, numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort

MATCH_THR, UNKNOWN_THR, REID_EVERY_N = 0.45, 0.55, 10

def cosine_dist(a,b): return 1 - float(np.dot(a,b) / (np.linalg.norm(a)*np.linalg.norm(b)+1e-8))

def make_matcher(gallery):  # name -> (pid, [vecs])
    # Pre-stack for faster CPU scans
    flat = []
    for name,(pid,vecs) in gallery.items():
        for v in vecs: flat.append((name,pid,v))
    return flat

def match_embedding(e, flat_gallery):
    best = ("Unknown", None, 1e9)
    # Linear scan on CPU; optimize later if needed (faiss/annoy)
    for name, pid, g in flat_gallery:
        d = cosine_dist(e, g)
        if d < best[2]: best = (name, pid, d)
    return best  # (name, pid, dist)

def run_stream(con, video_src, detector, face_app, on_event, stop_flag):
    tracker = DeepSort(max_age=30, n_init=2)
    gallery = load_gallery(con)
    flat = make_matcher(gallery)
    cache = {}  # track_id -> {'last_emb':..., 'last_name':..., 'hit_count':int}

    cap = cv2.VideoCapture(video_src)
    frame_idx = 0
    while not stop_flag.is_set():
        ok, frame = cap.read()
        if not ok: break

        # Detect faces (YOLO example)
        res = detector(frame, verbose=False)[0]
        dets = [(*b[:2], b[2]-b[0], b[3]-b[1], float(c), 'face')
                for b,c in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.conf.cpu().numpy())]

        tracks = tracker.update_tracks(dets, frame=frame)

        for tr in [t for t in tracks if t.is_confirmed()]:
            tid = tr.track_id
            x,y,w,h = map(int, tr.to_ltwh())
            crop = frame[max(0,y):y+h, max(0,x):x+w]
            # Embed every N frames
            if (tid not in cache) or (frame_idx % REID_EVERY_N == 0):
                faces = face_app.get(crop)
                if faces:
                    e = faces[0].normed_embedding
                    name, pid, dist = match_embedding(e, flat)
                    # hysteresis
                    if dist < MATCH_THR:
                        label = name
                        cache[tid] = {'last_emb':e, 'last_name':name, 'pid':pid, 'hits': cache.get(tid,{}).get('hits',0)+1}
                        if cache[tid]['hits'] == 2:  # confirm after 2 hits
                            on_event('match', tid, pid, name, 1.0 - dist, frame, (x,y,w,h))
                    elif dist > UNKNOWN_THR:
                        label = 'Unknown'
                        cache[tid] = {'last_emb':e, 'last_name':'Unknown', 'pid':None, 'hits':0}
                        on_event('unknown', tid, None, 'Unknown', 1.0 - dist, frame, (x,y,w,h))
                    else:
                        label = f"Maybe:{name}"
                        cache[tid] = {'last_emb':e, 'last_name':label, 'pid':pid, 'hits':0}

            # Draw
            label = cache.get(tid,{}).get('last_name','...')
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.putText(frame, f"{label} (ID {tid})", (x, max(0,y-6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

        # hand off frame to Tk canvas (convert via PIL)
        # ui_update_frame(frame)

        frame_idx += 1

    cap.release()
```

### `on_event` writes to history + snapshots

```python
import os, cv2
def on_event(kind, track_id, person_id, name, conf, frame, box):
    x,y,w,h = box
    face = frame[y:y+h, x:x+w]
    day = time.strftime("%Y-%m-%d")
    os.makedirs(f"storage/unknowns/{day}", exist_ok=True)
    path = f"storage/unknowns/{day}/{int(time.time()*1000)}_{name}.jpg"
    cv2.imwrite(path, face)
    con = ... # get connection
    con.execute("INSERT INTO events(track_id, person_id, name, confidence, frame_path, kind) VALUES (?,?,?,?,?,?)",
                (track_id, person_id, name, conf, path, kind))
    con.commit()
```

# Tkinter integration notes

* Use `threading.Thread(target=run_stream, ...)` for the pipeline; keep a `stop_flag` (`threading.Event`).
* Convert OpenCV frame → PIL Image → `ImageTk.PhotoImage` and set it on a `Label` every \~16 ms with `after`.
* For tables (**History**), use `ttk.Treeview` with scrollbar and date filters.
* For unknown thumbnails, scan `storage/unknowns/<today>/` and display clickable images (promote → People tab).

# CPU performance tips

* Use **SCRFD** detector from InsightFace instead of YOLO if YOLO is slow on your CPU; SCRFD is well-optimized.
* Lower inference size: 640 → 480; skip embedding every frame (**REID\_EVERY\_N = 10–15**).
* Only embed faces **> min\_box** size (e.g., width ≥ 80 px) & decent detector confidence.
* Consider **ByteTrack** if DeepSORT is heavy; DeepSORT is usually fine on CPU though.

# Managing people & (re)training

* There’s no heavy “training”; you’re just **storing embeddings**.
* When user clicks **Extract Embeddings**, run detector+embedder on each uploaded image; store all usable vectors.
* You can show **coverage score** (how many pose angles captured) to guide the user.

# Edge cases & quality gates

* If multiple faces in an enrollment image, pick the **largest** or show a picker.
* Blur/pose gate: skip embeddings when quality < threshold (use `faces[0].det_score` or size).
* For privacy, allow **Delete person** → cascades to embeddings & (optionally) events.

# Minimal “Settings” defaults

* `MATCH_THR=0.45`, `UNKNOWN_THR=0.55`
* `max_age=30`, `n_init=2`, `REID_EVERY_N=10`
* Detector size: 640 (drop to 512 if needed)
* “Store unknown snapshots”: ON

# What I can generate next (tell me which you want)

1. A **starter repo** with Tkinter UI stubs, DB layer, and a working CPU pipeline.
2. **Ready-made SQL + enrollment CLI** (`python enroll.py --name Alice ./photos/alice/`).
3. A **Tkinter People tab** that imports images, extracts embeddings, and updates the gallery.
4. A **Live tab** that starts/stops the background thread and renders frames smoothly.

If you share your **camera source** (USB index or RTSP) and preferred **detector** (YOLO vs SCRFD), I’ll drop in the exact code for a working MVP.
