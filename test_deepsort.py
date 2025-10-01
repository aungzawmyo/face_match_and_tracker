import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort

def test_deepsort_format():
    """Test different formats to see what DeepSORT expects"""
    tracker = DeepSort(max_age=30, n_init=2)
    
    # Create a dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Test different detection formats
    formats_to_try = [
        # Format 1: Simple list of [x, y, w, h, conf]
        [[100, 100, 50, 50, 0.9]],
        
        # Format 2: Tuple of (bbox, conf, class)
        [([100, 100, 50, 50], 0.9, "face")],
        
        # Format 3: Dictionary format
        [{"bbox": [100, 100, 50, 50], "confidence": 0.9, "class": "face"}],
        
        # Format 4: Just bbox
        [[100, 100, 50, 50]],
        
        # Format 5: Nested list
        [[[100, 100, 50, 50], 0.9]],
    ]
    
    for i, fmt in enumerate(formats_to_try):
        print(f"\nTrying format {i+1}: {fmt}")
        try:
            tracks = tracker.update_tracks(fmt, frame=frame)
            print(f"  ✅ SUCCESS: Format {i+1} works!")
            print(f"  Tracks returned: {len(tracks)}")
            break
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    test_deepsort_format()
