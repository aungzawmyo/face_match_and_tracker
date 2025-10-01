import cv2
import numpy as np
import insightface
from db import init_db, load_gallery
from pipeline import cosine_dist, match_embedding, build_flat_gallery

def test_face_matching():
    """Test face matching with current thresholds"""
    print("Testing face matching system...")
    
    # Initialize
    con = init_db()
    gallery = load_gallery(con)
    flat = build_flat_gallery(gallery)
    
    print(f"Gallery loaded: {len(gallery)} people")
    for name, (pid, vecs) in gallery.items():
        print(f"  {name}: {len(vecs)} embeddings")
    
    if not gallery:
        print("❌ No people enrolled! Please enroll someone first.")
        return
    
    # Initialize face detection
    face_app = insightface.app.FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=-1)
    
    # Test with live camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return
    
    print("\n🎥 Testing with live camera...")
    print("Press 'q' to quit, 's' to test current frame")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Detect faces
        faces = face_app.get(frame)
        
        for i, face in enumerate(faces):
            x1, y1, x2, y2 = map(int, face.bbox)
            embedding = face.normed_embedding
            
            # Test matching
            name, pid, dist = match_embedding(embedding, flat) if flat else ("Unknown", None, 1.0)
            
            # Determine classification
            if dist < 0.45:
                label = f"✅ {name}"
                color = (0, 255, 0)  # Green
            elif dist > 0.55:
                label = "❓ Unknown"
                color = (0, 0, 255)  # Red
            else:
                label = f"🤔 Maybe:{name}"
                color = (0, 255, 255)  # Yellow
            
            # Draw
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{label} (d={dist:.3f})", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Print details
            print(f"Face {i+1}: {name} (distance: {dist:.3f}) - {label}")
        
        cv2.imshow("Face Matching Test", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            print(f"\n--- Frame {frame_count} Analysis ---")
            if not faces:
                print("No faces detected in this frame")
            
        frame_count += 1
    
    cap.release()
    cv2.destroyAllWindows()

def test_thresholds():
    """Test different threshold values"""
    print("\n🔧 Testing different threshold values...")
    
    con = init_db()
    gallery = load_gallery(con)
    flat = build_flat_gallery(gallery)
    
    if not gallery:
        print("❌ No people enrolled!")
        return
    
    # Get a sample embedding from enrolled person
    sample_name = list(gallery.keys())[0]
    sample_embedding = gallery[sample_name][1][0]  # First embedding
    
    print(f"Testing with sample from '{sample_name}':")
    
    # Test self-similarity
    self_dist = cosine_dist(sample_embedding, sample_embedding)
    print(f"  Self-similarity: {self_dist:.4f} (should be ~0.0)")
    
    # Test against all embeddings
    distances = []
    for name, (pid, vecs) in gallery.items():
        for vec in vecs:
            dist = cosine_dist(sample_embedding, vec)
            distances.append((name, dist))
    
    # Sort by distance
    distances.sort(key=lambda x: x[1])
    
    print(f"  Distance to all embeddings:")
    for name, dist in distances[:10]:  # Show top 10
        print(f"    {name}: {dist:.4f}")
    
    # Recommend thresholds
    if len(distances) > 1:
        min_dist = distances[0][1]
        max_same_person = max([d for n, d in distances if n == sample_name])
        print(f"\n💡 Threshold recommendations:")
        print(f"   Min distance: {min_dist:.4f}")
        print(f"   Max same-person distance: {max_same_person:.4f}")
        print(f"   Suggested MATCH_THR: {max_same_person + 0.05:.3f}")

if __name__ == "__main__":
    test_thresholds()
    test_face_matching()
