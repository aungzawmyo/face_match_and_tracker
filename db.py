import sqlite3, numpy as np, os, sys
import logging

# Setup logging for database operations
logger = logging.getLogger(__name__)

# Handle PyInstaller executable path for database
if getattr(sys, 'frozen', False):
    # Running as executable - use current working directory
    DB_PATH = os.path.join(os.getcwd(), "face.db")
    logger.info(f"Running as executable - DB_PATH: {DB_PATH}")
else:
    # Running as script - use script directory
    DB_PATH = os.path.join(os.path.dirname(__file__), "face.db")
    logger.info(f"Running as script - DB_PATH: {DB_PATH}")

logger.info(f"Database file exists: {os.path.exists(DB_PATH)}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Script directory: {os.path.dirname(__file__)}")

def connect():
    try:
        logger.info(f"Attempting to connect to database: {DB_PATH}")
        con = sqlite3.connect(DB_PATH, check_same_thread=False)
        con.execute("PRAGMA foreign_keys=ON")
        logger.info("Database connection successful")
        return con
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def init_db():
    try:
        logger.info("Initializing database...")
        con = connect()
        
        # Handle PyInstaller executable path
        if getattr(sys, 'frozen', False):
            # Running as executable
            base_path = sys._MEIPASS
            logger.info(f"Running as executable - base_path: {base_path}")
        else:
            # Running as script
            base_path = os.path.dirname(__file__)
            logger.info(f"Running as script - base_path: {base_path}")
        
        mig_path = os.path.join(base_path, "migrations.sql")
        logger.info(f"Migration file path: {mig_path}")
        logger.info(f"Migration file exists: {os.path.exists(mig_path)}")
        
        if not os.path.exists(mig_path):
            logger.error(f"Migration file not found at: {mig_path}")
            raise FileNotFoundError(f"Migration file not found: {mig_path}")
        
        with open(mig_path, "r", encoding="utf8") as f:
            migration_sql = f.read()
            logger.info(f"Loaded migration SQL ({len(migration_sql)} characters)")
            con.executescript(migration_sql)
        
        con.commit()
        logger.info("Database initialization completed successfully")
        return con
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()

def from_blob(b: bytes) -> np.ndarray:
    return np.frombuffer(b, dtype=np.float32)

def get_person_by_name(name):
    """Get full person data by name"""
    try:
        logger.info(f"Getting person by name: {name}")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, phone, dob, link, info, social_link, info1, note, created_at
            FROM people 
            WHERE name = ?
        """, (name,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
        
    except Exception as e:
        print(f"Error getting person by name: {e}")
        return None
    finally:
        logger.info("Closing database connection")
        conn.close()

def update_person_details(person_id, **kwargs):
    """Update person details with provided fields"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clauses = []
        values = []
        
        for field, value in kwargs.items():
            if field in ['phone', 'dob', 'link', 'info', 'social_link', 'info1', 'note']:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if set_clauses:
            query = f"UPDATE people SET {', '.join(set_clauses)} WHERE id = ?"
            values.append(person_id)
            cursor.execute(query, values)
            conn.commit()
            logger.info(f"Updated person {person_id} with fields: {list(kwargs.keys())}")
        
    except Exception as e:
        logger.error(f"Error updating person details: {e}")
        raise
    finally:
        conn.close()

def add_track_event(track_id, person_id=None, name=None, confidence=None, kind='match'):
    """Add a track event to the database (legacy function, use add_smart_track_event instead)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (track_id, person_id, name, confidence, kind)
            VALUES (?, ?, ?, ?, ?)
        """, (track_id, person_id, name, confidence, kind))
        
        conn.commit()
        logger.info(f"Added track event: track_id={track_id}, name={name}, kind={kind}")
        
    except Exception as e:
        logger.error(f"Error adding track event: {e}")
    finally:
        conn.close()

