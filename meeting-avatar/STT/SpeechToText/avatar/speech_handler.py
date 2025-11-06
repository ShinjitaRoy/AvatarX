"""
Speech handling module for text-to-speech and speech-to-text conversion.
"""

import os
import wave
import pyaudio
import whisper
from gtts import gTTS
from typing import Optional
from . import config
from . import utils
import shutil
import subprocess
import re
import unicodedata

class SpeechHandler:
    def __init__(self):
        """Initialize the speech handler with Whisper model."""
        self.model = whisper.load_model(config.WHISPER_MODEL)
    
    def record_audio(self, duration: int = config.RECORD_SECONDS,
                    filename: str = config.TEMP_AUDIO_FILE) -> str:
        """
        Record audio from microphone for specified duration.
        
        Args:
            duration (int): Recording duration in seconds
            filename (str): Output audio filename
            
        Returns:
            str: Path to the recorded audio file
        """
        p = pyaudio.PyAudio()
        
        stream = p.open(
            format=pyaudio.paInt16,
            channels=config.CHANNELS,
            rate=config.RATE,
            input=True,
            frames_per_buffer=config.CHUNK
        )
        
        print(f"* Recording for {duration} seconds...")
        frames = []
        
        for _ in range(0, int(config.RATE / config.CHUNK * duration)):
            data = stream.read(config.CHUNK)
            frames.append(data)
            
        print("* Done recording")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Save the recorded audio
        filepath = os.path.join(config.TEMP_DIR, filename)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(config.CHANNELS)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(config.RATE)
            wf.writeframes(b''.join(frames))
        
        return filepath
    
    def speech_to_text(self, audio_file: str, language: Optional[str] = None) -> Optional[str]:
        """
        Convert speech to text using Whisper.
        
        Args:
            audio_file (str): Path to the audio file
            
        Returns:
            str: Transcribed text or None if failed
        """
        try:
            # Basic file checks
            if not os.path.exists(audio_file):
                print(f"Error: audio file does not exist: {audio_file}")
                return None

            if not os.access(audio_file, os.R_OK):
                print(f"Warning: audio file is not readable (permission denied): {audio_file}")
                # Try to copy the file into the project's TEMP_DIR and use that copy
                try:
                    utils.ensure_dir(config.TEMP_DIR)
                    dest_name = utils.sanitize_filename(os.path.basename(audio_file))
                    # Ensure unique file name
                    dest_path = os.path.join(config.TEMP_DIR, dest_name)
                    shutil.copy2(audio_file, dest_path)
                    print(f"Copied file to temporary location: {dest_path}")
                    audio_file = dest_path
                except Exception as copy_err:
                    print(f"Failed to copy audio to TEMP_DIR: {copy_err}")
                    return None

            # Check ffmpeg availability (Whisper uses ffmpeg via subprocess)
            if shutil.which("ffmpeg") is None:
                print("ffmpeg not found on PATH. Install ffmpeg and add it to PATH. See https://www.gyan.dev/ffmpeg/builds/")

            # Attempt transcription
            try:
                kwargs = {}
                if language:
                    kwargs["language"] = language

                result = self.model.transcribe(audio_file, **kwargs)
                raw_text = result.get("text", "").strip()
                cleaned = self._clean_transcript(raw_text)
                # If cleaning produced an empty string, return the raw text as fallback
                return cleaned if cleaned else raw_text
            except Exception as transcribe_err:
                # If ffmpeg ran but failed to open the file, try a diagnostic call to ffmpeg
                try:
                    ff_cmd = ["ffmpeg", "-v", "error", "-i", audio_file, "-f", "null", "-"]
                    proc = subprocess.run(ff_cmd, capture_output=True, text=True)
                    if proc.returncode != 0:
                        print("ffmpeg diagnostic output:\n", proc.stderr)
                except FileNotFoundError:
                    # ffmpeg not available — already warned above
                    pass

                print(f"Error in speech to text conversion: {transcribe_err}")
                return None
        except Exception as e:
            print(f"Error in speech to text conversion: {str(e)}")
            return None

    def _clean_transcript(self, text: str) -> str:
        """Normalize and lightly clean the transcript.

        - Normalize unicode to NFKC
        - Remove most control characters
        - Collapse whitespace
        """
        try:
            if not text:
                return ""

            # Normalize unicode
            text = unicodedata.normalize("NFKC", text)

            # Remove control characters (categories starting with C) except common whitespace
            cleaned = []
            for ch in text:
                cat = unicodedata.category(ch)
                if cat.startswith("C") and ch not in ("\n", "\t", "\r"):
                    continue
                cleaned.append(ch)
            text = "".join(cleaned)

            # Collapse whitespace
            text = re.sub(r"\s+", " ", text).strip()

            return text
        except Exception:
            return text
    
    def text_to_speech(self, text: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech using gTTS.
        
        Args:
            text (str): Text to convert to speech
            output_file (str, optional): Output audio file path
            
        Returns:
            str: Path to the generated audio file or None if failed
        """
        try:
            if not output_file:
                output_file = os.path.join(config.TEMP_DIR, "tts_output.mp3")
            
            tts = gTTS(text=text, lang=config.TTS_LANG, slow=config.TTS_SPEED)
            tts.save(output_file)
            return output_file
        except Exception as e:
            print(f"Error in text to speech conversion: {str(e)}")
            return None
        
    def process_audio_file(self, audio_path: str) -> str:
        """Process complete audio file and return transcribed text"""
        # Split audio on silence
        segments = split_on_silence(audio_path)
        
        # Process each segment and combine texts
        full_text = []
        for segment in segments:
            text = process_audio_to_text(segment)
            if text:
                full_text.append(text)
                
        return " ".join(full_text)