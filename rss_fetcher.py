import os
import feedparser
from datetime import datetime
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
    # First decode HTML entities
    text = unescape(text)
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    clean = ' '.join(clean.split())
    return clean.strip()

def read_urls(filename: str) -> List[str]:
    """Read URLs from the file."""
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def fetch_rss(url: str) -> List[dict]:
    """Fetch and parse RSS feed."""
    try:
        feed = feedparser.parse(url)
        entries = []
        
        for entry in feed.entries:
            # Parse publication date
            try:
                pub_date = parser.parse(entry.published)
            except (AttributeError, ValueError):
                pub_date = datetime.now()

            entries.append({
                "title": clean_html(entry.get("title", "")),
                "link": entry.get("link", ""),
                "description": clean_html(entry.get("description", "")),
                "pub_date": pub_date.isoformat(),
                "source_url": url
            })
        
        return entries
    except Exception as e:
        print(f"Error fetching RSS from {url}: {str(e)}")
        return []

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
            print(f"Fetching RSS from: {url}")
            entries = fetch_rss(url)
            
            if entries:
                try:
                    # Use upsert instead of insert to handle duplicates
                    data = supabase.table("rss_feeds").upsert(
                        entries,
                        on_conflict="link,source_url"  # columns that determine uniqueness
                    ).execute()
                    print(f"Processed {len(entries)} entries from {url}")
                except Exception as e:
                    print(f"Error saving entries from {url}: {str(e)}")
            else:
                print(f"No entries found for {url}")
                
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 