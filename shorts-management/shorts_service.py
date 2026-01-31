import os
import json
import datetime
from datetime import timezone, timedelta
from typing import List, Dict, Optional, Tuple
import isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

class ShortsService:
    """Handles YouTube Shorts operations with enhanced features."""
    
    def __init__(self, youtube_service):
        self.youtube = youtube_service
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict:
        """Load video settings from configuration file."""
        settings_file = "video_settings.json"
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "default_title_prefix": "",
            "default_description_prefix": "Gracias por mirar! ✨",
            "default_visibility": "private",
            "audience": "notMadeForKids",
            "license": "youtube",
            "language": "es",
            "enable_languages": ["en", "es", "es-419"],
            "push_to_subscribers": False,
            "tags_template": ["#toys", "#figures", "#unboxing"],
            "fallback_to_gpt": True
        }
    
    def get_uploads_playlist_id(self) -> str:
        """Get the uploads playlist ID for the authenticated channel."""
        try:
            channels_response = self.youtube.channels().list(
                part="contentDetails", mine=True
            ).execute()
            return channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except HttpError as e:
            raise Exception(f"Failed to get uploads playlist: {e}")
    
    def get_shorts_from_playlist(self, playlist_id: str, days_back: Optional[int] = None, 
                                max_results: Optional[int] = None) -> List[Dict]:
        """Get Shorts from playlist with optional date filtering."""
        videos = []
        next_page_token = None
        
        # Calculate cutoff date if filtering by days
        cutoff_date = None
        if days_back:
            cutoff_date = datetime.datetime.now(timezone.utc) - timedelta(days=days_back)
        
        while True:
            # Determine batch size
            batch_size = 50 if max_results is None else min(50, max_results - len(videos))
            if max_results and len(videos) >= max_results:
                break
            
            try:
                pl_request = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=playlist_id,
                    maxResults=batch_size,
                    pageToken=next_page_token
                )
                pl_response = pl_request.execute()
                
                if not pl_response.get("items"):
                    break
                
                # Get video IDs for duration checking
                video_ids = [item["contentDetails"]["videoId"] for item in pl_response["items"] 
                           if "videoId" in item["contentDetails"]]
                
                if not video_ids:
                    break
                
                # Get video details including duration
                vid_response = self.youtube.videos().list(
                    part="contentDetails,statistics", 
                    id=",".join(video_ids)
                ).execute()
                
                # Create duration lookup
                durations = {}
                for v in vid_response["items"]:
                    if "duration" in v["contentDetails"]:
                        durations[v["id"]] = isodate.parse_duration(
                            v["contentDetails"]["duration"]
                        ).total_seconds()
                
                # Process each video
                for item in pl_response["items"]:
                    vid_id = item["contentDetails"].get("videoId")
                    video_published_at = item["contentDetails"].get("videoPublishedAt")
                    
                    if not vid_id or not video_published_at:
                        continue
                    
                    # Check date filter
                    if cutoff_date:
                        published_date = datetime.datetime.fromisoformat(
                            video_published_at.replace("Z", "+00:00")
                        )
                        if published_date < cutoff_date:
                            continue
                    
                    # Check if it's a Short (≤ 60 seconds)
                    duration_seconds = durations.get(vid_id, 0)
                    if duration_seconds > 60:
                        continue
                    
                    # Get statistics
                    stats = next((v.get("statistics", {}) for v in vid_response["items"] 
                                if v["id"] == vid_id), {})
                    
                    videos.append({
                        "videoId": vid_id,
                        "title": item["snippet"]["title"],
                        "publishedAt": video_published_at,
                        "description": item["snippet"].get("description", ""),
                        "duration": duration_seconds,
                        "viewCount": int(stats.get("viewCount", 0)),
                        "likeCount": int(stats.get("likeCount", 0)),
                        "commentCount": int(stats.get("commentCount", 0)),
                        "tags": item["snippet"].get("tags", [])
                    })
                
                next_page_token = pl_response.get("nextPageToken")
                if not next_page_token:
                    break
                    
            except HttpError as e:
                print(f"Error fetching playlist items: {e}")
                break
        
        return videos[:max_results] if max_results else videos
    
    def get_todays_shorts(self, max_results: Optional[int] = None) -> List[Dict]:
        """Get Shorts published today."""
        playlist_id = self.get_uploads_playlist_id()
        return self.get_shorts_from_playlist(playlist_id, days_back=1, max_results=max_results)
    
    def get_recent_shorts(self, days_back: int = 7, max_results: Optional[int] = None) -> List[Dict]:
        """Get Shorts published within the last N days."""
        playlist_id = self.get_uploads_playlist_id()
        return self.get_shorts_from_playlist(playlist_id, days_back=days_back, max_results=max_results)
    
    def get_all_shorts(self, max_results: Optional[int] = None) -> List[Dict]:
        """Get all Shorts from the channel."""
        playlist_id = self.get_uploads_playlist_id()
        return self.get_shorts_from_playlist(playlist_id, max_results=max_results)
    
    def update_video_metadata(self, video_id: str, metadata: Dict) -> bool:
        """Update video metadata (title, description, tags, visibility) and localizations."""
        try:
            # First, get the current video details to preserve existing categoryId
            current_video = self.youtube.videos().list(
                part="snippet,status,localizations",
                id=video_id
            ).execute()
            
            if not current_video.get("items"):
                print(f"❌ Video {video_id} not found")
                return False
            
            current_snippet = current_video["items"][0]["snippet"]
            current_status = current_video["items"][0]["status"]
            current_localizations = current_video["items"][0].get("localizations", {})
            
            # Preserve existing categoryId if video is public, otherwise use default
            category_id = current_snippet.get("categoryId")
            if metadata.get("visibility") == "private" and not category_id:
                category_id = "22"  # People & Blogs - default category for private videos
            
            body = {
                "id": video_id,
                "snippet": {
                    "title": metadata.get("title", ""),
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", [])
                },
                "status": {
                    "privacyStatus": metadata.get("visibility", self.settings["default_visibility"]),
                    "madeForKids": metadata.get("audience", self.settings["audience"]) == "madeForKids"
                }
            }
            
            # Only add categoryId if we have one
            if category_id:
                body["snippet"]["categoryId"] = category_id
            
            # Handle localizations for multiple language versions
            if metadata.get("localizations"):
                # Determine the best default language
                # 1. Try to use the original video's language from settings
                # 2. Fall back to channel's primary language (es) or English
                # 3. Avoid Japanese as default unless content is actually Japanese
                
                # Get the original video's language from settings
                original_lang = self.settings.get("language", "es")
                
                # Check if we have a detected language from the metadata
                detected_lang = metadata.get("detected_language")
                if detected_lang and detected_lang != "unknown":
                    original_lang = detected_lang
                    print(f"🌐 Using detected language '{detected_lang}' as original language")
                
                # Check if the original content is in Japanese
                title = metadata.get("title", "")
                description = metadata.get("description", "")
                content_text = f"{title} {description}"
                
                # Simple Japanese detection (look for Japanese characters)
                japanese_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', content_text)
                is_japanese_content = len(japanese_chars) > 5  # Threshold for Japanese content
                
                if is_japanese_content:
                    # If content is actually Japanese, use Japanese as default
                    default_lang = "ja"
                    print(f"🌐 Content appears to be Japanese, using 'ja' as default")
                else:
                    # Use the channel's primary language or English as default
                    # Avoid Japanese as default for non-Japanese content
                    if original_lang == "ja" and not is_japanese_content:
                        # If settings say Japanese but content isn't Japanese, use English
                        default_lang = "en"
                        print(f"🌐 Settings suggest Japanese but content isn't Japanese, using 'en' as default")
                    else:
                        # Use the original language from settings
                        default_lang = original_lang
                        print(f"🌐 Using original language '{original_lang}' as default")
                
                body["snippet"]["defaultLanguage"] = default_lang
                
                # Merge with existing localizations
                updated_localizations = current_localizations.copy()
                updated_localizations.update(metadata["localizations"])
                body["localizations"] = updated_localizations
                print(f"🌐 Updated localizations: {list(updated_localizations.keys())}")
                print(f"🌐 Default language set to: {default_lang}")
            
            response = self.youtube.videos().update(
                part="snippet,status,localizations" if metadata.get("localizations") else "snippet,status",
                body=body
            ).execute()
            
            print(f"✅ Successfully updated video {video_id}")
            return True
            
        except HttpError as e:
            # Check if it's a quota exceeded error
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                print(f"❌ YouTube API quota exceeded. Stopping processing.")
                raise Exception("YOUTUBE_QUOTA_EXCEEDED") from e
            else:
                print(f"❌ Error updating video {video_id}: {e}")
                return False
    
    def export_videos_to_json(self, videos: List[Dict], filename: str = "videos_today.json") -> None:
        """Export videos to JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        print(f"✅ Exported {len(videos)} videos to {filename}") 