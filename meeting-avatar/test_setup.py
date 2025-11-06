import cv2
import pyaudio
import wave
import numpy as np
import time

def test_camera():
    print("Testing virtual camera...")
    cap = cv2.VideoCapture(0)  # Try different indices (0, 1, 2) if needed
    if not cap.isOpened():
        print("Could not open camera")
        return False
    
    ret, frame = cap.read()
    if ret:
        print("Successfully captured frame from camera")
        cv2.imwrite("camera_test.jpg", frame)
        print("Saved test frame to camera_test.jpg")
    cap.release()
    return ret

def test_audio():
    print("\nTesting audio devices...")
    p = pyaudio.PyAudio()
    
    print("\nAvailable Audio Devices:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        print(f"Device {i}: {dev['name']}")
        if "CABLE" in dev['name']:
            print(f"  → Found VB-Cable device!")
    
    p.terminate()

if __name__ == "__main__":
    print("Testing Avatar Setup\n")
    camera_ok = test_camera()
    test_audio()
    
    if camera_ok:
        print("\nCamera test passed!")
        print("Next steps:")
        print("1. Check camera_test.jpg - you should see your avatar")
        print("2. Test in Zoom: Settings → Video → select 'OBS Virtual Camera'")
    else:
        print("\nCamera test failed - check OBS Virtual Camera is running")