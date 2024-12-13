from flask import Flask, render_template
from supabase import create_client
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@app.route('/')
def index():
    # Fetch RSS feeds from Supabase
    response = supabase.table('rss_feeds')\
        .select('*')\
        .order('pub_date', desc=True)\
        .limit(10000)\
        .execute()
    
    feeds = response.data
    
    # Convert string dates to datetime objects
    for feed in feeds:
        if isinstance(feed['pub_date'], str):
            feed['pub_date'] = datetime.fromisoformat(feed['pub_date'].replace('Z', '+00:00'))
    
    # Prepare categories and counts
    categories = set()
    category_counts = defaultdict(int)
    
    # Count categories
    for feed in feeds:
        category = feed.get('category') or 'uncategorized'
        categories.add(category)
        category_counts[category] += 1
    
    return render_template('index.html', 
                         feeds=feeds,
                         categories=categories,
                         category_counts=dict(category_counts))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
