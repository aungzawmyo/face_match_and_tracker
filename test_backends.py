import cv2
import numpy as np

def test_camera_backends():
    print("Testing different OpenCV backends...")
    
    # Try different backends
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (cv2.CAP_V4L2, "Video4Linux2"),
        (cv2.CAP_ANY, "Any available")
    ]
    
    for backend_id, backend_name in backends:
        print(f"\nTrying backend: {backend_name}")
        try:
            cap = cv2.VideoCapture(0, backend_id)
            if cap.isOpened():
                print(f"  ✓ Camera opened with {backend_name}")
                
                # Set some properties to help with stability
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                
                # Try to read a frame
                for attempt in range(5):  # Try multiple times
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"  ✓ Frame read successfully on attempt {attempt+1}: {frame.shape}")
                        break
                    else:
                        print(f"  ✗ Frame read failed on attempt {attempt+1}")
                else:
                    print(f"  ✗ Failed to read frame after 5 attempts")
                
                cap.release()
            else:
                print(f"  ✗ Camera could not be opened with {backend_name}")
        except Exception as e:
            print(f"  ✗ Exception with {backend_name}: {e}")

def test_with_working_backend():
    """Test with DirectShow backend which usually works better on Windows"""
    print("\n\nTesting with DirectShow backend specifically...")
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Failed to open camera with DirectShow")
        return False
        
    # Set properties for better compatibility
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to avoid delays
    
    success_count = 0
    for i in range(10):
        ret, frame = cap.read()
        if ret and frame is not None:
            success_count += 1
            if i == 0:  # Print info for first successful frame
                print(f"First frame: shape={frame.shape}, dtype={frame.dtype}")
                print(f"Frame stats: min={frame.min()}, max={frame.max()}")
    
    cap.release()
    print(f"Successfully read {success_count}/10 frames")
    return success_count > 5

if __name__ == "__main__":
    test_camera_backends()
    test_with_working_backend()
