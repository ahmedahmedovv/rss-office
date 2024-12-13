from flask import Flask, render_template, jsonify, request, session
from supabase import create_client
from dotenv import load_dotenv
import os
import uuid
import logging
import sys
import os.path
from functools import lru_cache
import time
from collections import defaultdict

# Configure logging
log_directory = 'log'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_directory, 'app.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here")

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase = create_client(supabase_url, supabase_key)

# In-memory storage for read articles
read_articles = defaultdict(set)

def get_current_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/articles/read', methods=['POST'])
def toggle_read():
    try:
        user_id = get_current_user_id()
        article_link = request.json.get('link')
        
        if not article_link:
            return jsonify({'error': 'Article link required'}), 400
        
        # Toggle read status
        if article_link in read_articles[user_id]:
            read_articles[user_id].remove(article_link)
            is_read = False
        else:
            read_articles[user_id].add(article_link)
            is_read = True
        
        return jsonify({'status': 'success', 'is_read': is_read})
    except Exception as e:
        logger.exception(f"Error in toggle_read: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/read', methods=['GET'])
def get_read_articles():
    try:
        user_id = get_current_user_id()
        return jsonify({'read_articles': list(read_articles[user_id])})
    except Exception as e:
        logger.exception(f"Error in get_read_articles: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/read', methods=['DELETE'])
def clear_read_history():
    try:
        user_id = get_current_user_id()
        read_articles[user_id].clear()
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.exception(f"Error in clear_read_history: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Cache feeds response
_feeds_cache = {'data': None, 'timestamp': 0}
CACHE_DURATION = 300  # 5 minutes

@app.route('/api/feeds')
def get_feeds():
    try:
        current_time = time.time()
        
        # Return cached data if it's still fresh
        if _feeds_cache['data'] and (current_time - _feeds_cache['timestamp'] < CACHE_DURATION):
            return jsonify(_feeds_cache['data'])
        
        response = supabase.table("rss_feeds").select("*").order('pub_date', desc=True).limit(2000).execute()
        
        # Update cache
        _feeds_cache['data'] = response.data
        _feeds_cache['timestamp'] = current_time
        
        return jsonify(response.data)
    except Exception as e:
        logger.exception(f"Error in get_feeds: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
