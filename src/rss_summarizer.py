from mistralai.client import MistralClient
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
        self.mistral = MistralClient(api_key=mistral_api_key)
        self.logger = logger
        self.config = config['summarization']

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
        Make a request to Mistral AI with exponential backoff retry.
        
        Args:
            messages: List of message dictionaries for the chat completion
            
        Returns:
            Generated content or None if failed
        """
        try:
            response = self.mistral.chat(
                model=self.config['model'],
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip() if response.choices else None
        except Exception as e:
            self.logger.error(f"Error in Mistral API request: {e}")
            raise

    def create_summary(self, title: str, description: str) -> Optional[str]:
        """
        Generate a summary using Mistral AI.
        
        Args:
            title: Article title
            description: Article description
            
        Returns:
            Generated summary or None if failed
        """
        messages = [{
            "role": "user",
            "content": f"""Please provide a brief, one-paragraph summary of the following article:
            Title: {title}
            Content: {description}
            
            Keep the summary concise and focused on the key points."""
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
            "content": f"""Create a concise, engaging title (maximum 100 characters) for this article that captures its main point:
            Original Title: {title}
            Content: {description}
            
            Respond with only the new title, no additional text."""
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
        messages = [{
            "role": "user",
            "content": f"""Categorize this article into exactly one of these categories: 
            Politics, Economy, Technology, Society, Culture, Sports, Environment, Health, Education, International

            Title: {title}
            Content: {description}
            
            Respond with only the category name, no additional text."""
        }]
        
        return self._make_mistral_request(messages)

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
                    # Add base delay between entries to prevent rate limiting
                    time.sleep(self.config.get('base_delay', 2))
                    
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