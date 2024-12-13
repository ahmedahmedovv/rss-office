from datetime import datetime, timedelta
from supabase import Client
from typing import List
import feedparser
from dateutil import parser
import pytz
import logging
from html import unescape
import re

class RSSFetcher:
    def __init__(self, supabase: Client, logger: logging.Logger):
        self.supabase = supabase
        self.logger = logger

    def clean_html(self, text: str) -> str:
        """Remove HTML tags and normalize text"""
        if not text:
            return ""
        text = unescape(text)
        clean = re.sub(r'<[^>]+>', '', text)
        clean = ' '.join(clean.split())
        return clean.strip()

    def make_timezone_aware(self, dt: datetime) -> datetime:
        """Convert naive datetime to UTC timezone-aware datetime"""
        if dt.tzinfo is None:
            return pytz.UTC.localize(dt)
        return dt.astimezone(pytz.UTC)

    def get_latest_entry_date(self, source_url: str, default_days: int) -> datetime:
        """Get the latest publication date for a given source URL"""
        try:
            result = self.supabase.table("rss_feeds")\
                .select("pub_date")\
                .eq("source_url", source_url)\
                .order("pub_date", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and result.data[0].get("pub_date"):
                return self.make_timezone_aware(parser.parse(result.data[0]["pub_date"]))
            return self.make_timezone_aware(datetime.now() - timedelta(days=default_days))
        except Exception as e:
            self.logger.error(f"Error getting latest entry date: {str(e)}")
            return self.make_timezone_aware(datetime.now() - timedelta(days=default_days))

    def fetch_and_save(self, url: str, default_days: int) -> None:
        """Fetch RSS entries and save to database"""
        try:
            latest_date = self.get_latest_entry_date(url, default_days)
            feed = feedparser.parse(url)
            entries = []

            for entry in feed.entries:
                try:
                    pub_date = self.make_timezone_aware(parser.parse(entry.published))
                    if pub_date > latest_date:
                        entries.append({
                            "title": self.clean_html(entry.get("title", "")),
                            "description": self.clean_html(entry.get("description", "")),
                            "link": entry.get("link", ""),
                            "pub_date": pub_date.isoformat(),
                            "source_url": url
                        })
                except Exception as e:
                    self.logger.warning(f"Error processing entry: {str(e)}")
                    continue

            if entries:
                self.supabase.table("rss_feeds").upsert(
                    entries,
                    on_conflict="link,source_url"
                ).execute()
                self.logger.info(f"Saved {len(entries)} entries from {url}")

        except Exception as e:
            self.logger.error(f"Error fetching RSS from {url}: {str(e)}") 