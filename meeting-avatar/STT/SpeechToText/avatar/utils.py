"""
Utility functions for the Avatar application.
"""

import os
import time
from typing import Optional

def ensure_dir(directory: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_timestamp() -> str:
    """Generate a timestamp string."""
    return time.strftime("%Y%m%d_%H%M%S")

def get_file_extension(filename: str) -> str:
    """Get the file extension."""
    return os.path.splitext(filename)[1]

def sanitize_filename(filename: str) -> str:
    """Sanitize the filename by removing invalid characters."""
    return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))

def get_temp_filepath(prefix: str, extension: str) -> str:
    """Generate a temporary file path with timestamp."""
    timestamp = generate_timestamp()
    filename = f"{prefix}_{timestamp}{extension}"
    return os.path.join("temp", filename)