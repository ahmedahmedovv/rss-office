from flask import Flask, render_template, request
from supabase import create_client
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials in .env file")

supabase = create_client(supabase_url, supabase_key)

@app.route('/')
def index():
    # Get category filter from query parameters
    category = request.args.get('category', None)
    
    # Base query
    query = supabase.table('rss_feeds').select('*').order('pub_date', desc=True)
    
    # Apply category filter if specified
    if category:
        query = query.eq('category', category)
    
    # Execute query
    response = query.execute()
    feeds = response.data

    # Convert pub_date strings to datetime objects
    for feed in feeds:
        feed['pub_date'] = datetime.fromisoformat(feed['pub_date'].replace('Z', '+00:00'))

    # Get unique categories for filter panel
    categories_response = supabase.table('rss_feeds')\
        .select('category')\
        .execute()
    
    # Filter out None values and get unique categories
    unique_categories = sorted(set(item['category'] for item in categories_response.data if item['category']))

    return render_template('index.html', feeds=feeds, categories=unique_categories, selected_category=category)

if __name__ == '__main__':
    app.run(debug=True)
