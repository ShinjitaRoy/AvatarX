from dotenv import load_dotenv
import os

load_dotenv()

APP_TYPE = os.getenv("ZOOM_APP_TYPE", "server_to_server_oauth").lower()

# OAuth / Server-to-Server credentials
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")

# Legacy / SDK keys (only used if your app requires them)
ZOOM_API_KEY = os.getenv("ZOOM_API_KEY")
ZOOM_API_SECRET = os.getenv("ZOOM_API_SECRET")

def using_s2s_oauth():
    return APP_TYPE == "server_to_server_oauth"

AVATAR_MODEL_PATH = os.getenv("AVATAR_MODEL_PATH", "./models/avatar")
LANGUAGE = os.getenv("LANGUAGE", "en-US")
DB_PATH = os.getenv("DB_PATH", "./data/meetings.db")

class Config:
    ZOOM_API_KEY = ZOOM_API_KEY
    ZOOM_API_SECRET = ZOOM_API_SECRET
    MEETING_ID = os.getenv("MEETING_ID")
    USER_EMAIL = os.getenv("USER_EMAIL")
    AUDIO_OUTPUT_FORMAT = "wav"
    TRANSCRIPTION_LANGUAGE = "en-US"
    DATABASE_URL = os.getenv("DATABASE_URL")