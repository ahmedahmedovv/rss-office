from supabase import Client
import logging
from deep_translator import GoogleTranslator
from typing import List
from datetime import datetime
import pytz
from langdetect import detect

class RSSTranslator:
    def __init__(self, supabase: Client, logger: logging.Logger):
        self.supabase = supabase
        self.logger = logger
        self.translator = GoogleTranslator(source='auto', target='en')

    def is_english(self, text: str) -> bool:
        """Check if text is already in English"""
        try:
            if not text or len(text.strip()) < 10:  # Skip very short texts
                return True
            return detect(text) == 'en'
        except Exception as e:
            self.logger.warning(f"Language detection error: {str(e)}")
            return False

    def translate_text(self, text: str) -> str:
        """Translate text to English if not already in English"""
        try:
            if not text:
                return ""
            if self.is_english(text):
                self.logger.debug("Text already in English, skipping translation")
                return text
            return self.translator.translate(text)
        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            return ""

    def get_untranslated_entries(self, batch_size: int = 10) -> List[dict]:
        """Get entries that haven't been translated yet"""
        try:
            result = self.supabase.table("rss_feeds")\
                .select("id", "title", "description")\
                .is_("translated_at", "null")\
                .limit(batch_size)\
                .execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Error fetching untranslated entries: {str(e)}")
            return []

    def translate_entries(self, batch_size: int = 10) -> None:
        """Translate and update entries"""
        while True:  # Continue until no untranslated entries remain
            entries = self.get_untranslated_entries(batch_size)
            
            if not entries:  # Exit if no more entries to translate
                self.logger.info("No more entries to translate")
                break
            
            for entry in entries:
                try:
                    translated = {
                        "title_en": self.translate_text(entry["title"]),
                        "description_en": self.translate_text(entry["description"]),
                        "translated_at": datetime.now(pytz.UTC).isoformat()
                    }
                    
                    self.supabase.table("rss_feeds")\
                        .update(translated)\
                        .eq("id", entry["id"])\
                        .execute()
                    
                    self.logger.info(f"Translated entry {entry['id']}")
                except Exception as e:
                    self.logger.error(f"Error updating translated entry {entry['id']}: {str(e)}") 