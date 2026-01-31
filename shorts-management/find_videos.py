import os
import datetime
from datetime import timezone
import isodate
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json

def export_videos_to_json(videos, filename="videos_today.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRETS_FILE = "client_secret.json"
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

def get_uploads_playlist_id(youtube):
    channels_response = youtube.channels().list(part="contentDetails", mine=True).execute()
    return channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_videos_from_playlist(youtube, playlist_id, published_after=None):
    videos = []
    nextPageToken = None
    while True:
        pl_request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPageToken
        )
        pl_response = pl_request.execute()
        video_ids = [item["contentDetails"]["videoId"] for item in pl_response["items"] if "videoId" in item["contentDetails"]]

        if not video_ids:
            break

        vid_response = youtube.videos().list(part="contentDetails", id=",".join(video_ids)).execute()
        durations = {}
        for v in vid_response["items"]:
            durations[v["id"]] = isodate.parse_duration(v["contentDetails"]["duration"]).total_seconds()

        for item in pl_response["items"]:
            vid_id = item["contentDetails"].get("videoId")
            video_published_at = item["contentDetails"].get("videoPublishedAt")
            if not vid_id or not video_published_at:
                continue

            if published_after and video_published_at < published_after:
                continue

            duration_seconds = durations.get(vid_id, 0)
            if duration_seconds > 60:
                continue  # Not a Short

            videos.append({
                "videoId": vid_id,
                "title": item["snippet"]["title"],
                "publishedAt": video_published_at,
                "description": item["snippet"].get("description", ""),
                "duration": duration_seconds,
            })

        nextPageToken = pl_response.get("nextPageToken")
        if not nextPageToken:
            break
    return videos

if __name__ == "__main__":
    youtube = get_authenticated_service()
    uploads_playlist_id = get_uploads_playlist_id(youtube)
    today_utc = datetime.datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    shorts = get_videos_from_playlist(youtube, uploads_playlist_id, published_after=today_utc)
    print(f"Found {len(shorts)} Shorts published today or later:")
    for s in shorts:
        print(f"- {s['title']} ({s['duration']}s)")
