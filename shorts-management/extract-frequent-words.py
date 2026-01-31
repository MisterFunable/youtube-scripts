import os
import pickle
import re
import json
from collections import Counter
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
TOKEN_PICKLE = "token.pickle"
CLIENT_SECRET_FILE = "client_secret.json"

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s#\-]", "", text)
    return text.strip()

def main():
    youtube = get_authenticated_service()

    channel = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads_id = channel["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    video_ids = []
    next_page_token = None
    while True:
        playlist = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        video_ids.extend([item["contentDetails"]["videoId"] for item in playlist["items"]])
        next_page_token = playlist.get("nextPageToken")
        if not next_page_token:
            break

    phrases = Counter()
    stopwords = {"the", "a", "in", "to", "and", "of", "for", "on", "at", "is", "with", "by", "from"}

    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i + 50]
        response = youtube.videos().list(
            part="snippet",
            id=",".join(batch_ids)
        ).execute()
        for item in response["items"]:
            title = clean_text(item["snippet"]["title"])
            desc = clean_text(item["snippet"].get("description", ""))
            combined = f"{title} {desc}"
            words = combined.split()

            # Get single words + 2- and 3-word phrases
            for i in range(len(words)):
                if words[i] not in stopwords:
                    phrases[words[i]] += 1
                if i < len(words) - 1:
                    phrases[f"{words[i]} {words[i+1]}"] += 1
                if i < len(words) - 2:
                    phrases[f"{words[i]} {words[i+1]} {words[i+2]}"] += 1

    most_common = dict(phrases.most_common(100))
    with open("frequent_words.json", "w", encoding="utf-8") as f:
        json.dump(most_common, f, indent=2, ensure_ascii=False)

    print("✅ Extracted common words into frequent_words.json")

if __name__ == "__main__":
    main()
