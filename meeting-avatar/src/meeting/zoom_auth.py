import base64
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class ZoomAuth:
    def __init__(self):
        self.client_id = os.getenv("ZOOM_CLIENT_ID")
        self.client_secret = os.getenv("ZOOM_CLIENT_SECRET")
        self.access_token = None
        self.token_expiry = None

    def get_access_token(self):
        if self.access_token and datetime.now() < self.token_expiry:
            return self.access_token

        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_bytes}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(
            "https://zoom.us/oauth/token?grant_type=account_credentials&account_id=" + os.getenv("ZOOM_ACCOUNT_ID"),
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"])
            return self.access_token
            
        raise Exception(f"Failed to get access token: {response.text}")