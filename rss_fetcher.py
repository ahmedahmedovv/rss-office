import os
import feedparser
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List
from dateutil import parser
import re
from html import unescape

# Load environment variables
load_dotenv()

def clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities."""
    if not text:
        return ""
    text = unescape(text)
    clean = re.sub(r'<[^>]+>', '', text)
    clean = ' '.join(clean.split())
    return clean.strip()

def get_latest_entry_date(supabase: Client, source_url: str) -> datetime:
    """Get the latest publication date for a given source URL."""
    try:
        result = supabase.table("rss_feeds")\
            .select("pub_date")\
            .eq("source_url", source_url)\
            .order("pub_date", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data and result.data[0].get("pub_date"):
            return parser.parse(result.data[0]["pub_date"])
        return datetime.now() - timedelta(days=30)  # Default to 30 days ago if no entries
    except Exception as e:
        print(f"Error getting latest entry date: {str(e)}")
        return datetime.now() - timedelta(days=30)

def fetch_rss(url: str, since_date: datetime) -> List[dict]:
    """Fetch and parse RSS feed, only returning entries newer than since_date."""
    try:
        feed = feedparser.parse(url)
        entries = []
        
        for entry in feed.entries:
            try:
                pub_date = parser.parse(entry.published)
                # Only process entries newer than the latest entry in database
                if pub_date > since_date:
                    entries.append({
                        "title": clean_html(entry.get("title", "")),
                        "link": entry.get("link", ""),
                        "description": clean_html(entry.get("description", "")),
                        "pub_date": pub_date.isoformat(),
                        "source_url": url
                    })
            except (AttributeError, ValueError):
                continue
        
        return entries
    except Exception as e:
        print(f"Error fetching RSS from {url}: {str(e)}")
        return []

def read_urls(filename: str) -> List[str]:
    """Read URLs from the file."""
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def main():
    try:
        # Initialize Supabase client
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            print("Error: Please set SUPABASE_URL and SUPABASE_KEY in your .env file")
            return
            
        supabase: Client = create_client(url, key)
        
        # Read URLs from file
        urls = read_urls('url.md')
        
        # Process each URL
        for url in urls:
            print(f"Checking RSS from: {url}")
            
            # Get the latest entry date for this source
            latest_date = get_latest_entry_date(supabase, url)
            print(f"Fetching entries newer than: {latest_date}")
            
            # Only fetch entries newer than the latest one we have
            entries = fetch_rss(url, latest_date)
            
            if entries:
                try:
                    data = supabase.table("rss_feeds").upsert(
                        entries,
                        on_conflict="link,source_url"
                    ).execute()
                    print(f"Processed {len(entries)} new entries from {url}")
                except Exception as e:
                    print(f"Error saving entries from {url}: {str(e)}")
            else:
                print(f"No new entries found for {url}")
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 