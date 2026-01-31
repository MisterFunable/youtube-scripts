import json
import os
import sys

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.youtube_auth import YouTubeAuth
from shared.youtube_service import YouTubeService

OUTPUT_FILE = "youtube_videos_backup.json"

def get_channel_id(youtube):
    # Get your own channel ID
    response = youtube.channels().list(mine=True, part="id").execute()
    return response["items"][0]["id"]

def get_all_video_ids(youtube, channel_id):
    video_ids = []
    next_page_token = None
    while True:
        res = youtube.search().list(
            channelId=channel_id,
            part="id",
            order="date",
            maxResults=50,
            pageToken=next_page_token,
            type="video"
        ).execute()
        ids = [item["id"]["videoId"] for item in res["items"]]
        video_ids.extend(ids)
        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break
    return video_ids

def get_video_details(youtube, video_ids):
    all_details = []
    for i in range(0, len(video_ids), 50):  # API limit 50 per request
        batch_ids = video_ids[i:i+50]
        response = youtube.videos().list(
            part="snippet,contentDetails,statistics,status",
            id=",".join(batch_ids),
            maxResults=50
        ).execute()
        all_details.extend(response.get("items", []))
    return all_details

def main():
    youtube = get_authenticated_service()
    channel_id = get_channel_id(youtube)
    print(f"Channel ID: {channel_id}")

    print("Fetching all video IDs...")
    video_ids = get_all_video_ids(youtube, channel_id)
    print(f"Found {len(video_ids)} videos.")

    print("Fetching video details...")
    videos = get_video_details(youtube, video_ids)

    print(f"Saving video details to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

    print("Backup completed successfully!")

if __name__ == "__main__":
    main()
