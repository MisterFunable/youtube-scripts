#!/usr/bin/env python3
"""
YouTube Shorts Finder - Find and export Shorts from your channel
"""

import argparse
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_auth import YouTubeAuth
from shorts.shorts_service import ShortsService

def main():
    parser = argparse.ArgumentParser(description="Find YouTube Shorts from your channel")
    parser.add_argument("--days", type=int, default=1, 
                       help="Number of days back to search (default: 1 for today)")
    parser.add_argument("--all", action="store_true", 
                       help="Get all Shorts (ignore days filter)")
    parser.add_argument("--max", type=int, 
                       help="Maximum number of videos to fetch")
    parser.add_argument("--output", default="videos_today.json", 
                       help="Output JSON file (default: videos_today.json)")
    parser.add_argument("--test", action="store_true", 
                       help="Test API connection only")
    
    args = parser.parse_args()
    
    try:
        # Initialize authentication
        auth = YouTubeAuth(
            client_secret_file="client_secret.json",
            token_file="token.pickle"
        )
        
        if args.test:
            if auth.test_connection():
                print("✅ API connection successful")
            else:
                print("❌ API connection failed")
            return
        
        # Get authenticated service
        youtube = auth.get_authenticated_service()
        shorts_service = ShortsService(youtube)
        
        # Get Shorts based on arguments
        if args.all:
            print("🔍 Fetching all Shorts...")
            shorts = shorts_service.get_all_shorts(max_results=args.max)
        else:
            print(f"🔍 Fetching Shorts from the last {args.days} day(s)...")
            shorts = shorts_service.get_recent_shorts(days_back=args.days, max_results=args.max)
        
        # Export results
        if shorts:
            shorts_service.export_videos_to_json(shorts, args.output)
            print(f"\n📊 Found {len(shorts)} Shorts:")
            for short in shorts:
                duration = f"{short['duration']:.1f}s"
                views = f"{short['viewCount']:,}" if short['viewCount'] > 0 else "0"
                print(f"  • {short['title']} ({duration}, {views} views)")
        else:
            print("📭 No Shorts found matching criteria")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 