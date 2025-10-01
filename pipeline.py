import os, time, threading, cv2, numpy as np, logging
from deep_sort_realtime.deepsort_tracker import DeepSort
import insightface
from db import load_gallery, add_event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('facescanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Matching thresholds - Optimized based on testing
# MATCH_THR = 0.50      # Confident match (was 0.45)
# UNKNOWN_THR = 0.65    # Beyond this = unknown (was 0.55)
# REID_EVERY_N = 3      # Re-identify every 3 frames for faster recognition
MATCH_THR = 0.40      # Confident match (was 0.45)
UNKNOWN_THR = 0.65    # Beyond this = unknown (was 0.55)
REID_EVERY_N = 10      # Re-identify every 3 frames for faster recognition

def cosine_dist(a, b):
    """Calculate cosine distance between two embeddings"""
    # Ensure both are numpy arrays
    a = np.array(a).flatten()
    b = np.array(b).flatten()
    
    # Normalize the vectors
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # Avoid division by zero
    if norm_a == 0 or norm_b == 0:
        return 1.0
    
    # Calculate cosine similarity and convert to distance
    cosine_sim = np.dot(a, b) / (norm_a * norm_b)
    return 1.0 - cosine_sim

def build_flat_gallery(gallery):
    flat = []  # (name, pid, vec)
    for name, (pid, vecs) in gallery.items():
        for v in vecs:
            flat.append((name, pid, v))
    return flat

def match_embedding(e, flat_gallery, use_average=True):
    """
    Match embedding against gallery with optional averaging for better accuracy
    """
    if use_average:
        # Group embeddings by person and use average distance
        person_distances = {}
        for name, pid, g in flat_gallery:
            d = cosine_dist(e, g)
            if name not in person_distances:
                person_distances[name] = []
            person_distances[name].append((d, pid))
        
        # Find best match using average of top 3 closest embeddings per person
        best = ("Unknown", None, 1e9)
        for name, distances in person_distances.items():
            # Sort by distance and take top 3 (or all if less than 3)
            distances.sort(key=lambda x: x[0])
            top_distances = distances[:min(3, len(distances))]
            avg_dist = sum(d[0] for d in top_distances) / len(top_distances)
            
            if avg_dist < best[2]:
                best = (name, top_distances[0][1], avg_dist)  # Use pid from closest match
        
        return best
    else:
        # Original single best match
        best = ("Unknown", None, 1e9)
        for name, pid, g in flat_gallery:
            d = cosine_dist(e, g)
            if d < best[2]:
                best = (name, pid, d)
        return best  # (name, pid, dist)

class VideoWorker:
    def __init__(self, con, video_src=0, on_frame=None, on_stats=None, snapshot_dir="storage/unknowns"):
        logger.info(f"Initializing VideoWorker with video_src={video_src}")
        self.con = con
        self.video_src = video_src
        self.on_frame = on_frame
        self.on_stats = on_stats
        self.snapshot_dir = snapshot_dir
        self._stop = threading.Event()
        self.t = None
        
        try:
            logger.info("Initializing DeepSort tracker...")
            # More aggressive tracker settings to remove stale tracks faster
            # Using only supported parameters for deep_sort_realtime
            self.tracker = DeepSort(
                max_age=7,        # Reduced from 30 - remove tracks after 10 frames without detection
                # max_age=10,        # Reduced from 30 - remove tracks after 10 frames without detection
                n_init=2           # Still require 2 consecutive detections to confirm
            )
            logger.info("DeepSort tracker initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSort tracker: {e}")
            raise
        
        try:
            logger.info("Initializing InsightFace model...")
            self.face_app = insightface.app.FaceAnalysis(name="buffalo_l")
            self.face_app.prepare(ctx_id=-1)  # CPU
            logger.info("InsightFace model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize InsightFace model: {e}")
            raise
            
        self.cache = {}  # track_id -> dict
        self.fps = 0.0
        self._gallery_cache = None
        self._flat_cache = None
        logger.info("VideoWorker initialization completed")

    def refresh_gallery(self):
        """Manually refresh the gallery cache"""
        self._gallery_cache = load_gallery(self.con)
        self._flat_cache = build_flat_gallery(self._gallery_cache)

    def start(self):
        logger.info("Starting VideoWorker...")
        if self.t and self.t.is_alive():
            logger.warning("VideoWorker thread is already running")
            return
        self._stop.clear()
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()
        logger.info("VideoWorker thread started")

    def stop(self):
        logger.info("Stopping VideoWorker...")
        self._stop.set()
        if self.t:
            self.t.join(timeout=1.0)
        logger.info("VideoWorker stopped")

    def _run(self):
        logger.info(f"VideoWorker thread running with video_src={self.video_src}")
        
        # Use DirectShow backend on Windows for better compatibility
        try:
            if isinstance(self.video_src, int):
                logger.info(f"Opening camera index {self.video_src} with DirectShow")
                cap = cv2.VideoCapture(self.video_src, cv2.CAP_DSHOW)
            else:
                logger.info(f"Opening video file: {self.video_src}")
                cap = cv2.VideoCapture(self.video_src)
            
            if not cap.isOpened():
                error_msg = f"Error: Failed to open video source: {self.video_src}"
                logger.error(error_msg)
                if isinstance(self.video_src, int):
                    logger.error(f"Camera index {self.video_src} is not available.")
                    logger.info("Available camera debugging info:")
                    # Try to detect available cameras
                    for i in range(5):
                        test_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                        if test_cap.isOpened():
                            logger.info(f"  Camera {i}: Available")
                            test_cap.release()
                        else:
                            logger.info(f"  Camera {i}: Not available")
                if self.on_stats:
                    self.on_stats(error_msg)
                return
            
            logger.info("Video capture opened successfully")
                
            # Set camera properties for better stability
            if isinstance(self.video_src, int):
                logger.info("Setting camera properties...")
                # Set conservative camera properties to prevent hanging
                try:
                    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    # cap.set(cv2.CAP_PROP_FPS, 15)  # Lower FPS to reduce load
                    # cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to avoid delays
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 360)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                    cap.set(cv2.CAP_PROP_FPS, 10)  # Lower FPS to reduce load
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to avoid delays
                    
                    # Test read a frame to ensure camera is working
                    logger.info("Testing initial frame read...")
                    for attempt in range(3):
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None and test_frame.size > 0:
                            logger.info(f"Camera test successful on attempt {attempt + 1}")
                            break
                        else:
                            logger.warning(f"Camera test failed on attempt {attempt + 1}")
                            time.sleep(0.5)
                    else:
                        logger.error("Camera failed all test attempts")
                        if self.on_stats:
                            self.on_stats("Error: Camera failed initialization tests")
                        cap.release()
                        return
                        
                except Exception as e:
                    logger.error(f"Error setting camera properties: {e}")
                    cap.release()
                    return
            
            logger.info(f"Successfully opened video source: {self.video_src}")
            last = time.time()
            frame_idx = 0
            
        except Exception as e:
            error_msg = f"Critical error in VideoWorker: {e}"
            logger.error(error_msg)
            if self.on_stats:
                self.on_stats(error_msg)
            return
        
        # Initialize gallery cache
        self.refresh_gallery()
        last_gallery_refresh = time.time()
        # GALLERY_REFRESH_INTERVAL = 2.0  # Refresh gallery every 2 seconds for responsiveness
        # skip_frames = 20  # Process every 21st frame to reduce load
        GALLERY_REFRESH_INTERVAL = 5.0  # Refresh gallery every 5 seconds for responsiveness // Higher = less DB queries (5.0, 10.0)
        skip_frames = 5  # Process every 16th frame to reduce load
        frame_counter = 0

        while not self._stop.is_set():
            try:
                # Periodically refresh gallery to pick up newly enrolled people
                current_time = time.time()
                if current_time - last_gallery_refresh > GALLERY_REFRESH_INTERVAL:
                    # self.refresh_gallery()
                    last_gallery_refresh = current_time
                
                ok, frame = cap.read()
                if not ok:
                    logger.warning("Failed to read frame from camera, retrying...")
                    time.sleep(0.1)  # Brief pause before retry
                    continue
                
                # Skip frames to reduce processing load and prevent hanging
                frame_counter += 1
                if frame_counter % (skip_frames + 1) != 0:
                    continue
                
                # Comprehensive frame validation
                if frame is None:
                    logger.warning("Received None frame, skipping...")
                    continue
                
                if not hasattr(frame, 'shape'):
                    logger.warning("Frame has no shape attribute, skipping...")
                    continue
                    
                if frame.size == 0:
                    logger.warning("Frame has zero size, skipping...")
                    continue
                    
                if len(frame.shape) != 3:
                    logger.warning(f"Frame has invalid shape: {frame.shape}, skipping...")
                    continue
                    
                if frame.shape[0] == 0 or frame.shape[1] == 0:
                    logger.warning(f"Frame has zero dimensions: {frame.shape}, skipping...")
                    continue

                # Detect faces via InsightFace (SCRFD) with comprehensive error handling
                faces = []
                try:
                    # Simple timeout mechanism - limit processing time per frame
                    start_time = time.time()
                    faces = self.face_app.get(frame)
                    end_time = time.time()
                    
                    # If face detection takes too long, log it
                    if end_time - start_time > 1.0:
                        logger.warning(f"Face detection took {end_time - start_time:.2f} seconds")
                        
                except Exception as e:
                    logger.error(f"Error in face detection: {e}")
                    continue
                
                dets = []
                for f in faces:
                    try:
                        x1, y1, x2, y2 = map(int, f.bbox)
                        w, h = x2 - x1, y2 - y1
                        conf = float(getattr(f, "det_score", 0.9))
                        # DeepSORT expects format: [([x, y, w, h], conf, class_name), ...]
                        dets.append(([x1, y1, w, h], conf, "face"))
                    except Exception as e:
                        logger.error(f"Error processing face detection: {e}")
                        continue
                
                try:
                    tracks = self.tracker.update_tracks(dets, frame=frame)
                except Exception as e:
                    print(f"DeepSORT error: {e}")
                    tracks = []  # Continue with empty tracks

                # CRITICAL: Clean up cache for tracks that are no longer active
                current_track_ids = set()
                for track in tracks:
                    if track.is_confirmed():
                        current_track_ids.add(track.track_id)
                
                # Remove cache entries for tracks that are no longer confirmed
                stale_track_ids = set(self.cache.keys()) - current_track_ids
                for stale_id in stale_track_ids:
                    del self.cache[stale_id]
                    logger.debug(f"Removed stale track {stale_id} from cache")

                known_cnt, unk_cnt = 0, 0
                current_detections = []  # Track current frame detections
                
                # ONLY process confirmed and ACTIVE tracks with current detections
                active_tracks = [t for t in tracks if t.is_confirmed() and hasattr(t, 'time_since_update') and t.time_since_update < 3]
                
                for tr in active_tracks:
                    tid = tr.track_id
                    x, y, w, h = map(int, tr.to_ltwh())
                    x = max(0, x); y = max(0, y); w = max(1, w); h = max(1, h)
                    
                    # Ensure crop is within frame bounds and has valid dimensions
                    frame_h, frame_w = frame.shape[:2]
                    x = min(x, frame_w - 1)
                    y = min(y, frame_h - 1)
                    w = min(w, frame_w - x)
                    h = min(h, frame_h - y)
                    
                    # Skip if crop dimensions are too small
                    if w < 10 or h < 10:
                        continue
                    
                    # ADDITIONAL CHECK: Verify there's actually a face in this location
                    crop = frame[y:y+h, x:x+w]
                    if crop.size == 0 or crop.shape[0] == 0 or crop.shape[1] == 0:
                        continue
                    
                    # Validate that this track actually corresponds to a current face detection
                    has_matching_detection = False
                    for det in dets:
                        det_bbox = det[0]  # [x, y, w, h]
                        det_x, det_y, det_w, det_h = det_bbox
                        
                        # Calculate IoU (Intersection over Union) to verify overlap
                        overlap_x = max(x, det_x)
                        overlap_y = max(y, det_y)
                        overlap_w = min(x + w, det_x + det_w) - overlap_x
                        overlap_h = min(y + h, det_y + det_h) - overlap_y
                        
                        if overlap_w > 0 and overlap_h > 0:
                            overlap_area = overlap_w * overlap_h
                            track_area = w * h
                            det_area = det_w * det_h
                            union_area = track_area + det_area - overlap_area
                            
                            if union_area > 0:
                                iou = overlap_area / union_area
                                if iou > 0.3:  # 30% overlap threshold
                                    has_matching_detection = True
                                    break
                    
                    # Skip tracks that don't have corresponding face detections
                    if not has_matching_detection:
                        logger.debug(f"Track {tid} has no matching face detection, skipping")
                        continue

                    # Re-embed periodically (force identification for new tracks)
                    force_identify = tid not in self.cache
                    if force_identify or (frame_idx % REID_EVERY_N == 0):
                        try:
                            sub_faces = self.face_app.get(crop)
                            if sub_faces:
                                e = sub_faces[0].normed_embedding
                                name, pid, dist = match_embedding(e, self._flat_cache, use_average=True) if self._flat_cache else ("Unknown", None, 1.0)
                                # Debug output - remove this line in production
                                # print(f"Face recognition: {name} (dist: {dist:.3f}) [Force: {force_identify}]")  
                                label = None
                                if dist < MATCH_THR:
                                    label = name
                                    known_cnt += 1
                                    hits = self.cache.get(tid, {}).get("hits", 0) + 1
                                    self.cache[tid] = {"name": name, "pid": pid, "hits": hits, "dist": dist}
                                    if hits == 2:
                                        # log match event
                                        self._log_event("match", tr, pid, name, 1.0 - dist, frame, (x, y, w, h))
                                elif dist > UNKNOWN_THR:
                                    label = "Unknown"
                                    unk_cnt += 1
                                    self.cache[tid] = {"name": label, "pid": None, "hits": 0, "dist": dist}
                                    self._log_event("unknown", tr, None, "Unknown", 1.0 - dist, frame, (x, y, w, h))
                                else:
                                    label = f"Maybe:{name}"
                                    self.cache[tid] = {"name": label, "pid": pid, "hits": 0, "dist": dist}
                            else:
                                # No face detected in crop, try using original detection with larger margins
                                # print(f"No sub-faces detected in crop for track {tid}, using direct matching")
                                # Use a larger region around the detection for better face detection
                                margin = 20  # Pixels margin around the detection
                                expanded_x = max(0, x - margin)
                                expanded_y = max(0, y - margin)
                                expanded_w = min(frame_w - expanded_x, w + 2*margin)
                                expanded_h = min(frame_h - expanded_y, h + 2*margin)
                                
                                face_region = frame[expanded_y:expanded_y+expanded_h, expanded_x:expanded_x+expanded_w]
                                if face_region.size > 0 and face_region.shape[0] > 30 and face_region.shape[1] > 30:
                                    try:
                                        direct_faces = self.face_app.get(face_region)
                                        if direct_faces:
                                            e = direct_faces[0].normed_embedding
                                            name, pid, dist = match_embedding(e, self._flat_cache, use_average=True) if self._flat_cache else ("Unknown", None, 1.0)
                                            # print(f"Direct face recognition: {name} (dist: {dist:.3f}) [Force: {force_identify}]")
                                            if dist < MATCH_THR:
                                                self.cache[tid] = {"name": name, "pid": pid, "hits": 1, "dist": dist}
                                            elif dist > UNKNOWN_THR:
                                                self.cache[tid] = {"name": "Unknown", "pid": None, "hits": 0, "dist": dist}
                                            else:
                                                self.cache[tid] = {"name": f"Maybe:{name}", "pid": pid, "hits": 0, "dist": dist}
                                        else:
                                            # print(f"No faces in expanded region for track {tid}")
                                            # Try with even larger margin or use full frame face detection
                                            all_faces = self.face_app.get(frame)
                                            if all_faces:
                                                # Find the closest face to our tracking box
                                                best_face = None
                                                best_distance = float('inf')
                                                center_x, center_y = x + w//2, y + h//2
                                                
                                                for face in all_faces:
                                                    bbox = face.bbox.astype(int)
                                                    face_center_x = bbox[0] + (bbox[2] - bbox[0])//2
                                                    face_center_y = bbox[1] + (bbox[3] - bbox[1])//2
                                                    distance = ((center_x - face_center_x)**2 + (center_y - face_center_y)**2)**0.5
                                                    if distance < best_distance:
                                                        best_distance = distance
                                                        best_face = face
                                                
                                                if best_face and best_distance < 100:  # Within 100 pixels
                                                    e = best_face.normed_embedding
                                                    name, pid, dist = match_embedding(e, self._flat_cache, use_average=True) if self._flat_cache else ("Unknown", None, 1.0)
                                                    # print(f"Closest face recognition: {name} (dist: {dist:.3f}) [Force: {force_identify}]")
                                                    if dist < MATCH_THR:
                                                        self.cache[tid] = {"name": name, "pid": pid, "hits": 1, "dist": dist}
                                                    elif dist > UNKNOWN_THR:
                                                        self.cache[tid] = {"name": "Unknown", "pid": None, "hits": 0, "dist": dist}
                                                    else:
                                                        self.cache[tid] = {"name": f"Maybe:{name}", "pid": pid, "hits": 0, "dist": dist}
                                                else:
                                                    # print(f"No suitable face found for track {tid}")
                                                    if tid not in self.cache:
                                                        self.cache[tid] = {"name": "No Face", "pid": None, "hits": 0, "dist": 1.0}
                                            else:
                                                # print(f"No faces detected in entire frame for track {tid}")
                                                if tid not in self.cache:
                                                    self.cache[tid] = {"name": "No Face", "pid": None, "hits": 0, "dist": 1.0}
                                    except Exception as e2:
                                        # print(f"Direct face detection error for track {tid}: {e2}")
                                        if tid not in self.cache:
                                            self.cache[tid] = {"name": "Error", "pid": None, "hits": 0, "dist": 1.0}
                                else:
                                    # print(f"Invalid face region for track {tid}")
                                    if tid not in self.cache:
                                        self.cache[tid] = {"name": "Invalid", "pid": None, "hits": 0, "dist": 1.0}
                        except Exception as e:
                            # print(f"Error processing face crop for track {tid}: {e}")
                            # Set fallback label instead of leaving empty
                            if tid not in self.cache:
                                self.cache[tid] = {"name": "Error", "pid": None, "hits": 0, "dist": 1.0}

                    # Draw overlay
                    label = self.cache.get(tid, {}).get("name", "Detecting...")
                    confidence = 1.0 - self.cache.get(tid, {}).get("dist", 1.0)  # Convert distance to confidence
                    
                    # Add detection data for UI
                    current_detections.append({
                        'track_id': tid,
                        'name': label,
                        'confidence': max(0.0, confidence),
                        'bbox': (x, y, w, h)
                    })
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                    cv2.putText(frame, f"{label} ", (x, max(0, y-6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 1)

                # FIXED: Count all currently visible known/unknown faces from cache
                known_cnt = 0
                unk_cnt = 0
                for detection in current_detections:
                    name = detection['name']
                    if name != "Detecting..." and name != "Error" and name != "No Face" and name != "Invalid":
                        if name == "Unknown":
                            unk_cnt += 1
                        elif not name.startswith("Maybe:"):
                            known_cnt += 1

                # FPS
                now = time.time()
                dt = now - last
                if dt > 0:
                    self.fps = 1.0 / dt
                last = now

                # push frame
                if self.on_frame:
                    try:
                        self.on_frame(frame.copy())
                    except Exception:
                        pass

                if self.on_stats:
                    try:
                        self.on_stats(self.fps, known_cnt, unk_cnt, len(tracks), current_detections)
                    except Exception:
                        pass

                frame_idx += 1

            except Exception as e:
                logger.error(f"Error in main processing loop: {e}")
                time.sleep(0.1)  # Brief pause before continuing

        cap.release()

    def _log_event(self, kind, track, person_id, name, conf, frame, box):
        x, y, w, h = box
        # Save snapshot for auditing
        day = time.strftime("%Y-%m-%d")
        out_dir = os.path.join(self.snapshot_dir, day)
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{int(time.time()*1000)}_{name}.jpg")
        face = frame[y:y+h, x:x+w]
        cv2.imwrite(path, face)
        # Write to DB
        try:
            add_event(self.con, track.track_id, person_id, name, conf, path, kind)
        except Exception:
            pass
