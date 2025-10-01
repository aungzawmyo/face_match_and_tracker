import cv2
import numpy as np

def test_camera():
    print("Testing camera access...")
    
    # Try different camera indices
    for i in range(3):
        print(f"Trying camera index {i}...")
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera {i} opened successfully")
            
            # Try to read a frame
            ret, frame = cap.read()
            if ret:
                print(f"Frame read successfully: shape={frame.shape}, dtype={frame.dtype}")
                print(f"Frame stats: min={frame.min()}, max={frame.max()}, mean={frame.mean():.2f}")
                
                # Check if frame looks normal
                if frame.shape[0] > 0 and frame.shape[1] > 0:
                    print("Frame appears to be valid")
                else:
                    print("Frame appears to be invalid")
            else:
                print(f"Failed to read frame from camera {i}")
            
            cap.release()
        else:
            print(f"Camera {i} could not be opened")
    
    print("Camera test completed")

if __name__ == "__main__":
    test_camera()
