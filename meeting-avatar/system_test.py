import logging
import cv2
import os
from src.avatar.avatar_renderer import AvatarRenderer
from src.meeting.meeting_controller import MeetingController
from src.avatar.avatar_controller import AvatarController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_avatar_display(duration=5):
    """Test avatar rendering and window creation"""
    logger.info("Testing avatar display...")
    renderer = AvatarRenderer(640, 480)
    
    for i in range(duration * 30):  # Run for duration seconds at ~30 FPS
        frame = renderer.render_frame()
        renderer.display_frame(frame)
        cv2.waitKey(33)  # ~30 FPS
        
        if i == 0:  # Save first frame
            cv2.imwrite("avatar_test.jpg", frame)
            logger.info("Saved avatar test frame to avatar_test.jpg")
    
    renderer.cleanup()
    return os.path.exists("avatar_test.jpg")

def test_zoom_connection():
    """Test Zoom authentication and meeting connection"""
    logger.info("Testing Zoom connection...")
    mc = MeetingController()
    
    # Create a test meeting or use existing one
    meeting_id = "your_test_meeting_id"  # Replace with real test meeting
    password = "your_test_password"      # Replace with real password
    
    try:
        mc._start_meeting(meeting_id, password)
        logger.info("Successfully connected to Zoom")
        return True
    except Exception as e:
        logger.error(f"Zoom connection failed: {e}")
        return False

def run_system_test():
    """Run all system components test"""
    results = {
        "Avatar Display": False,
        "Zoom Connection": False,
        "Virtual Camera": False,
        "Virtual Audio": False
    }
    
    # Test 1: Avatar Display
    try:
        results["Avatar Display"] = test_avatar_display(duration=3)
    except Exception as e:
        logger.error(f"Avatar display test failed: {e}")
    
    # Test 2: Zoom Connection
    try:
        results["Zoom Connection"] = test_zoom_connection()
    except Exception as e:
        logger.error(f"Zoom connection test failed: {e}")
    
    # Print Results
    print("\nSystem Test Results:")
    print("-" * 50)
    for component, status in results.items():
        status_str = "✓ PASS" if status else "✗ FAIL"
        print(f"{component:.<30}{status_str}")
    
    print("\nNext Steps:")
    if not results["Avatar Display"]:
        print("- Check avatar_renderer.py and OBS configuration")
    if not results["Zoom Connection"]:
        print("- Verify Zoom credentials in .env")
        print("- Check network connectivity")
    if not results["Virtual Camera"]:
        print("- Ensure OBS Virtual Camera is running")
    if not results["Virtual Audio"]:
        print("- Check VB-Cable installation")

if __name__ == "__main__":
    run_system_test()