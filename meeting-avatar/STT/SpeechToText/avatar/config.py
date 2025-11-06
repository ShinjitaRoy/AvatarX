"""
Configuration settings for the Avatar application.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Audio settings
AUDIO_FORMAT = 'wav'
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5
TEMP_AUDIO_FILE = "temp_audio.wav"

# Model settings
WHISPER_MODEL = "base"
SUMMARIZATION_MODEL = "facebook/bart-large-cnn"
SUMMARY_MAX_LENGTH = 130
SUMMARY_MIN_LENGTH = 30

# Speech synthesis settings
TTS_LANG = 'en'
TTS_SPEED = False  # Normal speed

# OpenAI / ChatGPT settings (optional)
USE_CHATGPT = os.getenv("USE_CHATGPT", "false").lower() in ("1", "true", "yes")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(ROOT_DIR, "temp")

# Create temp directory if it doesn't exist
os.makedirs(TEMP_DIR, exist_ok=True)