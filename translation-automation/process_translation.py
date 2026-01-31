import os
import json
import time
import sys
import re

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import openai
import isodate

from shared.youtube_auth import YouTubeAuth

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# File management
VIDEO_QUEUE = "video_queue.json"
PROCESSED_QUEUE = "processed.json"

# Supported languages
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "es-419": "Latin American Spanish",
}

DEFAULT_TAGS = ["#toys", "#collection", "#anime", "#unboxing", "dolls", "mechs", "mechas", "#lego", "figma"]

# ------------------ Utility Functions ------------------ #

def strip_surrounding_quotes(text):
    if not text:
        return text
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("“") and text.endswith("”")):
        return text[1:-1].strip()
    return text

def clean_translation_text(text):
    text = text.strip().strip('"').strip("'")
    text = re.sub(r"^['\"“”]+|['\"“”]+$", '', text)
    return text

def is_short_video(video):
    duration_iso = video.get("contentDetails", {}).get("duration")
    if not duration_iso:
        return False
    duration = isodate.parse_duration(duration_iso)
    return duration.total_seconds() <= 60

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

def safe_api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs).execute()
    except HttpError as e:
        if e.resp.status == 403 and "quota" in str(e).lower():
            print("⚠️ Quota exceeded. Try again later.")
            sys.exit(1)
        raise

# ------------------ Translation ------------------ #
def translate_text(text, target_lang, retries=3):
    if not text.strip():
        return text

    system_message = (
        f"You are a professional translator. "
        f"Translate the provided YouTube metadata text into {LANGUAGES.get(target_lang, target_lang)}. "
        f"Do NOT translate any words that are ALL UPPERCASE (brand names or acronyms). "
        f"Preserve formatting, line breaks, emojis, timestamps, links, hashtags, and punctuation exactly as in the input. "
        f"Do NOT add any extra commentary, disclaimers, or summaries."
    )

    user_message = (
        f"Translate the entire following text fully and ONLY the text, nothing else:\n\n"
        f"{text.strip()}"
    )

    for attempt in range(retries):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0,
                max_tokens=3500,  # use high max tokens to avoid cutoff
            )
            translation = response.choices[0].message.content.strip()

            return clean_translation_text(translation)
        except Exception as e:
            print(f"⚠️ Translation API error on attempt {attempt + 1}: {e}")
            time.sleep(2 ** attempt)

    print("⚠️ Translation failed after retries, returning original text.")
    return text

# ------------------ YouTube Data ------------------ #

def get_uploaded_videos(youtube, max_results=1000):
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

def get_video_details(youtube, video_ids, include_shorts=True):
    details = []
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i + 50]
        response = youtube.videos().list(
            part="snippet,status,localizations,contentDetails",
            id=",".join(batch_ids)
        ).execute()
        for video in response.get("items", []):
            if include_shorts or not is_short_video(video):
                details.append(video)
    return details

# ------------------ Metadata Update ------------------ #

def update_video_settings(youtube, video):
    video_id = video["id"]
    snippet = video["snippet"]
    status = video.get("status", {})
    localizations = video.get("localizations", {}) or {}

    changes = []

    snippet["title"] = strip_surrounding_quotes(snippet.get("title", ""))
    snippet["description"] = strip_surrounding_quotes(snippet.get("description", ""))

    for lang, loc in localizations.items():
        loc["title"] = strip_surrounding_quotes(loc.get("title", ""))
        loc["description"] = strip_surrounding_quotes(loc.get("description", ""))

    if "defaultCaptionLanguage" in snippet:
        snippet.pop("defaultCaptionLanguage")
        changes.append("Removed defaultCaptionLanguage")
    if "defaultAudioLanguage" in snippet:
        snippet.pop("defaultAudioLanguage")
        changes.append("Removed defaultAudioLanguage")

    if snippet.get("categoryId") != "22":
        snippet["categoryId"] = "22"
        changes.append("Set category to People & Blogs")
    if status.get("license") != "youtube":
        status["license"] = "youtube"
        changes.append("Set license to YouTube standard")
    if status.get("publishAt"):
        status.pop("publishAt")
        changes.append("Removed scheduled publish date")
    if status.get("madeForKids") is not False:
        status["madeForKids"] = False
        changes.append("Set madeForKids to False")

    # Default tags
    existing_tags = snippet.get("tags", [])
    combined_tags = list(set(existing_tags + DEFAULT_TAGS))

    is_short = is_short_video(video)

    # Add #shorts to tags if it's a short
    if is_short and "#shorts" not in combined_tags:
        combined_tags.append("#shorts")
        changes.append("Added #shorts to tags")

    if set(combined_tags) != set(existing_tags):
        snippet["tags"] = combined_tags
        changes.append("Updated tags")

    # Add #shorts to description if missing
    original_description = snippet.get("description", "")
    if is_short and "#shorts" not in original_description.lower():
        if not original_description.endswith("\n"):
            original_description += "\n"
        original_description += "#shorts"
        changes.append("Added #shorts to description")
    snippet["description"] = original_description

    if snippet.get("defaultLanguage") != "es":
        snippet["defaultLanguage"] = "es"
        changes.append("Set defaultLanguage to 'es'")

    original_title = snippet.get("title", "")

    for lang_code in ["en", "es-419", "es"]:
        translated_desc = translate_text(original_description, lang_code)
        translated_title = translate_text(original_title, lang_code)
        localizations[lang_code] = {
            "title": translated_title,
            "description": translated_desc
        }
        changes.append(f"Updated {lang_code} localization")

    safe_api_call(
        youtube.videos().update,
        part="snippet,status,localizations",
        body={
            "id": video_id,
            "snippet": snippet,
            "status": status,
            "localizations": localizations,
        }
    )

    return {
        "video_id": video_id,
        "title": snippet["title"],
        "changes": changes
    }

# ------------------ Queue Management ------------------ #

def load_video_queue():
    if os.path.exists(VIDEO_QUEUE):
        with open(VIDEO_QUEUE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_video_queue(queue):
    with open(VIDEO_QUEUE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def append_to_processed(video):
    processed = []
    if os.path.exists(PROCESSED_QUEUE):
        with open(PROCESSED_QUEUE, "r", encoding="utf-8") as f:
            processed = json.load(f)
    processed.append(video)
    with open(PROCESSED_QUEUE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)

# ------------------ Main Logic ------------------ #

def main(limit=None, only_shorts=True):
    youtube = get_authenticated_service()

    queue = load_video_queue()
    if not queue:
        print("📥 No queue file found. Fetching new video list.")
        video_ids = get_uploaded_videos(youtube, max_results=limit or 1000)
        videos = get_video_details(youtube, video_ids)
        if only_shorts:
            videos = [v for v in videos if is_short_video(v)]
        queue = [{"id": v["id"]} for v in videos]
        save_video_queue(queue)

    while queue:
        video_entry = queue.pop(0)
        video_id = video_entry["id"]

        print(f"▶️ Processing video ID: {video_id}")
        details = get_video_details(youtube, [video_id])
        if not details:
            print("⚠️ Skipping - video not found.")
            continue

        update_result = update_video_settings(youtube, details[0])
        append_to_processed(update_result)
        save_video_queue(queue)

    print(f"✅ All done! Results saved in {PROCESSED_QUEUE}")

if __name__ == "__main__":
    limit_arg = None
    only_shorts = True  # ✅ Default to only shorts
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.isdigit():
                limit_arg = int(arg)
            elif arg == "--all":
                only_shorts = False
    main(limit=limit_arg, only_shorts=only_shorts)