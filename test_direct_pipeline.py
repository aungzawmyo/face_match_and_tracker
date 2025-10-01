import cv2
import insightface
from db import connect, load_gallery
from pipeline import build_flat_gallery, match_embedding

def test_direct_pipeline():
    """Test the pipeline directly without GUI"""
    print("Testing direct pipeline...")
    
    # Load gallery
    con = connect()
    gallery = load_gallery(con)
    flat = build_flat_gallery(gallery)
    con.close()
    
    print(f"Gallery loaded: {len(flat)} embeddings")
    
    # Load face detection
    face_app = insightface.app.FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=-1)
    
    # Test with camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    print("Testing pipeline with live camera...")
    
    for i in range(10):
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Get all faces in frame
        faces = face_app.get(frame)
        print(f"Frame {i+1}: {len(faces)} faces detected")
        
        for j, face in enumerate(faces):
            # Test recognition
            e = face.normed_embedding
            name, pid, dist = match_embedding(e, flat, use_average=True) if flat else ("Unknown", None, 1.0)
            
            # Apply thresholds
            if dist < 0.50:
                status = "CONFIDENT"
            elif dist < 0.65:
                status = "MAYBE"
            else:
                status = "UNKNOWN"
            
            print(f"  Face {j+1}: {name} (dist: {dist:.3f}) -> {status}")
        
        if faces:
            break  # Exit after first successful detection
    
    cap.release()
    print("Pipeline test completed!")

if __name__ == "__main__":
    test_direct_pipeline()
