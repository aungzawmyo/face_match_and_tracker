import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort

def test_empty_detections():
    """Test what happens with empty detections"""
    tracker = DeepSort(max_age=30, n_init=2)
    
    # Create a dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    print("Testing empty detections...")
    try:
        tracks = tracker.update_tracks([], frame=frame)
        print(f"✅ Empty list works! Tracks returned: {len(tracks)}")
    except Exception as e:
        print(f"❌ Empty list failed: {e}")

    print("\nTesting with valid detection first, then empty...")
    try:
        # First update with a detection
        tracks = tracker.update_tracks([([100, 100, 50, 50], 0.9, "face")], frame=frame)
        print(f"✅ First update works! Tracks: {len(tracks)}")
        
        # Then update with empty
        tracks = tracker.update_tracks([], frame=frame)
        print(f"✅ Empty after detection works! Tracks: {len(tracks)}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_empty_detections()
