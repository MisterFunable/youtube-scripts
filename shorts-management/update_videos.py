import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Setup ---
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

# Dummy example: Replace or implement your actual translation & metadata updating logic here
def update_video_metadata(video_metadata, lang_code="es"):
    # This is where you'd apply your translations & logic to update title, description, tags, etc.
    # Return updated dict or None if no changes
    # For demo, just appending " (ES)" to title if lang_code is "es"
    if lang_code == "es" and not video_metadata["title"].endswith(" (ES)"):
        updated = video_metadata.copy()
        updated["title"] = video_metadata["title"] + " (ES)"
        return updated
    return None

def update_youtube_video(youtube, video_id, updated_metadata):
    body = {
        "id": video_id,
        "snippet": {
            "title": updated_metadata["title"],
            "description": updated_metadata["description"],
            "tags": updated_metadata.get("tags", [])
        },
        "status": {
            "privacyStatus": updated_metadata.get("visibility", "private")
        }
    }
    response = youtube.videos().update(
        part="snippet,status",
        body=body
    ).execute()
    return response

if __name__ == "__main__":
    youtube = get_authenticated_service()
    with open("videos_today.json", "r", encoding="utf-8") as f:
        videos = json.load(f)

    for video in videos:
        video_metadata = {
            "id": video.get("videoId"),
            "title": video.get("title", ""),
            "description": video.get("description", ""),
            "tags": [],  # Extend if you want to load existing tags
            "visibility": "private"  # default; adjust if you want
        }

        updated = update_video_metadata(video_metadata, lang_code="es")
        if updated:
            print(f"Updating video {video_metadata['id']} with new metadata...")
            resp = update_youtube_video(youtube, video_metadata["id"], updated)
            print("Update response:", resp)
        else:
            print(f"No changes to apply for video {video_metadata['id']}.")
