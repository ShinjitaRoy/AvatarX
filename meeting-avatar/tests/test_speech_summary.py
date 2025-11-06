import time
import logging
from src.audio.audio_manager import AudioManager

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_speech_to_summary():
    am = AudioManager("test_meeting")
    
    print("\nStarting 30-second recording - speak into your microphone...")
    am.start_recording()
    
    # Record for 30 seconds
    for i in range(30):
        print(f"Recording... {i+1}/30s")
        time.sleep(1)
    
    print("\nStopping recording and generating summary...")
    am.stop_recording()
    
    print("\nCheck the summaries folder for the generated summary")

if __name__ == "__main__":
    test_speech_to_summary()