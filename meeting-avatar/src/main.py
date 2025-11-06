import logging
from src.config import settings
from src.meeting.meeting_controller import MeetingController
from src.avatar.avatar_controller import AvatarController
from src.audio.audio_capture import AudioCapture
from src.audio.speech_to_text import SpeechToText
from src.utils.summarizer import Summarizer
from src.ui.meeting_window import MeetingWindow

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the UI window
    window = MeetingWindow()
    window.run()

if __name__ == "__main__":
    main()