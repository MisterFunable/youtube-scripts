import openai
import os
import re

openai.api_key = os.getenv("OPENAI_API_KEY")

def strip_surrounding_quotes(text):
    if not text:
        return text
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith(""") and text.endswith("")):
        return text[1:-1].strip()
    return text

def clean_translation_text(text):
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
            return clean_translation_text(translation)
        except Exception as e:
            print(f"⚠️ Translation API error on attempt {attempt + 1}: {e}")
    print("⚠️ Translation failed after retries, returning original text.")
    return text
