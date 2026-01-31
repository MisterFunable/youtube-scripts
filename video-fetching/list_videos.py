#!/usr/bin/env python3
"""
Optimized YouTube video listing script with date filtering capabilities.
Supports both recent videos (last N days) and full channel listing.
"""

import json
import argparse
import os
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.youtube_auth import YouTubeAuth
from shared.youtube_service import YouTubeService
from shared.config import *

def save_videos_to_file(videos: list, output_file: str, backup: bool = True):
    """Save videos to JSON file with optional backup."""
    # Create backup directory if it doesn't exist
    if backup and not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Create backup of existing file
    if backup and os.path.exists(output_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"video_list_backup_{timestamp}.json")
        os.rename(output_file, backup_file)
        print(f"📦 Created backup: {backup_file}")
    
    # Save new data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(videos)} videos to {output_file}")

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def print_summary(videos: list):
    """Print a summary of the fetched videos."""
    if not videos:
        print("📭 No videos found matching the criteria.")
        return
    
    total_duration = sum(video["duration_seconds"] for video in videos)
    total_views = sum(video["viewCount"] for video in videos)
    total_likes = sum(video["likeCount"] for video in videos)
    
    print(f"\n📊 Summary:")
    print(f"   • Total videos: {len(videos)}")
    print(f"   • Total duration: {format_duration(total_duration)}")
    print(f"   • Total views: {total_views:,}")
    print(f"   • Total likes: {total_likes:,}")
    
    # Show date range
    dates = [video["publishedAt"] for video in videos]
    if dates:
        earliest = min(dates)
        latest = max(dates)
        print(f"   • Date range: {earliest[:10]} to {latest[:10]}")

def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube videos with date filtering")
    parser.add_argument(
        "--days", "-d", 
        type=int, 
        default=DEFAULT_DAYS_BACK,
        help=f"Number of days back to fetch (default: {DEFAULT_DAYS_BACK})"
    )
    parser.add_argument(
        "--all", "-a", 
        action="store_true",
        help="Fetch all videos (ignores --days parameter)"
    )
    parser.add_argument(
        "--max", "-m", 
        type=int, 
        default=DEFAULT_MAX_VIDEOS,
        help="Maximum number of videos to fetch (default: no limit)"
    )
    parser.add_argument(
        "--output", "-o", 
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output file name (default: {DEFAULT_OUTPUT_FILE})"
    )
    parser.add_argument(
        "--no-backup", 
        action="store_true",
        help="Don't create backup of existing output file"
    )
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Test API connection only"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.days < 1 or args.days > MAX_DAYS_BACK:
        print(f"❌ Days must be between 1 and {MAX_DAYS_BACK}")
        return
    
    if args.max is not None and args.max < 1:
        print("❌ Max videos must be at least 1")
        return
    
    # Initialize authentication
    print("🔐 Initializing YouTube authentication...")
    auth = YouTubeAuth(CLIENT_SECRET_FILE, TOKEN_FILE)
    
    if args.test:
        auth.test_connection()
        return
    
    # Get YouTube service
    youtube_service = auth.get_authenticated_service()
    service = YouTubeService(youtube_service)
    
    # Fetch videos based on parameters
    if args.all:
        print(f"📺 Fetching all videos (max: {args.max or 'unlimited'})...")
        videos = service.get_all_videos(args.max)
    else:
        print(f"📺 Fetching videos from the last {args.days} days (max: {args.max or 'unlimited'})...")
        videos = service.get_recent_videos(args.days, args.max)
    
    # Print summary
    print_summary(videos)
    
    # Save to file
    if videos:
        save_videos_to_file(videos, args.output, not args.no_backup)

if __name__ == "__main__":
    main() 