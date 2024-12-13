from mistralai import Mistral
from supabase import Client
import logging
from datetime import datetime
import pytz
from typing import List
import time

class RSSSummarizer:
    def __init__(self, supabase: Client, mistral_api_key: str, logger: logging.Logger, config: dict):
        self.supabase = supabase
        self.mistral = Mistral(api_key=mistral_api_key)
        self.logger = logger
        self.config = config['summarization']

    def get_unsummarized_entries(self, batch_size: int = 5) -> List[dict]:
        """Get entries that haven't been summarized yet"""
        try:
            result = self.supabase.table("rss_feeds")\
                .select("id", "title", "description")\
                .is_("summarized_at", "null")\
                .is_("ai_title_generated_at", "null")\
                .not_.is_("translated_at", "null")\
                .limit(batch_size)\
                .execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Error fetching unsummarized entries: {str(e)}")
            return []

    def create_summary(self, title: str, description: str, retry_count: int = 0) -> str:
        """Generate summary using Mistral AI with retry logic"""
        try:
            if not self.mistral:
                raise ValueError("Mistral client not properly initialized")

            # Add base delay between all requests to prevent rate limiting
            if retry_count == 0:
                time.sleep(1)  # 1 second base delay between requests
            else:
                # Exponential backoff for retries
                delay = self.config['retry_delay_seconds'] * (2 ** (retry_count - 1))
                self.logger.warning(
                    f"Rate limit hit, waiting {delay} seconds before retry "
                    f"(attempt {retry_count + 1}/{self.config['max_retries']})"
                )
                time.sleep(delay)

            messages = [
                {
                    "role": "user",
                    "content": f"""Please provide a brief, one-paragraph summary of the following article:
                    Title: {title}
                    Content: {description}
                    
                    Keep the summary concise and focused on the key points."""
                }
            ]

            response = self.mistral.chat.complete(
                model=self.config['model'],
                messages=messages
            )

            if response and response.choices:
                return response.choices[0].message.content.strip()
            return ""
            
        except Exception as e:
            if "rate limit" in str(e).lower() and retry_count < self.config['max_retries']:
                return self.create_summary(title, description, retry_count + 1)
            elif retry_count < self.config['max_retries']:
                self.logger.error(f"Error in summarization: {str(e)}")
                return self.create_summary(title, description, retry_count + 1)
            self.logger.error(f"Error generating summary after {self.config['max_retries']} attempts: {str(e)}")
            return ""

    def create_ai_title(self, title: str, description: str, retry_count: int = 0) -> str:
        """Generate AI title using Mistral AI with retry logic"""
        try:
            if not self.mistral:
                raise ValueError("Mistral client not properly initialized")

            if retry_count == 0:
                time.sleep(1)
            else:
                delay = self.config['retry_delay_seconds'] * (2 ** (retry_count - 1))
                self.logger.warning(
                    f"Rate limit hit, waiting {delay} seconds before retry "
                    f"(attempt {retry_count + 1}/{self.config['max_retries']})"
                )
                time.sleep(delay)

            messages = [
                {
                    "role": "user",
                    "content": f"""Create a concise, engaging title (maximum 100 characters) for this article that captures its main point:
                    Original Title: {title}
                    Content: {description}
                    
                    Respond with only the new title, no additional text."""
                }
            ]

            response = self.mistral.chat.complete(
                model=self.config['model'],
                messages=messages
            )

            if response and response.choices:
                return response.choices[0].message.content.strip()
            return ""
            
        except Exception as e:
            if "rate limit" in str(e).lower() and retry_count < self.config['max_retries']:
                return self.create_ai_title(title, description, retry_count + 1)
            elif retry_count < self.config['max_retries']:
                self.logger.error(f"Error in AI title generation: {str(e)}")
                return self.create_ai_title(title, description, retry_count + 1)
            self.logger.error(f"Error generating AI title after {self.config['max_retries']} attempts: {str(e)}")
            return ""

    def summarize_entries(self, batch_size: int = None) -> None:
        """Summarize and update entries"""
        if batch_size is None:
            batch_size = self.config['batch_size']

        while True:
            entries = self.get_unsummarized_entries(batch_size)
            
            if not entries:
                self.logger.info("No more entries to summarize")
                break
            
            for entry in entries:
                try:
                    summary = self.create_summary(entry["title"], entry["description"])
                    ai_title = self.create_ai_title(entry["title"], entry["description"])
                    
                    current_time = datetime.now(pytz.UTC).isoformat()
                    update_data = {
                        "summary": summary,
                        "summarized_at": current_time,
                    }
                    
                    if ai_title:
                        update_data.update({
                            "ai_title": ai_title,
                            "ai_title_generated_at": current_time
                        })
                    
                    self.supabase.table("rss_feeds")\
                        .update(update_data)\
                        .eq("id", entry["id"])\
                        .execute()
                    
                    self.logger.info(f"Processed entry {entry['id']}")
                    time.sleep(2)
                except Exception as e:
                    self.logger.error(f"Error updating entry {entry['id']}: {str(e)}")