import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class YouTubeAuth:
    """Handles YouTube API authentication and service creation."""
    
    def __init__(self, client_secret_file="client_secret.json", token_file="token.pickle"):
        self.client_secret_file = client_secret_file
        self.token_file = token_file
        self.scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    
    def get_authenticated_service(self):
        """Get authenticated YouTube service."""
        creds = None
        
        # Load existing credentials if available
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)
        
        # Refresh or create new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)
        
        return build("youtube", "v3", credentials=creds)
    
    def test_connection(self):
        """Test the YouTube API connection."""
        try:
            youtube = self.get_authenticated_service()
            channels_response = youtube.channels().list(part="snippet", mine=True).execute()
            channel_name = channels_response["items"][0]["snippet"]["title"]
            print(f"✅ Connected successfully to channel: {channel_name}")
            return True
        except Exception as e:
            print(f"❌ Error testing connection: {e}")
            return False 