def add_smart_track_event(track_id, person_id=None, name=None, confidence=None, kind='match', session_timeout_minutes=5):
    """Add a track event only if it's a new session (person entered/re-entered)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if this person has been detected recently (within session timeout)
        if name and name != 'Unknown' and 'Maybe' not in name:
            cursor.execute("""
                SELECT MAX(timestamp) as last_seen
                FROM events 
                WHERE name = ? AND kind IN ('match', 'enter')
                ORDER BY timestamp DESC
                LIMIT 1
            """, (name,)) 
            result = cursor.fetchone()
            if result and result[0]:
                last_seen = result[0]
                
                # Parse the timestamp and check if it's within the session timeout
                from datetime import datetime, timedelta
                try:
                    last_seen_dt = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S')
                    now = datetime.now()
                    time_diff = now - last_seen_dt
                    
                    # If last seen within session timeout, don't add new record
                    if time_diff < timedelta(minutes=session_timeout_minutes):
                        logger.debug(f"Person {name} still in session (last seen {time_diff.total_seconds():.1f}s ago), skipping event")
                        return False
                    else:
                        # Person re-entered after timeout - this is a new session
                        kind = 'enter'
                        logger.info(f"Person {name} re-entered after {time_diff.total_seconds():.1f}s (new session)")
                        
                except ValueError as e:
                    logger.warning(f"Could not parse timestamp {last_seen}: {e}")
        
        # For unknown persons, use track_id to avoid duplicates
        elif name == 'Unknown':
            cursor.execute("""
                SELECT MAX(timestamp) as last_seen
                FROM events 
                WHERE track_id = ? AND kind IN ('unknown', 'enter')
                ORDER BY timestamp DESC
                LIMIT 1
            """, (track_id,))
            
            result = cursor.fetchone()
            if result and result[0]:
                last_seen = result[0]
                
                from datetime import datetime, timedelta
                try:
                    last_seen_dt = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S')
                    now = datetime.now()
                    time_diff = now - last_seen_dt
                    
                    # For unknown persons, use shorter timeout (2 minutes)
                    if time_diff < timedelta(minutes=2):
                        logger.debug(f"Unknown person track {track_id} still active, skipping event")
                        return False
                    else:
                        kind = 'enter'
                        logger.info(f"Unknown person track {track_id} re-entered")
                        
                except ValueError as e:
                    logger.warning(f"Could not parse timestamp {last_seen}: {e}")
        else:
            logger.debug(f"Name is None or invalid, adding event without session check")
            return False
        
        # Add the new event
        cursor.execute("""
            INSERT INTO events (track_id, person_id, name, confidence, kind)
            VALUES (?, ?, ?, ?, ?)
        """, (track_id, person_id, name, confidence, kind))
        
        conn.commit()
        logger.info(f"Added smart track event: track_id={track_id}, name={name}, kind={kind}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding smart track event: {e}")
        return False
    finally:
        conn.close()

def get_active_sessions(session_timeout_minutes=5):
    """Get currently active tracking sessions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        from datetime import datetime, timedelta
        timeout_time = (datetime.now() - timedelta(minutes=session_timeout_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            SELECT DISTINCT name, MAX(timestamp) as last_seen, track_id
            FROM events 
            WHERE timestamp > ? AND kind IN ('match', 'unknown', 'enter')
            GROUP BY COALESCE(name, track_id)
            ORDER BY last_seen DESC
        """, (timeout_time,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return []
    finally:
        conn.close()

def get_track_history(limit=100):
    """Get track history events"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, track_id, person_id, name, confidence, kind
            FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        # Convert rows to dict and ensure proper data types with robust error handling
        events = []
        for row in rows:
            event = dict(row)
            
            # Handle each field with multiple fallback strategies
            for field in ['timestamp', 'name', 'kind']:
                value = event.get(field)
                if isinstance(value, bytes):
                    try:
                        # Try UTF-8 first
                        event[field] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            # Try latin-1 as fallback
                            event[field] = value.decode('latin-1')
                            logger.warning(f"Used latin-1 fallback for {field} in event {event.get('id')}")
                        except UnicodeDecodeError:
                            # Last resort: use replacement characters
                            event[field] = value.decode('utf-8', errors='replace')
                            logger.warning(f"Used replacement characters for {field} in event {event.get('id')}")
                        
                        # Apply field-specific defaults for corrupted data
                        if field == 'timestamp' and not str(event[field]).replace('�', '').strip():
                            event[field] = '1970-01-01 00:00:00'
                        elif field == 'name' and not str(event[field]).replace('�', '').strip():
                            event[field] = 'Unknown'
                        elif field == 'kind' and not str(event[field]).replace('�', '').strip():
                            event[field] = 'unknown'
            
            # Ensure numeric fields are proper types
            try:
                if event.get('confidence') is not None:
                    event['confidence'] = float(event['confidence'])
            except (ValueError, TypeError):
                event['confidence'] = 0.0
                
            try:
                if event.get('track_id') is not None:
                    event['track_id'] = int(event['track_id'])
            except (ValueError, TypeError):
                event['track_id'] = 0
                
            try:
                if event.get('person_id') is not None:
                    event['person_id'] = int(event['person_id'])
            except (ValueError, TypeError):
                event['person_id'] = None
            
            events.append(event)
            
        return events
        
    except Exception as e:
        logger.error(f"Error getting track history: {e}")
        return []
    finally:
        conn.close()

def clear_track_history():
    """Clear all track history events"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM events")
        deleted_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"Cleared {deleted_count} track history events")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error clearing track history: {e}")
        raise
    finally:
        conn.close()

def clean_corrupted_events():
    """Clean up corrupted event data in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all events
        cursor.execute("SELECT id, timestamp, name, kind FROM events")
        rows = cursor.fetchall()
        
        updates = []
        for row in rows:
            event_id, timestamp, name, kind = row
            needs_update = False
            clean_data = {}
            
            # Check and clean timestamp
            if isinstance(timestamp, bytes):
                try:
                    clean_data['timestamp'] = timestamp.decode('utf-8')
                except UnicodeDecodeError:
                    clean_data['timestamp'] = '1970-01-01 00:00:00'
                needs_update = True
            
            # Check and clean name
            if isinstance(name, bytes):
                try:
                    clean_data['name'] = name.decode('utf-8')
                except UnicodeDecodeError:
                    clean_data['name'] = 'Unknown'
                needs_update = True
            
            # Check and clean kind
            if isinstance(kind, bytes):
                try:
                    clean_data['kind'] = kind.decode('utf-8')
                except UnicodeDecodeError:
                    clean_data['kind'] = 'unknown'
                needs_update = True
            
            if needs_update:
                updates.append((event_id, clean_data))
        
        # Apply updates
        for event_id, clean_data in updates:
            if 'timestamp' in clean_data:
                cursor.execute("UPDATE events SET timestamp = ? WHERE id = ?", 
                             (clean_data['timestamp'], event_id))
            if 'name' in clean_data:
                cursor.execute("UPDATE events SET name = ? WHERE id = ?", 
                             (clean_data['name'], event_id))
            if 'kind' in clean_data:
                cursor.execute("UPDATE events SET kind = ? WHERE id = ?", 
                             (clean_data['kind'], event_id))
        
        conn.commit()
        logger.info(f"Cleaned {len(updates)} corrupted events in database")
        return len(updates)
        
    except Exception as e:
        logger.error(f"Error cleaning corrupted events: {e}")
        return 0
    finally:
        conn.close()

def get_track_stats():
    """Get track history statistics with session-aware counting"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total events (entries/sessions)
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        
        # Events by kind with better descriptions
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN kind = 'match' THEN 'Recognized Entries'
                    WHEN kind = 'enter' THEN 'Person Re-entries'
                    WHEN kind = 'unknown' THEN 'Unknown Entries'
                    ELSE kind
                END as event_type,
                COUNT(*) as count
            FROM events
            GROUP BY kind
        """)
        events_by_kind = dict(cursor.fetchall())
        
        # Unique people tracked (distinct names, excluding Unknown)
        cursor.execute("""
            SELECT COUNT(DISTINCT name) 
            FROM events 
            WHERE name IS NOT NULL AND name != 'Unknown'
        """)
        unique_people = cursor.fetchone()[0]
        
        # Recent activity (last hour) - actual entries, not continuous detections
        cursor.execute("""
            SELECT COUNT(*) 
            FROM events 
            WHERE datetime(timestamp) > datetime('now', '-1 hour')
        """)
        recent_activity = cursor.fetchone()[0]
        
        # Most frequent visitors (top 5)
        cursor.execute("""
            SELECT name, COUNT(*) as visits
            FROM events 
            WHERE name IS NOT NULL AND name != 'Unknown'
            GROUP BY name
            ORDER BY visits DESC
            LIMIT 5
        """)
        frequent_visitors = cursor.fetchall()
        
        # Today's activity
        cursor.execute("""
            SELECT COUNT(*) 
            FROM events 
            WHERE DATE(timestamp) = DATE('now')
        """)
        today_activity = cursor.fetchone()[0]
        
        return {
            'total_events': total_events,
            'events_by_kind': events_by_kind,
            'unique_people': unique_people,
            'recent_activity': recent_activity,
            'frequent_visitors': frequent_visitors,
            'today_activity': today_activity
        }
        
    except Exception as e:
        logger.error(f"Error getting track stats: {e}")
        return {
            'total_events': 0,
            'events_by_kind': {},
            'unique_people': 0,
            'recent_activity': 0,
            'frequent_visitors': [],
            'today_activity': 0
        }
    finally:
        conn.close()

# Updated add_person function to include new fields
def add_person(conn,name, encoding_path, photo_path=None, phone=None, dob=None, link=None, info=None, social_link=None, info1=None, note=None):
    # conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO people(name, phone, dob, link, info, social_link, info1, note) VALUES (?,?,?,?,?,?,?,?)", 
        (name, phone, dob, link, info, social_link, info1, note)
    )
    conn.commit()
    person_id = cur.lastrowid
    # conn.close()
    return person_id

