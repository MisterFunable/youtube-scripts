#!/usr/bin/env python3
"""
YouTube Shorts Updater - Update metadata for Shorts videos
Version: 2.2.0
"""

import argparse
import json
import sys
import os
import re
from typing import Dict, Optional, List
from datetime import datetime
import openai

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_auth import YouTubeAuth
from shorts.shorts_service import ShortsService
from shorts.translation_service import TranslationService

# File management constants
VIDEO_QUEUE = "video_queue.json"
PROCESSED_QUEUE = "processed.json"
CUSTOM_TRANSLATIONS_FILE = "custom_translations.json"
VERSION = "2.2.0"

openai.api_key = os.getenv("OPENAI_API_KEY")

def format_title_case(text: str) -> str:
    """
    Format text in proper title case for YouTube titles.
    Capitalizes first letter of each word, preserves acronyms and brand names.
    """
    if not text:
        return text
    
    # List of words to keep lowercase unless first word
    lowercase_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'is', 'it', 'of', 'on', 'or', 'the', 'to', 'up', 'vs', 'vs.'}
    words = text.split()
    result = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in lowercase_words:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    return ' '.join(result)

def detect_language(text: str) -> str:
    """
    Detect if text is in Spanish, English, or Japanese.
    Returns 'es' for Spanish, 'en' for English, 'ja' for Japanese, 'unknown' for unclear.
    """
    if not text or not text.strip():
        return "unknown"
    
    text_lower = text.lower()
    
    # Japanese detection - look for Hiragana, Katakana, and Kanji characters
    japanese_patterns = [
        r'[\u3040-\u309F]',  # Hiragana
        r'[\u30A0-\u30FF]',  # Katakana
        r'[\u4E00-\u9FAF]',  # Kanji
        r'[\uFF66-\uFF9F]',  # Half-width Katakana
    ]
    
    japanese_count = 0
    for pattern in japanese_patterns:
        japanese_count += len(re.findall(pattern, text))
    
    # If significant Japanese characters are found, it's Japanese
    if japanese_count > 3:  # Threshold to avoid false positives
        return "ja"
    
    # Common Spanish words and patterns
    spanish_indicators = [
        'el', 'la', 'los', 'las', 'de', 'del', 'que', 'y', 'a', 'en', 'un', 'una', 'es', 'se', 'no', 'te', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'me', 'hasta', 'hay', 'donde', 'han', 'quien', 'están', 'estado', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mi', 'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras'
    ]
    
    # Common English words and patterns
    english_indicators = [
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
    ]
    
    # Count Spanish and English indicators
    spanish_count = sum(1 for word in spanish_indicators if re.search(r'\b' + re.escape(word) + r'\b', text_lower))
    english_count = sum(1 for word in english_indicators if re.search(r'\b' + re.escape(word) + r'\b', text_lower))
    
    # Spanish-specific patterns
    spanish_patterns = [
        r'\b(gracias|por|mirar|video|vídeo|unboxing|desempaquetado|review|reseña|juguete|figura|muñeca|colección|mecha|robot|anime|manga|lego|construcción|armado|montaje|piezas|partes|caja|empaque|empaquetado|nuevo|nueva|nuevos|nuevas|bonito|bonita|hermoso|hermosa|increíble|fantástico|fantástica|genial|excelente|perfecto|perfecta|mejor|peor|grande|pequeño|pequeña|alto|alta|bajo|baja|color|colores|rojo|roja|azul|verde|amarillo|amarilla|negro|negra|blanco|blanca|rosa|morado|morada|naranja|gris|marrón|dorado|dorada|plateado|plateada)\b',
        r'\b(este|esta|estos|estas|ese|esa|esos|esas|aquel|aquella|aquellos|aquellas)\b',
        r'\b(yo|tú|él|ella|nosotros|nosotras|vosotros|vosotras|ellos|ellas)\b',
        r'\b(soy|eres|es|somos|sois|son|estoy|estás|está|estamos|estáis|están)\b',
        r'\b(tengo|tienes|tiene|tenemos|tenéis|tienen|tuve|tuviste|tuvo|tuvimos|tuvisteis|tuvieron)\b',
        r'\b(hago|haces|hace|hacemos|hacéis|hacen|hice|hiciste|hizo|hicimos|hicisteis|hicieron)\b'
    ]
    
    # English-specific patterns
    english_patterns = [
        r'\b(thanks|for|watching|video|unboxing|review|toy|figure|doll|collection|mecha|robot|anime|manga|lego|construction|build|assembly|pieces|parts|box|packaging|new|beautiful|amazing|fantastic|great|excellent|perfect|better|worse|big|small|tall|short|color|colors|red|blue|green|yellow|black|white|pink|purple|orange|gray|brown|gold|silver)\b',
        r'\b(this|that|these|those)\b',
        r'\b(i|you|he|she|we|they|it)\b',
        r'\b(am|is|are|was|were|be|been|being)\b',
        r'\b(have|has|had|do|does|did|will|would|could|should|can|may|might)\b',
        r'\b(make|makes|made|go|goes|went|gone|get|gets|got|gotten)\b'
    ]
    
    # Count pattern matches
    for pattern in spanish_patterns:
        spanish_count += len(re.findall(pattern, text_lower))
    
    for pattern in english_patterns:
        english_count += len(re.findall(pattern, text_lower))
    
    # Determine language based on counts
    if spanish_count > english_count and spanish_count > 0:
        return "es"
    elif english_count > spanish_count and english_count > 0:
        return "en"
    else:
        return "unknown"

