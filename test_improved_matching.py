import cv2
import insightface
import numpy as np
from db import load_gallery, connect
from pipeline import match_embedding

def test_improved_matching():
    """Test improved matching with optimized thresholds"""
    print("Testing improved face matching...")
    
    # Load face recognition model
    face_app = insightface.app.FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=-1)  # CPU
    
    # Load gallery
    con = connect()
    gallery = load_gallery(con)
    flat_gallery = []
    for name, (pid, embeddings) in gallery.items():  # Fixed: gallery format is name -> (pid, [vecs])
        for i, emb in enumerate(embeddings):
            flat_gallery.append((name, pid, emb))
    
    print(f"Gallery loaded: {len(flat_gallery)} total embeddings")
    con.close()
    
    # Test with camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    print("Testing for 30 frames... Press 'q' to quit early")
    
    # New thresholds
    MATCH_THR = 0.50
    UNKNOWN_THR = 0.65
    
    results = {"confident": 0, "maybe": 0, "unknown": 0, "total": 0}
    
    for frame_num in range(30):
        ret, frame = cap.read()
        if not ret:
            break
            
        # Detect faces
        faces = face_app.get(frame)
        
        for face in faces:
            results["total"] += 1
            
            # Extract embedding
            embedding = face.embedding
            
            # Test both matching methods
            print(f"\nFrame {frame_num + 1}, Face {results['total']}:")
            
            # Original method
            name_orig, pid_orig, dist_orig = match_embedding(embedding, flat_gallery, use_average=False)
            
            # Improved method (averaging)
            name_avg, pid_avg, dist_avg = match_embedding(embedding, flat_gallery, use_average=True)
            
            print(f"  Original: {name_orig} (distance: {dist_orig:.3f})")
            print(f"  Averaged: {name_avg} (distance: {dist_avg:.3f})")
            
            # Categorize result (using averaged result)
            if dist_avg <= MATCH_THR:
                category = "confident"
                status = "✅"
                results["confident"] += 1
            elif dist_avg <= UNKNOWN_THR:
                category = "maybe"
                status = "🤔"
                results["maybe"] += 1
            else:
                category = "unknown"
                status = "❓"
                results["unknown"] += 1
            
            print(f"  Result: {status} {category.upper()} - {name_avg}")
        
        # Show frame with detection
        cv2.imshow('Improved Matching Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"Total faces tested: {results['total']}")
    print(f"Confident matches: {results['confident']} ({results['confident']/max(1,results['total'])*100:.1f}%)")
    print(f"Maybe matches: {results['maybe']} ({results['maybe']/max(1,results['total'])*100:.1f}%)")
    print(f"Unknown: {results['unknown']} ({results['unknown']/max(1,results['total'])*100:.1f}%)")
    
    total_recognized = results['confident'] + results['maybe']
    if results['total'] > 0:
        print(f"Overall recognition rate: {total_recognized/results['total']*100:.1f}%")

if __name__ == "__main__":
    test_improved_matching()
