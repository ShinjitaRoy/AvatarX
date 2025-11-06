from src.meeting.meeting_controller import MeetingController
from src.avatar.avatar_controller import AvatarController
import time
import logging

logging.basicConfig(level=logging.INFO)

def test_meeting():
    mc = MeetingController()
    avatar = AvatarController()
    
    # Add your actual Zoom meeting details
    meeting_id = "6744941574"  # Replace with your actual meeting ID
    password = "j2Xkf3"   # Replace with your actual meeting password
    
    print("Starting avatar...")
    avatar.activate()
    
    print("Joining test meeting...")
    try:
        mc._start_meeting(meeting_id, password)
        print("Successfully joined meeting")
        
        print("Waiting until host ends meeting or you are removed (no auto-leave)...")
        # block until the meeting ends or the client is removed
        try:
            mc.zoom.wait_until_left()  # blocks indefinitely until detected
            print("Meeting ended / kicked by host detected.")
        except Exception as e:
            print(f"Error while waiting for meeting end: {e}")
    except Exception as e:
        print(f"Error during meeting: {e}")
    finally:
        avatar.deactivate()
        print("Test complete")

if __name__ == "__main__":
    test_meeting()