def get_target_language(current_lang: str, settings: Dict) -> str:
    """
    Get the target language for translation based on current language and settings.
    If current is Spanish, translate to English. If current is English, translate to Spanish.
    If current is Japanese, translate to English (or Spanish if English not available).
    """
    enable_languages = settings.get("enable_languages", ["en", "es", "es-419", "ja"])
    
    if current_lang == "es":
        # Spanish → English (preferred) or Japanese
        if "en" in enable_languages:
            return "en"
        elif "ja" in enable_languages:
            return "ja"
        else:
            return "es"  # Fallback to Spanish if no other options
    elif current_lang == "en":
        # English → Spanish (preferred) or Japanese
        if "es" in enable_languages:
            return "es"
        elif "ja" in enable_languages:
            return "ja"
        else:
            return "en"  # Fallback to English if no other options
    elif current_lang == "ja":
        # Japanese → English (preferred) or Spanish
        if "en" in enable_languages:
            return "en"
        elif "es" in enable_languages:
            return "es"
        else:
            return "ja"  # Fallback to Japanese if no other options
    else:
        # Unknown language → default to Spanish
        if "es" in enable_languages:
            return "es"
        elif "en" in enable_languages:
            return "en"
        elif "ja" in enable_languages:
            return "ja"
        else:
            return "es"  # Ultimate fallback

