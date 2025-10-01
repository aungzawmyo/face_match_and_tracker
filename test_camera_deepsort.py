import cv2
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort

def test_camera_with_deepsort():
    """Test camera + DeepSORT without InsightFace"""
    print("Testing camera with DeepSORT...")
    
    # Open camera with DirectShow
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Failed to open camera")
        return
    
    print("Camera opened successfully")
    
    # Initialize tracker
    tracker = DeepSort(max_age=30, n_init=2)
    print("DeepSORT initialized")
    
    frame_count = 0
    try:
        while frame_count < 10:  # Test for 10 frames
            ret, frame = cap.read()
            if not ret:
                print(f"Failed to read frame {frame_count}")
                continue
            
            print(f"Frame {frame_count}: {frame.shape}")
            
            # Test with empty detections
            tracks = tracker.update_tracks([], frame=frame)
            print(f"  Empty detections: {len(tracks)} tracks")
            
            # Test with fake detection
            fake_det = [([100, 100, 50, 50], 0.9, "face")]
            tracks = tracker.update_tracks(fake_det, frame=frame)
            print(f"  Fake detection: {len(tracks)} tracks")
            
            frame_count += 1
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cap.release()
        print("Test completed")

if __name__ == "__main__":
    test_camera_with_deepsort()
