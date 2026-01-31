import isodate
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

class YouTubeService:
    """Handles YouTube API operations."""
    
    def __init__(self, youtube_service):
        self.youtube = youtube_service
    
    def get_upload_playlist_id(self) -> str:
        """Get the uploads playlist ID for the authenticated channel."""
        channels_response = self.youtube.channels().list(
            part="contentDetails", mine=True
        ).execute()
        return channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    def get_video_ids(self, playlist_id: str, max_results: Optional[int] = None) -> List[str]:
        """Get video IDs from a playlist."""
        video_ids = []
        next_page_token = None
        
        while True:
            # Determine batch size
            batch_size = 50 if max_results is None else min(50, max_results - len(video_ids))
            if max_results and len(video_ids) >= max_results:
                break
            
            playlist_response = self.youtube.playlistItems().list(
                playlistId=playlist_id,
                part="contentDetails",
                maxResults=batch_size,
                pageToken=next_page_token
            ).execute()
            
            batch_ids = [item["contentDetails"]["videoId"] for item in playlist_response.get("items", [])]
            video_ids.extend(batch_ids)
            
            next_page_token = playlist_response.get("nextPageToken")
            if not next_page_token:
                break
        
        return video_ids[:max_results] if max_results else video_ids
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed information for a list of video IDs."""
        all_details = []
        
        # Process in batches of 50 (YouTube API limit)
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i + 50]
            response = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=",".join(batch_ids)
            ).execute()
            
            for item in response["items"]:
                snippet = item["snippet"]
                content_details = item["contentDetails"]
                statistics = item.get("statistics", {})
                
                # Parse duration
                duration_seconds = 0
                if "duration" in content_details:
                    duration_seconds = isodate.parse_duration(content_details["duration"]).total_seconds()
                
                video_detail = {
                    "id": item["id"],
                    "title": snippet["title"],
                    "description": snippet.get("description", ""),
                    "publishedAt": snippet["publishedAt"],
                    "duration_seconds": duration_seconds,
                    "viewCount": int(statistics.get("viewCount", 0)),
                    "likeCount": int(statistics.get("likeCount", 0)),
                    "commentCount": int(statistics.get("commentCount", 0)),
                    "tags": snippet.get("tags", []),
                    "categoryId": snippet.get("categoryId", ""),
                    "defaultLanguage": snippet.get("defaultLanguage", ""),
                    "defaultAudioLanguage": snippet.get("defaultAudioLanguage", "")
                }
                all_details.append(video_detail)
        
        return all_details
    
    def filter_videos_by_date(self, videos: List[Dict], days_back: int) -> List[Dict]:
        """Filter videos published within the last N days."""
        # Use timezone-aware datetime for comparison
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        filtered_videos = []
        
        for video in videos:
            published_date = datetime.fromisoformat(video["publishedAt"].replace("Z", "+00:00"))
            if published_date >= cutoff_date:
                filtered_videos.append(video)
        
        return filtered_videos
    
    def get_recent_videos(self, days_back: int = 7, max_results: Optional[int] = None) -> List[Dict]:
        """Get videos published within the last N days."""
        playlist_id = self.get_upload_playlist_id()
        video_ids = self.get_video_ids(playlist_id, max_results)
        video_details = self.get_video_details(video_ids)
        return self.filter_videos_by_date(video_details, days_back)
    
    def get_all_videos(self, max_results: Optional[int] = None) -> List[Dict]:
        """Get all videos from the channel."""
        playlist_id = self.get_upload_playlist_id()
        video_ids = self.get_video_ids(playlist_id, max_results)
        return self.get_video_details(video_ids) 