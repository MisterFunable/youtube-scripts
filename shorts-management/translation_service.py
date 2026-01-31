"""
Translation Service for YouTube Shorts
Handles custom translations and fallback to external services
"""

import re
from typing import Dict, Optional

class TranslationService:
    """Handles text translation using custom dictionaries and fallback services."""
    
    def __init__(self, custom_translations: Dict):
        self.custom_translations = custom_translations
        self._build_translation_cache()
    
    def _build_translation_cache(self):
        """Build a cache of all translations for faster lookup."""
        self.translation_cache = {}
        
        for category, items in self.custom_translations.items():
            for key, translations in items.items():
                for lang, translation in translations.items():
                    if lang not in self.translation_cache:
                        self.translation_cache[lang] = {}
                    self.translation_cache[lang][key.lower()] = translation
    
    def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text using custom translations."""
        if target_lang not in self.translation_cache:
            return text
        
        translated_text = text
        cache = self.translation_cache[target_lang]
        
        # Sort keys by length (longest first) to avoid partial matches
        sorted_keys = sorted(cache.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            # Use case-insensitive replacement
            pattern = re.compile(re.escape(key), re.IGNORECASE)
            replacement = cache[key]
            
            # Clean up any double quotes that might be in the replacement
            if isinstance(replacement, str):
                replacement = replacement.strip('"').strip("'")
            
            translated_text = pattern.sub(replacement, translated_text)
        
        return translated_text
    
    def get_available_languages(self) -> list:
        """Get list of available target languages."""
        return list(self.translation_cache.keys())
    
    def get_translation_categories(self) -> list:
        """Get list of translation categories."""
        return list(self.custom_translations.keys())
    
    def add_custom_translation(self, category: str, key: str, translations: Dict):
        """Add a new custom translation."""
        if category not in self.custom_translations:
            self.custom_translations[category] = {}
        
        self.custom_translations[category][key] = translations
        self._build_translation_cache() 