CREATE TABLE IF NOT EXISTS people (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  phone TEXT,
  dob TEXT,
  link TEXT,
  info TEXT,
  social_link TEXT,
  info1 TEXT,
  note TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS embeddings (
  id INTEGER PRIMARY KEY,
  person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
  vec BLOB NOT NULL,
  norm REAL NOT NULL,
  src_path TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
  track_id INTEGER,
  person_id INTEGER,
  name TEXT,
  confidence REAL,
  frame_path TEXT,
  kind TEXT CHECK(kind IN ('appear','update','disappear','match','unknown')) NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);
