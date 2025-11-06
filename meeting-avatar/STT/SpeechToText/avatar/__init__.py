
"""
Main Avatar application integrating speech and text processing capabilities.
"""

import os
from typing import Optional
from .speech_handler import SpeechHandler
from .text_processor import TextProcessor
from . import config, utils

class Avatar:
    def __init__(self):
        """Initialize Avatar with speech and text processing capabilities."""
        self.speech_handler = SpeechHandler()
        self.text_processor = TextProcessor()
        utils.ensure_dir(config.TEMP_DIR)
    
    def listen_and_summarize(self, duration: int = config.RECORD_SECONDS, language: Optional[str] = None) -> Optional[str]:
        """
        Record speech, convert to text, and generate a summary.
        
        Args:
            duration (int): Recording duration in seconds
            
        Returns:
            str: Summarized text or None if failed
        """
        try:
            # Record audio
            audio_file = self.speech_handler.record_audio(duration=duration)
            
            # Convert speech to text
            text = self.speech_handler.speech_to_text(audio_file, language=language)
            if not text:
                return None
            
            # Generate summary
            summary = self.text_processor.summarize_text(text)
            return summary if summary else text
            
        except Exception as e:
            print(f"Error in listen and summarize: {str(e)}")
            return None
    
    def summarize_and_speak(self, text: str) -> bool:
        """
        Summarize text and convert it to speech.
        
        Args:
            text (str): Input text to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate summary
            summary = self.text_processor.summarize_text(text)
            if not summary:
                return False
            
            # Convert summary to speech
            audio_file = self.speech_handler.text_to_speech(summary)
            return bool(audio_file)
            
        except Exception as e:
            print(f"Error in summarize and speak: {str(e)}")
            return False
    
    def process_speech(self, duration: int = config.RECORD_SECONDS, language: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """
        Record speech, convert to text, and return both full text and summary.
        
        Args:
            duration (int): Recording duration in seconds
            
        Returns:
            tuple: (full_text, summary) or (None, None) if failed
        """
        try:
            # Record audio
            audio_file = self.speech_handler.record_audio(duration=duration)
            
            # Convert speech to text
            full_text = self.speech_handler.speech_to_text(audio_file, language=language)
            if not full_text:
                return None, None
            
            # Generate summary
            summary = self.text_processor.summarize_text(full_text)
            return full_text, summary
            
        except Exception as e:
            print(f"Error in process speech: {str(e)}")
            return None, None
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary audio files."""
        try:
            for file in os.listdir(config.TEMP_DIR):
                if file.endswith(('.wav', '.mp3')):
                    os.remove(os.path.join(config.TEMP_DIR, file))
        except Exception as e:
            print(f"Error cleaning up temp files: {str(e)}")

# Example usage
if __name__ == "__main__":
    avatar = Avatar()
    
    print("1. Recording speech for 5 seconds...")
    full_text, summary = avatar.process_speech()
    
    if full_text and summary:
        print("\nFull Text:")
        print(full_text)
        print("\nSummary:")
        print(summary)
        
        print("\n2. Converting summary to speech...")
        avatar.speech_handler.text_to_speech(summary)
    
    avatar.cleanup_temp_files()