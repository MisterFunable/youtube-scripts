import os
import json
import sys

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from googleapiclient.errors import HttpError
from shared.youtube_auth import YouTubeAuth

OUTPUT_JSON = "video_backup_and_changes.json"

def safe_api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs).execute()
    except HttpError as e:
        if e.resp.status == 403 and "quota" in str(e).lower():
            print("Quota exceeded. Stopping script. Please try again later.")
            exit(1)
        else:
            raise e

def get_uploaded_videos(youtube, max_results=1000):
    # Get authenticated user's channel uploads playlist ID
    channels_response = safe_api_call(youtube.channels().list, part="contentDetails", mine=True)
    uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    video_ids = []
    nextPageToken = None
    while True:
        playlist_response = safe_api_call(
            youtube.playlistItems().list,
            playlistId=uploads_playlist_id,
            part="contentDetails",
            maxResults=50,
            pageToken=nextPageToken
        )
        video_ids.extend([item["contentDetails"]["videoId"] for item in playlist_response.get("items", [])])
        nextPageToken = playlist_response.get("nextPageToken")
        if not nextPageToken or len(video_ids) >= max_results:
            break

    return video_ids[:max_results]

def get_video_details(youtube, video_ids):
    details = []
    for i in range(0, len(video_ids), 50):  # batch max 50 ids
        batch_ids = video_ids[i:i+50]
        response = safe_api_call(
            youtube.videos().list,
            part="snippet,status",  # not requesting contentDetails to avoid ageGating
            id=",".join(batch_ids)
        )
        details.extend(response.get("items", []))
    return details

def update_video_settings(youtube, video):
    video_id = video["id"]
    snippet = video["snippet"]
    status = video.get("status", {})

    changes_made = []

    # Ensure video is not made for kids
    if status.get("madeForKids") != False:
        status["madeForKids"] = False
        changes_made.append("Set madeForKids to False")

    # Altered content via contentRating removal is not possible because we don't fetch contentDetails,
    # but if you had it, you'd remove contentRating here.
    # Since we don't have it, we can't do that via API.

    body = {
        "id": video_id,
        "snippet": snippet,
        "status": status
    }

    try:
        response = safe_api_call(
            youtube.videos().update,
            part="snippet,status",
            body=body
        )
        if changes_made:
            print(f"Updated video {video_id}: " + ", ".join(changes_made))
        else:
            print(f"No changes needed for video {video_id}.")
        return {
            "videoId": video_id,
            "changes": changes_made,
            "status": "updated"
        }
    except HttpError as e:
        print(f"Failed to update video {video_id}: {e}")
        return {
            "videoId": video_id,
            "changes": changes_made,
            "status": f"failed: {e}"
        }

def main(limit=None):
    youtube = get_authenticated_service()

    max_videos = limit if limit else 1000
    print(f"Fetching last {max_videos} uploaded videos...")
    video_ids = get_uploaded_videos(youtube, max_results=max_videos)

    print(f"Total videos to process: {len(video_ids)}")

    videos = get_video_details(youtube, video_ids)

    output = []
    for video in videos:
        vid = video["id"]
        print(f"Processing video {vid} - Title: {video['snippet'].get('title', 'N/A')}")
        result = update_video_settings(youtube, video)
        # Save full video info + changes for backup
        output.append({
            "video": video,
            "update_result": result
        })

    # Save to JSON file
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Process complete. Results saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    import sys
    arg_limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit=arg_limit)
