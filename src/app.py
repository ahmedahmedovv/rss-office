from flask import Flask, render_template, request, jsonify
from flask_login import (
    LoginManager, 
    UserMixin, 
    current_user, 
    login_required, 
    login_user
)
from supabase import create_client
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Simple User class
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# This keeps track of the current user
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials in .env file")

supabase = create_client(supabase_url, supabase_key)

@app.route('/')
def index():
    # For testing purposes, create a dummy user if none exists
    if not current_user.is_authenticated:
        test_user = User("test_user_1")
        login_user(test_user)
    
    # Get category filter from query parameters
    category = request.args.get('category', None)
    
    # Base query
    query = supabase.table('rss_feeds').select('*').order('pub_date', desc=True)
    
    if category:
        query = query.eq('category', category)
    
    response = query.execute()
    feeds = response.data

    # Get read articles for current user
    read_articles = supabase.table('read_articles')\
        .select('feed_id')\
        .eq('user_id', current_user.id)\
        .execute()
    
    read_feed_ids = {item['feed_id'] for item in read_articles.data}
    
    # Convert pub_date strings to datetime objects and add read status
    for feed in feeds:
        feed['pub_date'] = datetime.fromisoformat(feed['pub_date'].replace('Z', '+00:00'))
        feed['is_read'] = feed['id'] in read_feed_ids

    # Get unique categories
    categories_response = supabase.table('rss_feeds')\
        .select('category')\
        .execute()
    
    unique_categories = sorted(set(item['category'] for item in categories_response.data if item['category']))

    return render_template('index.html', feeds=feeds, categories=unique_categories, selected_category=category)

@app.route('/mark-read/<int:feed_id>', methods=['POST'])
@login_required
def mark_read(feed_id):
    try:
        supabase.table('read_articles').insert({
            'user_id': current_user.id,
            'feed_id': feed_id
        }).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
