from mistralai import Mistral
from supabase import Client
import logging
from datetime import datetime
import pytz
from typing import List, Optional, Dict, Any
import time
import backoff

class RSSSummarizer:
    def __init__(self, supabase: Client, mistral_api_key: str, logger: logging.Logger, config: dict):
        """
        Initialize RSSSummarizer with required clients and configuration.
        
        Args:
            supabase: Supabase client instance
            mistral_api_key: API key for Mistral AI
            logger: Logger instance
            config: Configuration dictionary
        """
        self.supabase = supabase
        self.mistral = Mistral(api_key=mistral_api_key)
        self.logger = logger
        self.config = config['summarization']
        self.last_request_time = 0
        self.min_request_interval = self.config.get('min_request_interval', 1.0)  # seconds

    def get_unsummarized_entries(self, batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch entries that haven't been processed yet.
        
        Args:
            batch_size: Number of entries to fetch
            
        Returns:
            List of unprocessed entries
        """
        try:
            result = self.supabase.table("rss_feeds")\
                .select("id", "title", "description")\
                .is_("summarized_at", "null")\
                .is_("ai_title_generated_at", "null")\
                .is_("category_generated_at", "null")\
                .not_.is_("translated_at", "null")\
                .limit(batch_size)\
                .execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Error fetching unsummarized entries: {e}")
            return []

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=30
    )
    def _make_mistral_request(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Make a request to Mistral AI with rate limiting and exponential backoff retry.
        
        Args:
            messages: List of message dictionaries for the chat completion
            
        Returns:
            Generated content or None if failed
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        try:
            response = self.mistral.chat.complete(
                model=self.config['model'],
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            self.last_request_time = time.time()  # Update last request time
            return response.choices[0].message.content.strip() if response.choices else None
        except Exception as e:
            self.logger.error(f"Error in Mistral API request: {e}")
            raise

    def create_summary(self, title: str, description: str) -> Optional[str]:
        """
        Generate a short summary using Mistral AI.
        
        Args:
            title: Article title
            description: Article description
            
        Returns:
            Generated summary or None if failed
        """
        messages = [{
            "role": "user",
            "content": f"""Summarize this article in 2-3 concise sentences IN ENGLISH:
            Title: {title}
            Content: {description}
            
            Rules:
            1. Maximum 50 words
            2. Focus only on the most important point
            3. Use simple, clear language
            4. Always respond in English regardless of input language
            
            Respond with just the summary, no additional text."""
        }]
        
        return self._make_mistral_request(messages)

    def create_ai_title(self, title: str, description: str) -> Optional[str]:
        """
        Generate an AI title using Mistral AI.
        
        Args:
            title: Original title
            description: Article description
            
        Returns:
            Generated title or None if failed
        """
        messages = [{
            "role": "user",
            "content": f"""Create a concise, engaging title IN ENGLISH (maximum 100 characters) for this article that captures its main point:
            Original Title: {title}
            Content: {description}
            
            Respond with only the new title in English, no additional text, regardless of the input language."""
        }]
        
        return self._make_mistral_request(messages)

    def create_category(self, title: str, description: str) -> Optional[str]:
        """
        Generate a category using Mistral AI.
        
        Args:
            title: Article title
            description: Article description
            
        Returns:
            Generated category or None if failed
        """
        available_categories = ", ".join(self.config['categories'])
        
        messages = [{
            "role": "user",
            "content": f"""Analyze this article and select the most appropriate category from the following list:
            {available_categories}

            Article Title: {title}
            Article Content: {description}
            
            Rules:
            1. Choose exactly ONE category from the provided list
            2. Return ONLY the category name, exactly as written above
            3. If content spans multiple categories, choose the most dominant one
            
            Response format: Return only the category name, no additional text or explanation."""
        }]
        
        category = self._make_mistral_request(messages)
        
        # Validate the returned category
        if category and category in self.config['categories']:
            return category
        
        self.logger.warning(f"Invalid category returned: {category}")
        return None

    def update_entry(self, entry_id: str, update_data: Dict[str, Any]) -> None:
        """
        Update an entry in the database.
        
        Args:
            entry_id: ID of the entry to update
            update_data: Dictionary of fields to update
        """
        try:
            self.supabase.table("rss_feeds")\
                .update(update_data)\
                .eq("id", entry_id)\
                .execute()
        except Exception as e:
            self.logger.error(f"Error updating entry {entry_id}: {e}")
            raise

    def summarize_entries(self, batch_size: Optional[int] = None) -> None:
        """
        Process a batch of entries with summaries, AI titles, and categories.
        
        Args:
            batch_size: Optional number of entries to process
        """
        if batch_size is None:
            batch_size = self.config['batch_size']

        while True:
            entries = self.get_unsummarized_entries(batch_size)
            
            if not entries:
                self.logger.info("No more entries to summarize")
                break
            
            for entry in entries:
                try:
                    # Increased base delay between entries
                    time.sleep(self.config.get('base_delay', 3))  # Increased from 2 to 3 seconds
                    
                    current_time = datetime.now(pytz.UTC).isoformat()
                    update_data = {}

                    # Generate and add summary
                    if summary := self.create_summary(entry["title"], entry["description"]):
                        update_data.update({
                            "summary": summary,
                            "summarized_at": current_time
                        })

                    # Generate and add AI title
                    if ai_title := self.create_ai_title(entry["title"], entry["description"]):
                        update_data.update({
                            "ai_title": ai_title,
                            "ai_title_generated_at": current_time
                        })

                    # Generate and add category
                    if category := self.create_category(entry["title"], entry["description"]):
                        update_data.update({
                            "category": category,
                            "category_generated_at": current_time
                        })

                    if update_data:
                        self.update_entry(entry["id"], update_data)
                        self.logger.info(f"Successfully processed entry {entry['id']}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process entry {entry['id']}: {e}")
                    continue