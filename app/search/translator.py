"""Automatic translation module for translating Japanese queries into scientific English."""
import re
import urllib.request
import urllib.parse
import json
import logging
from typing import Tuple
from ..config import config

logger = logging.getLogger(__name__)

def is_japanese(text: str) -> bool:
    """Check if the text contains Japanese characters (Hiragana, Katakana, or Kanji)."""
    return bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text))

def translate_query(text: str, api_key: str = None) -> Tuple[str, bool]:
    """Translate Japanese text to academic English. Returns (translated_text, was_translated)."""
    text = text.strip()
    if not is_japanese(text):
        return text, False

    key = api_key or config.GEMINI_API_KEY
    if key:
        try:
            from google import genai
            client = genai.Client(api_key=key)
            prompt = (
                f"Translate the following Japanese scientific/medical research query into concise, "
                f"standard English academic search keywords. Only output the translated English keywords without quotes or explanations:\n{text}"
            )
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            if resp and resp.text:
                cleaned = resp.text.strip().replace('"', '').replace("'", "")
                return cleaned, True
        except Exception as e:
            logger.warning(f"Gemini translation failed: {e}")

    # Fallback: Free MyMemory API
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair=ja|en"
        req = urllib.request.Request(url, headers={"User-Agent": "OpenJournalMetaAnalyzer/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("responseData", {}).get("translatedText")
            if translated and not translated.startswith("MYMEMORY WARNING"):
                # Clean punctuation
                cleaned = re.sub(r"[.!?]", "", translated).strip()
                return cleaned, True
    except Exception as e:
        logger.warning(f"MyMemory translation failed: {e}")

    return text, False


translate_to_english = translate_query