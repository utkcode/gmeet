"""
Google OAuth Authentication Module
Handles authentication with Google APIs for Calendar, Meet, and Drive access
"""

import os
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Scopes required for accessing Google services
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

class GoogleAuthManager:
    """Manages Google OAuth authentication and service initialization"""
    
    def __init__(self):
        self.credentials: Optional[Credentials] = None
        self.calendar_service = None
        self.drive_service = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google APIs using OAuth2 flow
        Returns True if authentication successful, False otherwise
        """
        creds = None
        token_file = 'token.pickle'
        
        # Load existing credentials if available
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no valid credentials, initiate OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                try:
                    # Create OAuth flow
                    flow = InstalledAppFlow.from_client_config(
                        self._get_client_config(), SCOPES
                    )
                    creds = flow.run_local_server(port=8080)
                except Exception as e:
                    print(f"Error during OAuth flow: {e}")
                    return False
            
            # Save credentials for future use
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        return self._initialize_services()
    
    def _get_client_config(self) -> Dict[str, Any]:
        """Get OAuth client configuration from environment variables"""
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8080/callback')
        
        if not client_id or not client_secret:
            raise ValueError(
                "Missing Google OAuth credentials. Please set GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET in your .env file"
            )
        
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }
    
    def _initialize_services(self) -> bool:
        """Initialize Google API services"""
        try:
            self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Error initializing services: {e}")
            return False
    
    def get_calendar_service(self):
        """Get Google Calendar service instance"""
        return self.calendar_service
    
    def get_drive_service(self):
        """Get Google Drive service instance"""
        return self.drive_service
    
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.credentials is not None and self.credentials.valid
