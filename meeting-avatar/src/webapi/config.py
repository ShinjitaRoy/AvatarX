import os

HOST = os.getenv("WEBAPI_HOST", "127.0.0.1")
PORT = int(os.getenv("WEBAPI_PORT", "5000"))
DEBUG = os.getenv("WEBAPI_DEBUG", "1") == "1"

# frontend build folder (Vite default = dist)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND_DIST = os.path.join(ROOT, "frontend", "dist")