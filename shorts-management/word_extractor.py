#!/usr/bin/env python3
"""
Word Extractor - Extract frequent words and phrases from video titles and descriptions
"""

import argparse
import json
import re
import sys
import os
from collections import Counter
from typing import List, Dict, Set

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_auth import YouTubeAuth
from youtube_service import YouTubeService

class WordExtractor:
    """Extracts and analyzes frequent words and phrases from video content."""
    
    def __init__(self, youtube_service):
        self.youtube = youtube_service
        self.stopwords = self._load_stopwords()
    
    def _load_stopwords(self) -> Set[str]:
        """Load common stopwords to filter out."""
        return {
            "the", "a", "an", "in", "to", "and", "of", "for", "on", "at", "is", "with", 
            "by", "from", "as", "or", "that", "this", "but", "they", "have", "had", 
            "what", "said", "each", "which", "she", "do", "how", "their", "if", "up", 
            "out", "many", "then", "them", "these", "so", "some", "her", "would", 
            "make", "like", "into", "him", "time", "two", "more", "go", "no", "way", 
            "could", "my", "than", "first", "been", "call", "who", "its", "now", 
            "find", "long", "down", "day", "did", "get", "come", "made", "may", "part"
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep hashtags, hyphens, and spaces
        text = re.sub(r"[^\w\s#\-]", "", text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_phrases(self, text: str, max_phrase_length: int = 3) -> List[str]:
        """Extract words and phrases from text."""
        words = text.split()
        phrases = []
        
        # Extract single words and phrases
        for i in range(len(words)):
            word = words[i]
            
            # Add single word if not a stopword
            if word not in self.stopwords and len(word) > 2:
                phrases.append(word)
            
            # Add phrases of different lengths
            for length in range(2, min(max_phrase_length + 1, len(words) - i + 1)):
                phrase = " ".join(words[i:i + length])
                if len(phrase) > 3:  # Minimum phrase length
                    phrases.append(phrase)
        
        return phrases
    
    def analyze_videos(self, max_videos: Optional[int] = None) -> Dict[str, int]:
        """Analyze videos and extract frequent words/phrases."""
        print("🔍 Fetching videos for analysis...")
        
        # Get all videos
        video_ids = self.youtube.get_video_ids(
            self.youtube.get_upload_playlist_id(), 
            max_results=max_videos
        )
        
        if not video_ids:
            print("❌ No videos found")
            return {}
        
        print(f"📊 Analyzing {len(video_ids)} videos...")
        
        # Get video details
        video_details = self.youtube.get_video_details(video_ids)
        
        # Extract phrases from all videos
        phrase_counter = Counter()
        
        for video in video_details:
            title = self.clean_text(video.get("title", ""))
            description = self.clean_text(video.get("description", ""))
            
            # Combine title and description
            combined_text = f"{title} {description}"
            
            # Extract phrases
            phrases = self.extract_phrases(combined_text)
            phrase_counter.update(phrases)
        
        return dict(phrase_counter.most_common(100))
    
    def export_frequent_words(self, phrases: Dict[str, int], filename: str = "frequent_words.json"):
        """Export frequent words/phrases to JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(phrases, f, indent=2, ensure_ascii=False)
        print(f"✅ Exported {len(phrases)} frequent words/phrases to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Extract frequent words from video content")
    parser.add_argument("--max-videos", type=int, 
                       help="Maximum number of videos to analyze")
    parser.add_argument("--output", default="frequent_words.json", 
                       help="Output JSON file (default: frequent_words.json)")
    parser.add_argument("--phrase-length", type=int, default=3, 
                       help="Maximum phrase length to extract (default: 3)")
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
        youtube_service = YouTubeService(youtube)
        
        # Initialize word extractor
        extractor = WordExtractor(youtube_service)
        
        # Analyze videos
        frequent_words = extractor.analyze_videos(max_videos=args.max_videos)
        
        if frequent_words:
            # Export results
            extractor.export_frequent_words(frequent_words, args.output)
            
            print(f"\n📊 Top 10 most frequent words/phrases:")
            for i, (phrase, count) in enumerate(list(frequent_words.items())[:10], 1):
                print(f"  {i:2d}. {phrase} ({count} times)")
        else:
            print("❌ No words/phrases found")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 