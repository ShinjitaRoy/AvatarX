import time
import logging
from src.audio.audio_manager import AudioManager

logging.basicConfig(level=logging.DEBUG)

def test_continuous_recording():
    am = AudioManager("test_meeting")
    
    print("\nStarting continuous recording - speak into your microphone...")
    print("Recording will continue until you press Ctrl+C")
    
    try:
        am.start_meeting_recording()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping recording and generating summary...")
        am.stop_meeting_recording()
        print("\nCheck the summaries folder for the generated summary")

if __name__ == "__main__":
    test_continuous_recording()