def load_custom_translations() -> Dict:
    """Load custom translations from JSON file."""
    if os.path.exists(CUSTOM_TRANSLATIONS_FILE):
        with open(CUSTOM_TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_custom_translations(translations: Dict) -> None:
    """Save custom translations to JSON file."""
    with open(CUSTOM_TRANSLATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(translations, f, indent=2, ensure_ascii=False)

def get_basic_translations_for_language(target_lang: str) -> Dict:
    """Get basic translations for a specific language."""
    # Only provide basic translations for languages that don't exist in custom_translations.json
    # Since your custom_translations.json already has all languages, return empty dict
    return {}

def add_missing_language_to_translations(translations: Dict, target_lang: str, 
                                       settings: Dict, dry_run: bool = True) -> tuple[Dict, int]:
    """
    Add missing language to translations by creating basic translations
    for common terms that are likely to be used.
    Returns (updated_translations, added_terms_count)
    """
    updated_translations = translations.copy()
    added_terms = 0
    
    basic_translations = get_basic_translations_for_language(target_lang)
    
    if basic_translations:
        print(f"🔧 Adding missing language '{target_lang}' to translations...")
        
        for category, terms in basic_translations.items():
            if category not in updated_translations:
                updated_translations[category] = {}
            
            for term, translation in terms.items():
                if term not in updated_translations[category]:
                    updated_translations[category][term] = {}
                
                if target_lang not in updated_translations[category][term]:
                    updated_translations[category][term][target_lang] = translation
                    added_terms += 1
                    if not dry_run:
                        print(f"  ➕ Added '{term}' → '{translation}' ({target_lang})")
        
        if not dry_run:
            save_custom_translations(updated_translations)
            print(f"✅ Added {added_terms} translations for '{target_lang}'")
        else:
            print(f"🎯 Would add {added_terms} translations for '{target_lang}' (dry run)")
    else:
        print(f"⚠️ No basic translations available for language '{target_lang}'")
    
    return updated_translations, added_terms

def count_translations_for_enabled_languages(translations: Dict, settings: Dict) -> int:
    """Count total translations available for enabled languages."""
    enable_languages = settings.get("enable_languages", ["en", "es", "es-419", "ja"])
    total_translations = 0
    language_counts = {lang: 0 for lang in enable_languages}
    
    if translations:
        print(f"🔍 Translation Summary:")
        print(f"  📁 Categories: {len(translations)}")
        
        for category, terms in translations.items():
            category_total = 0
            for term, lang_dict in terms.items():
                for lang in enable_languages:
                    if lang in lang_dict:
                        total_translations += 1
                        language_counts[lang] += 1
                        category_total += 1
            
            if category_total > 0:
                print(f"  📂 {category}: {category_total} translations")
        
        print(f"  🌐 Language breakdown:")
        for lang, count in language_counts.items():
            print(f"    {lang}: {count} translations")
        print(f"  📊 Total: {total_translations} translations across all languages")
    else:
        print("🔍 No translations file found")
    
    return total_translations

def ensure_all_languages_available(translations: Dict, settings: Dict, dry_run: bool = True) -> tuple[Dict, int]:
    """
    Ensure all enabled languages are available in translations.
    Adds missing languages with basic translations.
    Returns (updated_translations, total_added_terms)
    """
    enable_languages = settings.get("enable_languages", ["en", "es", "es-419", "ja"])
    total_added_terms = 0
    
    if not translations:
        print("📝 No translations file found. Creating new one with all enabled languages...")
        translations = {}
    
    # Get currently available languages
    available_languages = []
    if translations:
        translation_service = TranslationService(translations)
        available_languages = translation_service.get_available_languages()
    
    # Find missing languages
    missing_languages = [lang for lang in enable_languages if lang not in available_languages]
    
    if missing_languages:
        print(f"🔧 Found missing languages: {missing_languages}")
        print(f"📋 Available languages: {available_languages}")
        print(f"🎯 Target languages: {enable_languages}")
        
        for lang in missing_languages:
            translations, added_terms = add_missing_language_to_translations(translations, lang, settings, dry_run)
            total_added_terms += added_terms
        
        if not dry_run:
            print("✅ All missing languages have been added!")
        else:
            print("🎯 All missing languages would be added (dry run)")
    else:
        print(f"✅ All enabled languages are available: {available_languages}")
        print(f"📊 Using existing translations from custom_translations.json")
    
    return translations, total_added_terms

def clean_translation_text(text):
    """Clean translation text by removing extra quotes and formatting."""
    if not text:
        return text
    text = text.strip().strip('"').strip("'")
    text = re.sub(r"^['\"""]+|['\"""]+$", '', text)
    return text

def translate_full_sentence(text, target_lang, retries=3):
    if not text.strip():
        return text
    system_message = (
        f"You are a professional translator. "
        f"Translate the provided YouTube metadata text into {target_lang}. "
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
                max_tokens=3500,
            )
            translation = response.choices[0].message.content.strip()
            # Clean the translation text to remove any extra quotes or formatting
            translation = clean_translation_text(translation)
            return translation
        except Exception as e:
            print(f"⚠️ Translation API error on attempt {attempt + 1}: {e}")
    print("⚠️ Translation failed after retries, returning original text.")
    return text

def update_video_metadata(video_metadata: Dict, settings: Dict, 
                         translations: Dict, dry_run: bool = True) -> Optional[Dict]:
    """Update video metadata with translations and settings, adding multiple language versions."""
    updated = video_metadata.copy()
    changes_made = False
    
    # Detect the original language of the content
    title = updated.get("title", "")
    description = updated.get("description", "")
    content_text = f"{title} {description}"
    detected_lang = detect_language(content_text)
    
    # Update settings with detected language for better default language selection
    if detected_lang != "unknown":
        settings = settings.copy()
        settings["detected_language"] = detected_lang
        print(f"🌐 Detected original language: {detected_lang}")
    
    # Apply title prefix if not already present
    title_prefix = settings.get("default_title_prefix", "")
    if title_prefix and not updated["title"].startswith(title_prefix):
        updated["title"] = title_prefix + " " + updated["title"]
        changes_made = True
    
    # Apply description prefix if not already present
    desc_prefix = settings.get("default_description_prefix", "")
    if desc_prefix:
        # Check if the prefix is already at the beginning of the description
        description = updated["description"]
        if not description.startswith(desc_prefix):
            # Remove any existing prefix if it's there
            if description.startswith("Gracias por mirar! ✨"):
                description = description.replace("Gracias por mirar! ✨", "").strip()
            
            # Add the prefix at the beginning
            updated["description"] = desc_prefix + "\n\n" + description
            changes_made = True
    
    # Apply default tags if none exist
    if not updated.get("tags"):
        updated["tags"] = settings.get("tags_template", [])
        changes_made = True
    
    # Apply visibility setting
    if updated.get("visibility") != settings.get("default_visibility"):
        updated["visibility"] = settings.get("default_visibility", "private")
        changes_made = True
    
    # Initialize localizations for multiple language versions
    localizations = {}
    
    enable_languages = settings.get("enable_languages", ["en", "es", "es-419", "ja"])
    # For each enabled language, always add a localization using full-sentence translation
    for lang in enable_languages:
        # Full-sentence translation for title and description
        translated_title = translate_full_sentence(updated["title"], lang)
        translated_title = format_title_case(translated_title)
        description = updated["description"]
        desc_prefix = settings.get("default_description_prefix", "")
        if desc_prefix and description.startswith(desc_prefix):
            prefix_part = desc_prefix
            content_part = description[len(desc_prefix):].strip()
            translated_content = translate_full_sentence(content_part, lang)
            translated_desc = prefix_part + "\n\n" + translated_content
        else:
            translated_desc = translate_full_sentence(description, lang)
        # Always add localization, even if identical
        localizations[lang] = {
            "title": translated_title,
            "description": translated_desc
        }
        print(f"  ➕ Added {lang} localization: '{translated_title[:50]}...'")
        changes_made = True
    # If we have localizations, add them to the updated metadata
    if localizations:
        updated["localizations"] = localizations
        print(f"📝 Added {len(localizations)} language localizations")
    return updated if changes_made else None

# ------------------ Queue Management ------------------ #

def load_video_queue() -> List[Dict]:
    """Load video queue from JSON file."""
    if os.path.exists(VIDEO_QUEUE):
        with open(VIDEO_QUEUE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_video_queue(queue: List[Dict]) -> None:
    """Save video queue to JSON file."""
    with open(VIDEO_QUEUE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)

def append_to_processed(video_result: Dict) -> None:
    """Append processed video result to processed queue."""
    processed = []
    if os.path.exists(PROCESSED_QUEUE):
        with open(PROCESSED_QUEUE, "r", encoding="utf-8") as f:
            processed = json.load(f)
    
    # Add timestamp to the result
    video_result["timestamp"] = datetime.now().isoformat()
    processed.append(video_result)
    
    with open(PROCESSED_QUEUE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)

def create_queue_from_input(input_file: str) -> List[Dict]:
    """Create a queue from input file for processing."""
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return []
    
    with open(input_file, "r", encoding="utf-8") as f:
        videos = json.load(f)
    
    # Convert to queue format
    queue = []
    for video in videos:
        video_id = video.get("videoId")
        if video_id:
            queue.append({
                "id": video_id,
                "title": video.get("title", ""),
                "description": video.get("description", ""),
                "tags": video.get("tags", []),
                "visibility": video.get("visibility", "private")
            })
    
    return queue

def analyze_tag_changes(old_tags: List[str], new_tags: List[str]) -> Dict:
    """Analyze changes between old and new tags."""
    old_set = set(old_tags)
    new_set = set(new_tags)
    
    added = new_set - old_set
    removed = old_set - new_set
    unchanged = old_set & new_set
    
    return {
        "added": list(added),
        "removed": list(removed),
        "unchanged": list(unchanged),
        "total_old": len(old_tags),
        "total_new": len(new_tags),
        "net_change": len(new_tags) - len(old_tags)
    }

def format_description_preview(description: str, max_length: int = 100) -> str:
    """Format description for preview, truncating if too long."""
    if len(description) <= max_length:
        return description
    return description[:max_length] + "..."

def print_detailed_changes(video_id: str, original: Dict, updated: Dict, 
                          current_lang: str, dry_run: bool = True) -> None:
    """Print detailed changes in a formatted way."""
    print(f"\n{'='*80}")
    print(f"📹 VIDEO: {video_id}")
    print(f"🌐 LANGUAGE: {current_lang}")
    print(f"{'='*80}")
    
    # Title changes
    if original["title"] != updated["title"]:
        print(f"\n📝 TITLE CHANGES:")
        print(f"  OLD: {original['title']}")
        print(f"  NEW: {updated['title']}")
        print(f"  LENGTH: {len(original['title'])} → {len(updated['title'])} chars")
    else:
        print(f"\n📝 TITLE: No changes")
        print(f"  CURRENT: {original['title']}")
    
    # Description changes
    if original["description"] != updated["description"]:
        print(f"\n📄 DESCRIPTION CHANGES:")
        print(f"  OLD: {format_description_preview(original['description'])}")
        print(f"  NEW: {format_description_preview(updated['description'])}")
        print(f"  LENGTH: {len(original['description'])} → {len(updated['description'])} chars")
        
        # Show full description if it's short enough
        if len(updated['description']) <= 200:
            print(f"  FULL NEW DESCRIPTION:")
            print(f"    {updated['description']}")
    else:
        print(f"\n📄 DESCRIPTION: No changes")
        print(f"  CURRENT: {format_description_preview(original['description'])}")
    
    # Localization changes
    if updated.get("localizations"):
        print(f"\n🌐 LOCALIZATION CHANGES:")
        localizations = updated["localizations"]
        print(f"  ADDING {len(localizations)} LANGUAGE VERSION(S):")
        for lang, loc_data in localizations.items():
            print(f"    {lang.upper()}:")
            print(f"      Title: {loc_data['title'][:60]}...")
            print(f"      Description: {format_description_preview(loc_data['description'], 80)}")
    else:
        print(f"\n🌐 LOCALIZATIONS: No language versions added")
    
    # Tag analysis
    tag_analysis = analyze_tag_changes(original.get("tags", []), updated.get("tags", []))
    print(f"\n🏷️  TAG ANALYSIS:")
    print(f"  TOTAL: {tag_analysis['total_old']} → {tag_analysis['total_new']} (net: {tag_analysis['net_change']:+d})")
    
    if tag_analysis['added']:
        print(f"  ➕ ADDED ({len(tag_analysis['added'])}):")
        for tag in sorted(tag_analysis['added']):
            print(f"    • {tag}")
    
    if tag_analysis['removed']:
        print(f"  ➖ REMOVED ({len(tag_analysis['removed'])}):")
        for tag in sorted(tag_analysis['removed']):
            print(f"    • {tag}")
    
    if tag_analysis['unchanged']:
        print(f"  🔄 UNCHANGED ({len(tag_analysis['unchanged'])}):")
        for tag in sorted(tag_analysis['unchanged'])[:10]:  # Show first 10
            print(f"    • {tag}")
        if len(tag_analysis['unchanged']) > 10:
            print(f"    ... and {len(tag_analysis['unchanged']) - 10} more")
    
    # Visibility changes
    if original.get("visibility") != updated.get("visibility"):
        print(f"\n👁️  VISIBILITY:")
        print(f"  OLD: {original.get('visibility', 'private')}")
        print(f"  NEW: {updated.get('visibility', 'private')}")
    else:
        print(f"\n👁️  VISIBILITY: No changes ({original.get('visibility', 'private')})")
    
    # Summary
    changes_count = sum([
        1 if original["title"] != updated["title"] else 0,
        1 if original["description"] != updated["description"] else 0,
        1 if original.get("tags", []) != updated.get("tags", []) else 0,
        1 if original.get("visibility") != updated.get("visibility") else 0,
        1 if updated.get("localizations") else 0
    ])
    
    print(f"\n📊 SUMMARY:")
    print(f"  CHANGES: {changes_count} field(s) modified")
    if updated.get("localizations"):
        print(f"  LANGUAGES: Added {len(updated['localizations'])} language version(s)")
    if dry_run:
        print(f"  STATUS: DRY RUN - No actual changes made")
    else:
        print(f"  STATUS: Changes applied to YouTube")
    
    print(f"{'='*80}")

def main():
    parser = argparse.ArgumentParser(description="Update YouTube Shorts metadata")
    parser.add_argument("--input", default="videos_today.json", 
                       help="Input JSON file with videos (default: videos_today.json)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be updated without making changes")
    parser.add_argument("--video-id", 
                       help="Update specific video ID only")
    parser.add_argument("--test", action="store_true", 
                       help="Test API connection only")
    parser.add_argument("--queue-mode", action="store_true",
                       help="Use queue mode: process videos from queue and move to processed list")
    parser.add_argument("--create-queue", action="store_true",
                       help="Create queue from input file and exit")
    parser.add_argument("--limit", type=int,
                       help="Limit number of videos to process")
    parser.add_argument("--version", action="store_true",
                       help="Show version and exit")
    parser.add_argument("--add-missing-languages", action="store_true",
                       help="Add missing languages to translations file")
    parser.add_argument("--ensure-languages", action="store_true",
                       help="Ensure all enabled languages are available in translations")
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        print(f"YouTube Shorts Updater v{VERSION}")
        return
    
    print(f"🎬 YouTube Shorts Updater v{VERSION}")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
        
        # Load custom translations
        translations = load_custom_translations()
        
        # Handle adding missing languages
        if args.add_missing_languages:
            enable_languages = shorts_service.settings.get("enable_languages", ["en", "es", "es-419", "ja"])
            available_languages = []
            if translations:
                translation_service = TranslationService(translations)
                available_languages = translation_service.get_available_languages()
            
            missing_languages = [lang for lang in enable_languages if lang not in available_languages]
            
            if missing_languages:
                print(f"🔧 Adding missing languages: {missing_languages}")
                total_added = 0
                for lang in missing_languages:
                    translations, added_terms = add_missing_language_to_translations(translations, lang, shorts_service.settings, args.dry_run)
                    total_added += added_terms
                print("✅ Missing languages added!")
                if args.dry_run:
                    print(f"🎯 Would add {total_added} total translations (dry run)")
            else:
                print("✅ All enabled languages are already available in translations")
            return
        
        # Handle ensuring all languages are available
        if args.ensure_languages:
            translations, total_added = ensure_all_languages_available(translations, shorts_service.settings, args.dry_run)
            if args.dry_run and total_added > 0:
                print(f"🎯 Would add {total_added} total translations (dry run)")
            return
        
        # Track languages added during processing
        total_languages_added = 0
        total_translations_available = 0
        
        # Ensure all languages are available before processing
        if not args.dry_run:
            print("🔍 Checking for missing languages...")
            translations, total_added = ensure_all_languages_available(translations, shorts_service.settings, dry_run=False)
            total_languages_added += total_added
        else:
            # Also check for missing languages during dry run to get the count
            print("🔍 Checking for missing languages (dry run)...")
            _, total_added = ensure_all_languages_available(translations, shorts_service.settings, dry_run=True)
            total_languages_added += total_added
        
        # Count total translations available for enabled languages
        total_translations_available = count_translations_for_enabled_languages(translations, shorts_service.settings)
        
        # Handle queue creation
        if args.create_queue:
            queue = create_queue_from_input(args.input)
            if queue:
                save_video_queue(queue)
                print(f"✅ Created queue with {len(queue)} videos from {args.input}")
            else:
                print("❌ No videos found to create queue")
            return
        
        # Handle queue mode
        if args.queue_mode:
            queue = load_video_queue()
            if not queue:
                print("📥 No queue file found. Creating queue from input file...")
                queue = create_queue_from_input(args.input)
                if queue:
                    save_video_queue(queue)
                    print(f"✅ Created queue with {len(queue)} videos")
                else:
                    print("❌ No videos found to process")
                    return
            
            print(f"🔧 Processing {len(queue)} videos from queue...")
            print(f"🌐 Enabled languages: {shorts_service.settings.get('enable_languages', ['en', 'es', 'es-419', 'ja'])}")
            
            processed_count = 0
            limit = args.limit or len(queue)
            
            while queue and processed_count < limit:
                video_entry = queue.pop(0)
                video_id = video_entry["id"]
                
                # Update metadata
                updated = update_video_metadata(
                    video_entry, 
                    shorts_service.settings, 
                    translations, 
                    dry_run=args.dry_run
                )
                
                if updated:
                    # Print detailed changes
                    print_detailed_changes(video_id, video_entry, updated, "manual", args.dry_run)
                    
                    if not args.dry_run:
                        try:
                            success = shorts_service.update_video_metadata(video_id, updated)
                            if success:
                                # Add to processed list
                                processed_result = {
                                    "video_id": video_id,
                                    "title": updated["title"],
                                    "changes": [
                                        f"Updated title: {video_entry.get('title', '')} → {updated['title']}",
                                        f"Updated description: {len(video_entry.get('description', ''))} chars → {len(updated['description'])} chars",
                                        f"Updated tags: {len(video_entry.get('tags', []))} → {len(updated['tags'])}",
                                        f"Updated visibility: {video_entry.get('visibility', 'private')} → {updated['visibility']}",
                                        f"Added {len(updated.get('localizations', {}))} language version(s)"
                                    ]
                                }
                                append_to_processed(processed_result)
                                processed_count += 1
                                print(f"✅ Video {video_id} processed and added to processed list")
                                # Remove from videos_today.json
                                if os.path.exists(args.input):
                                    with open(args.input, "r", encoding="utf-8") as f:
                                        today_videos = json.load(f)
                                    # Remove by videoId (not id)
                                    today_videos = [v for v in today_videos if v.get("videoId") != video_id]
                                    with open(args.input, "w", encoding="utf-8") as f:
                                        json.dump(today_videos, f, indent=2, ensure_ascii=False)
                            else:
                                print(f"❌ Failed to update video {video_id}")
                                # Put back in queue for retry
                                queue.append(video_entry)
                        except Exception as e:
                            if str(e) == "YOUTUBE_QUOTA_EXCEEDED":
                                print(f"\n🛑 YouTube API quota exceeded after processing {processed_count} videos.")
                                print(f"📊 Progress: {processed_count}/{len(queue)} videos processed successfully.")
                                print(f"⏰ YouTube API quota resets daily. You can continue later with:")
                                print(f"   python3 shorts_updater.py --queue-mode --limit {len(queue) - processed_count}")
                                return
                            else:
                                raise e
                    else:
                        processed_count += 1
                else:
                    print(f"✅ Video {video_id} - No changes needed")
                    # Still add to processed list to avoid reprocessing
                    processed_result = {
                        "video_id": video_id,
                        "title": video_entry.get("title", ""),
                        "changes": ["No changes needed"]
                    }
                    append_to_processed(processed_result)
                    processed_count += 1
                    # Remove from videos_today.json even if no changes
                    if not args.dry_run and os.path.exists(args.input):
                        with open(args.input, "r", encoding="utf-8") as f:
                            today_videos = json.load(f)
                        today_videos = [v for v in today_videos if v.get("videoId") != video_id]
                        with open(args.input, "w", encoding="utf-8") as f:
                            json.dump(today_videos, f, indent=2, ensure_ascii=False)
                
                # Save updated queue
                save_video_queue(queue)
            
            if args.dry_run:
                print(f"\n🎯 Dry run completed. {processed_count} videos would be processed.")
                if total_languages_added > 0:
                    print(f"🌐 Languages added: {total_languages_added} translations would be added to the translations file.")
                print(f"📚 Total translations available: {total_translations_available} translations in the translations file for enabled languages.")
            else:
                print(f"\n✅ Queue processing completed. {processed_count} videos processed successfully.")
                print(f"📊 Queue status: {len(queue)} videos remaining in queue")
                if total_languages_added > 0:
                    print(f"🌐 Languages added: {total_languages_added} translations were added to the translations file.")
                print(f"📚 Total translations available: {total_translations_available} translations in the translations file for enabled languages.")
            
            return
        
        # Original mode - process all videos from input file
        if not os.path.exists(args.input):
            print(f"❌ Input file not found: {args.input}")
            sys.exit(1)
        
        with open(args.input, "r", encoding="utf-8") as f:
            videos = json.load(f)
        
        if not videos:
            print("❌ No videos found in input file")
            return
        
        # Filter by specific video ID if provided
        if args.video_id:
            videos = [v for v in videos if v.get("videoId") == args.video_id]
            if not videos:
                print(f"❌ Video ID {args.video_id} not found in input file")
                return
        
        print(f"🔧 Processing {len(videos)} video(s)...")
        print(f"🌐 Enabled languages: {shorts_service.settings.get('enable_languages', ['en', 'es', 'es-419', 'ja'])}")
        
        updated_count = 0
        for video in videos:
            video_id = video.get("videoId")
            if not video_id:
                continue
            
            # Prepare metadata
            video_metadata = {
                "id": video_id,
                "title": video.get("title", ""),
                "description": video.get("description", ""),
                "tags": video.get("tags", []),
                "visibility": video.get("visibility", "private")
            }
            
            # Update metadata
            updated = update_video_metadata(
                video_metadata, 
                shorts_service.settings, 
                translations, 
                dry_run=args.dry_run
            )
            
            if updated:
                # Print detailed changes
                print_detailed_changes(video_id, video_metadata, updated, "manual", args.dry_run)
                
                if not args.dry_run:
                    try:
                        success = shorts_service.update_video_metadata(video_id, updated)
                        if success:
                            updated_count += 1
                    except Exception as e:
                        if str(e) == "YOUTUBE_QUOTA_EXCEEDED":
                            print(f"\n🛑 YouTube API quota exceeded after processing {updated_count} videos.")
                            print(f"📊 Progress: {updated_count}/{len(videos)} videos processed successfully.")
                            print(f"⏰ YouTube API quota resets daily. You can continue later with:")
                            print(f"   python3 shorts_updater.py --input {args.input} --limit {len(videos) - updated_count}")
                            return
                        else:
                            raise e
                else:
                    updated_count += 1
            else:
                print(f"✅ Video {video_id} - No changes needed")
        
        if args.dry_run:
            print(f"\n🎯 Dry run completed. {updated_count} videos would be updated.")
            if total_languages_added > 0:
                print(f"🌐 Languages added: {total_languages_added} translations would be added to the translations file.")
            print(f"📚 Total translations available: {total_translations_available} translations in the translations file for enabled languages.")
        else:
            print(f"\n✅ Update completed. {updated_count} videos updated successfully.")
            if total_languages_added > 0:
                print(f"🌐 Languages added: {total_languages_added} translations were added to the translations file.")
            print(f"📚 Total translations available: {total_translations_available} translations in the translations file for enabled languages.")
    
    except Exception as e:
        if str(e) == "YOUTUBE_QUOTA_EXCEEDED":
            print(f"\n🛑 YouTube API quota exceeded. Processing stopped.")
            print(f"⏰ YouTube API quota resets daily. You can continue later.")
            sys.exit(1)
        else:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main() 