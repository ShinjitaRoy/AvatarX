import sqlite3
import os
import hashlib
import logging
from datetime import datetime

log = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    """Create users and meetings tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Meetings table with foreign key to users
    c.execute('''CREATE TABLE IF NOT EXISTS meetings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  meeting_id TEXT NOT NULL,
                  password TEXT,
                  start_time TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class User:
    @staticmethod
    def register(name: str, email: str, password: str) -> bool:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            hashed = hash_password(password)
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                     (name, email, hashed))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            log.warning(f"User with email {email} already exists")
            return False
        except Exception as e:
            log.error(f"Error registering user: {e}")
            return False

    @staticmethod
    def login(email: str, password: str) -> dict:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            hashed = hash_password(password)
            c.execute("SELECT id, name, email FROM users WHERE email=? AND password=?",
                     (email, hashed))
            user = c.fetchone()
            conn.close()
            if user:
                return {"id": user[0], "name": user[1], "email": user[2]}
            return None
        except Exception as e:
            log.error(f"Error logging in: {e}")
            return None

    @staticmethod
    def get_meetings(user_id: int) -> list:
        """Get all meetings for a user"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                SELECT meeting_id, password, start_time, created_at 
                FROM meetings 
                WHERE user_id=? 
                ORDER BY start_time DESC""", (user_id,))
            meetings = [{
                "meeting_id": row[0],
                "password": row[1],
                "start_time": row[2],
                "created_at": row[3]
            } for row in c.fetchall()]
            conn.close()
            return meetings
        except Exception as e:
            log.error(f"Error getting meetings: {e}")
            return []

    @staticmethod
    def add_meeting(user_id: int, meeting_id: str, password: str, start_time: str) -> bool:
        """Add a meeting for a user"""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO meetings (user_id, meeting_id, password, start_time)
                VALUES (?, ?, ?, ?)""", (user_id, meeting_id, password, start_time))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log.error(f"Error adding meeting: {e}")
            return False