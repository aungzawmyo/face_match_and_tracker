import cv2
import time
from db import connect, load_gallery
from pipeline import build_flat_gallery, match_embedding

def quick_test_main_app():
    """Quick test to verify main app improvements"""
    print("Testing main app pipeline improvements...")
    
    # Connect to database
    con = connect()
    gallery = load_gallery(con)
    flat = build_flat_gallery(gallery)
    con.close()
    
    print(f"Loaded gallery: {len(flat)} embeddings")
    for name, pid, emb in flat[:3]:  # Show first 3
        print(f"  {name} (ID:{pid}): {emb.shape}")
    
    # Test with camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    import insightface
    face_app = insightface.app.FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=-1)
    
    print("Testing face recognition with main app settings...")
    print("MATCH_THR = 0.50, UNKNOWN_THR = 0.65")
    
    for i in range(5):
        ret, frame = cap.read()
        if not ret:
            continue
            
        faces = face_app.get(frame)
        if faces:
            e = faces[0].normed_embedding
            
            # Test both methods
            name_old, pid_old, dist_old = match_embedding(e, flat, use_average=False)
            name_new, pid_new, dist_new = match_embedding(e, flat, use_average=True)
            
            print(f"Frame {i+1}:")
            print(f"  Old method: {name_old} (dist: {dist_old:.3f})")
            print(f"  New method: {name_new} (dist: {dist_new:.3f})")
            
            # Apply thresholds
            MATCH_THR = 0.50
            UNKNOWN_THR = 0.65
            
            if dist_new <= MATCH_THR:
                status = "✅ CONFIDENT"
            elif dist_new <= UNKNOWN_THR:
                status = "🤔 MAYBE"
            else:
                status = "❓ UNKNOWN"
            
            print(f"  Result: {status}")
        
        time.sleep(0.5)
    
    cap.release()
    print("Quick test completed!")

if __name__ == "__main__":
    quick_test_main_app()
