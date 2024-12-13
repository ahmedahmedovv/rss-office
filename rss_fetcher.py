import os
import feedparser
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List
from dateutil import parser
import re
from html import unescape
import pytz
import logging
from logging.handlers import RotatingFileHandler
import yaml

# Load environment variables
load_dotenv()

def load_config():
    """Load configuration from YAML file"""
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def setup_logger(config):
    """Configure logging system"""
    log_config = config['logging']
    
    if not os.path.exists(log_config['directory']):
        os.makedirs(log_config['directory'])
    
    logger = logging.getLogger('RSSFetcher')
    logger.setLevel(getattr(logging, log_config['level']))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_config['level']))
    
    # File handler
    file_handler = RotatingFileHandler(
        os.path.join(log_config['directory'], log_config['filename']),
        maxBytes=log_config['max_size_mb']*1024*1024,
        backupCount=log_config['backup_count']
    )
    file_handler.setLevel(getattr(logging, log_config['level']))
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities."""
    if not text:
        return ""
    text = unescape(text)
    clean = re.sub(r'<[^>]+>', '', text)
    clean = ' '.join(clean.split())
    return clean.strip()

def make_timezone_aware(dt: datetime) -> datetime:
    """Convert naive datetime to UTC timezone-aware datetime."""
    if dt.tzinfo is None:
        return pytz.UTC.localize(dt)
    return dt.astimezone(pytz.UTC)

def get_latest_entry_date(supabase: Client, source_url: str, config: dict) -> datetime:
    """Get the latest publication date for a given source URL."""
    try:
        result = supabase.table("rss_feeds")\
            .select("pub_date")\
            .eq("source_url", source_url)\
            .order("pub_date", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data and result.data[0].get("pub_date"):
            return make_timezone_aware(parser.parse(result.data[0]["pub_date"]))
        logger.info(f"No previous entries found for {source_url}, defaulting to {config['rss']['default_history_days']} days ago")
        return make_timezone_aware(datetime.now() - timedelta(days=config['rss']['default_history_days']))
    except Exception as e:
        logger.error(f"Error getting latest entry date for {source_url}: {str(e)}")
        return make_timezone_aware(datetime.now() - timedelta(days=config['rss']['default_history_days']))

def fetch_rss(url: str, since_date: datetime) -> List[dict]:
    """Fetch and parse RSS feed, only returning entries newer than since_date."""
    try:
        logger.info(f"Fetching RSS from: {url}")
        feed = feedparser.parse(url)
        entries = []
        
        for entry in feed.entries:
            try:
                pub_date = make_timezone_aware(parser.parse(entry.published))
                
                if pub_date > since_date:
                    entries.append({
                        "title": clean_html(entry.get("title", "")),
                        "link": entry.get("link", ""),
                        "description": clean_html(entry.get("description", "")),
                        "pub_date": pub_date.isoformat(),
                        "source_url": url
                    })
            except (AttributeError, ValueError) as e:
                logger.warning(f"Error processing entry date for {url}: {str(e)}")
                continue
        
        logger.info(f"Found {len(entries)} new entries from {url}")
        return entries
    except Exception as e:
        logger.error(f"Error fetching RSS from {url}: {str(e)}")
        return []

def read_urls(filename: str) -> List[str]:
    """Read URLs from the file."""
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def main():
    try:
        # Load configuration
        config = load_config()
        
        # Initialize logger with config
        global logger
        logger = setup_logger(config)
        
        logger.info("Starting RSS fetcher")
        
        # Initialize Supabase client
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            logger.error("Missing Supabase credentials in .env file")
            return
            
        supabase: Client = create_client(url, key)
        
        # Read URLs from configured file
        urls = read_urls(config['rss']['urls_file'])
        logger.info(f"Found {len(urls)} URLs to process")
        
        # Process each URL
        for url in urls:
            logger.info(f"Processing: {url}")
            
            # Get the latest entry date for this source
            latest_date = get_latest_entry_date(supabase, url, config)
            logger.info(f"Fetching entries newer than: {latest_date}")
            
            # Only fetch entries newer than the latest one we have
            entries = fetch_rss(url, latest_date)
            
            if entries:
                try:
                    data = supabase.table("rss_feeds").upsert(
                        entries,
                        on_conflict="link,source_url"
                    ).execute()
                    logger.info(f"Successfully processed {len(entries)} new entries from {url}")
                except Exception as e:
                    logger.error(f"Error saving entries from {url}: {str(e)}")
            else:
                logger.info(f"No new entries found for {url}")
                
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    
    logger.info("RSS fetcher completed")

if __name__ == "__main__":
    main() 