def get_person_by_name_legacy(con, name):
    cur = con.cursor()
    cur.execute("SELECT id, name, phone, dob, link, info, social_link, info1, note FROM people WHERE name=?", (name,))
    return cur.fetchone()

def get_person_by_id(con, person_id):
    cur = con.cursor()
    cur.execute("SELECT id, name, phone, dob, link, info, social_link, info1, note FROM people WHERE id=?", (person_id,))
    return cur.fetchone()

def update_person(con, person_id, name, phone="", dob="", link="", info="", social_link="", info1="", note=""):
    cur = con.cursor()
    cur.execute(
        "UPDATE people SET name=?, phone=?, dob=?, link=?, info=?, social_link=?, info1=?, note=? WHERE id=?",
        (name, phone, dob, link, info, social_link, info1, note, person_id)
    )
    con.commit()

def delete_person(con, person_id):
    con.execute("DELETE FROM people WHERE id=?", (person_id,))
    con.commit()

def add_embedding(con, person_id, vec, src_path=None):
    import numpy as np
    nrm = float(np.linalg.norm(vec))
    cur = con.cursor()
    cur.execute(
        "INSERT INTO embeddings(person_id, vec, norm, src_path) VALUES (?,?,?,?)",
        (person_id, to_blob(vec), nrm, src_path),
    )
    con.commit()

def load_gallery(con):
    people = {}
    cur = con.cursor()
    for pid, name in cur.execute("SELECT id,name FROM people"):
        # Use a separate cursor for the nested query to avoid iteration issues
        cur2 = con.cursor()
        vecs = [from_blob(b) for (b,) in cur2.execute(
            "SELECT vec FROM embeddings WHERE person_id=?", (pid,)
        )]
        # cur2.close()
        # Normalize
        normed = []
        for v in vecs:
            n = (np.linalg.norm(v) + 1e-8)
            normed.append((v / n).astype(np.float32))
        people[name] = (pid, normed)
    # cur.close()
    return people  # name -> (pid, [vecs])

def add_event(con, track_id, person_id, name, confidence, frame_path, kind):
    con.execute(
        "INSERT INTO events(track_id, person_id, name, confidence, frame_path, kind) VALUES (?,?,?,?,?,?)",
        (track_id, person_id, name, confidence, frame_path, kind),
    )
    con.commit()
