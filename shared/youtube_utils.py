#!/usr/bin/env python3
"""
Utility functions for YouTube video management.
"""

import json
import os
from datetime import datetime
from typing import List, Dict

def load_video_list(filename: str = "video_list.json") -> List[Dict]:
    """Load video list from JSON file."""
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found")
        return []
    
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def find_videos_by_title(videos: List[Dict], search_term: str, case_sensitive: bool = False) -> List[Dict]:
    """Find videos by title search term."""
    results = []
    search_term = search_term if case_sensitive else search_term.lower()
    
    for video in videos:
        title = video["title"] if case_sensitive else video["title"].lower()
        if search_term in title:
            results.append(video)
    
    return results

def get_videos_by_date_range(videos: List[Dict], start_date: str, end_date: str) -> List[Dict]:
    """Get videos published within a date range (YYYY-MM-DD format)."""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    filtered_videos = []
    for video in videos:
        published_date = datetime.fromisoformat(video["publishedAt"][:10])
        if start <= published_date <= end:
            filtered_videos.append(video)
    
    return filtered_videos

def get_top_videos(videos: List[Dict], metric: str = "viewCount", limit: int = 10) -> List[Dict]:
    """Get top videos by specified metric."""
    valid_metrics = ["viewCount", "likeCount", "commentCount", "duration_seconds"]
    if metric not in valid_metrics:
        print(f"❌ Invalid metric. Choose from: {valid_metrics}")
        return []
    
    sorted_videos = sorted(videos, key=lambda x: x[metric], reverse=True)
    return sorted_videos[:limit]

def export_videos_to_csv(videos: List[Dict], filename: str = "videos.csv"):
    """Export videos to CSV format."""
    import csv
    
    if not videos:
        print("❌ No videos to export")
        return
    
    fieldnames = videos[0].keys()
    
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(videos)
    
    print(f"✅ Exported {len(videos)} videos to {filename}")

def print_video_info(video: Dict):
    """Print formatted video information."""
    print(f"📺 {video['title']}")
    print(f"   ID: {video['id']}")
    print(f"   Published: {video['publishedAt'][:10]}")
    print(f"   Duration: {video['duration_seconds']}s")
    print(f"   Views: {video['viewCount']:,}")
    print(f"   Likes: {video['likeCount']:,}")
    print(f"   Comments: {video['commentCount']:,}")
    print()

def main():
    """Example usage of utility functions."""
    videos = load_video_list()
    
    if not videos:
        print("No videos loaded. Run list_videos_optimized.py first.")
        return
    
    print(f"📊 Loaded {len(videos)} videos")
    
    # Example: Find videos with "tutorial" in title
    tutorial_videos = find_videos_by_title(videos, "tutorial")
    print(f"🎓 Found {len(tutorial_videos)} tutorial videos")
    
    # Example: Get top 5 videos by views
    top_videos = get_top_videos(videos, "viewCount", 5)
    print(f"🏆 Top 5 videos by views:")
    for video in top_videos:
        print_video_info(video)

if __name__ == "__main__":
    main() 