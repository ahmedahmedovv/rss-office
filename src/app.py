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
    # Get category filter from query parameters
    category = request.args.get('category', None)
    
    # Get ALL feeds first (without category filter)
    all_feeds = supabase.table('rss_feeds')\
        .select('*')\
        .order('pub_date', desc=True)\
        .execute()
    
    # Get read articles for current user
    read_articles = supabase.table('read_articles')\
        .select('feed_id')\
        .eq('user_id', current_user.id)\
        .execute()
    
    read_feed_ids = {item['feed_id'] for item in read_articles.data}
    
    # Calculate unread counts for all categories
    category_counts = {}
    for feed in all_feeds.data:
        if feed['id'] not in read_feed_ids:
            feed_category = feed['category'] or 'Uncategorized'
            category_counts[feed_category] = category_counts.get(feed_category, 0) + 1
    
    # Calculate total unread count
    total_unread = sum(category_counts.values())
    
    # Now filter feeds by category if needed
    if category:
        feeds = [feed for feed in all_feeds.data if feed['category'] == category]
    else:
        feeds = all_feeds.data

    # Convert pub_date strings to datetime objects and add read status
    for feed in feeds:
        feed['pub_date'] = datetime.fromisoformat(feed['pub_date'].replace('Z', '+00:00'))
        feed['is_read'] = feed['id'] in read_feed_ids

    # Get unique categories
    unique_categories = sorted(set(feed['category'] for feed in all_feeds.data if feed['category']))

    return render_template('index.html', 
                         feeds=feeds, 
                         categories=unique_categories, 
                         selected_category=category,
                         category_counts=category_counts,
                         total_unread=total_unread)

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

@app.route('/toggle-read/<int:feed_id>', methods=['POST'])
@login_required
def toggle_read(feed_id):
    try:
        # Check if article is already read
        existing = supabase.table('read_articles')\
            .select('id')\
            .eq('user_id', current_user.id)\
            .eq('feed_id', feed_id)\
            .execute()
        
        if existing.data:
            # If read, delete the record to mark as unread
            supabase.table('read_articles')\
                .delete()\
                .eq('user_id', current_user.id)\
                .eq('feed_id', feed_id)\
                .execute()
            return jsonify({'success': True, 'is_read': False})
        else:
            # If unread, insert record to mark as read
            supabase.table('read_articles').insert({
                'user_id': current_user.id,
                'feed_id': feed_id
            }).execute()
            return jsonify({'success': True, 'is_read': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
