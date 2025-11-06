from src.audio.audio_manager import AudioManager
import time

def test_recording():
    audio_mgr = AudioManager("test_meeting")
    print("Starting recording...")
    audio_mgr.start_recording()
    
    # Record for 30 seconds
    time.sleep(30)
    
    print("Stopping recording...")
    audio_mgr.stop_recording()
    
    print("Check summaries folder for the meeting summary")

if __name__ == "__main__":
    test_recording()