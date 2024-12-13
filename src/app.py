from flask import Flask, jsonify, render_template
from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

@app.route('/')
def index():
    # Fetch categories for sidebar
    categories_response = supabase.table('rss_feeds')\
        .select('category')\
        .not_.is_('category', None)\
        .execute()
    
    # Extract unique categories
    categories = sorted(set(entry['category'] for entry in categories_response.data if entry['category']))
    
    # Since we don't have read_status, we'll just return the categories without unread counts
    return render_template('index.html', 
                         categories=categories)

@app.route('/api/entries')
def get_entries():
    # Add ai_title and link to the selected fields
    response = supabase.table('rss_feeds').select(
        "category",
        "summary",
        "ai_title",
        "link"
    ).order('pub_date', desc=True).execute()
    
    return jsonify(response.data)

@app.route('/get_articles')
def get_articles():
    try:
        # Fetch all articles with complete information
        response = supabase.table('rss_feeds').select(
            "*"
        ).order('optimized_at', desc=True).execute()
        
        return jsonify({
            "status": "success",
            "data": response.data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
