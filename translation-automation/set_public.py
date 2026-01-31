import os
import json
import sys

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from googleapiclient.errors import HttpError
from shared.youtube_auth import YouTubeAuth

VIDEO_QUEUE = "video_queue.json"

def set_videos_public():
    youtube = get_authenticated_service()
    
    # Load video queue
    with open(VIDEO_QUEUE, "r", encoding="utf-8") as f:
        queue = json.load(f)
    
    for video in queue:
        video_id = video["id"]
        print(f"▶️ Setting video {video_id} to public...")
        
        try:
            # Get current video status
            response = youtube.videos().list(
                part="status",
                id=video_id
            ).execute()
            
            if not response.get("items"):
                print(f"⚠️ Video {video_id} not found")
                continue
            
            # Update to public
            youtube.videos().update(
                part="status",
                body={
                    "id": video_id,
                    "status": {
                        "privacyStatus": "public",
                        "selfDeclaredMadeForKids": False,
                        "madeForKids": False,
                        "notifySubscribers": False
                    }
                }
            ).execute()
            
            print(f"✅ Video {video_id} is now public")
            
        except HttpError as e:
            print(f"⚠️ Error updating video {video_id}: {e}")
            continue

if __name__ == "__main__":
    set_videos_public() 