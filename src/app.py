from flask import Flask, render_template, jsonify, request, session
from supabase import create_client
from dotenv import load_dotenv
import os
from src.services.redis_service import RedisService
import uuid
import logging
import sys
import os.path
from functools import lru_cache
import time

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
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

redis_service = RedisService()

# Add cache duration constant
CACHE_DURATION = 300  # 5 minutes

# Add cache for feeds
_feeds_cache = {'data': None, 'timestamp': 0}

def get_current_user_id():
    """
    Get current user ID from session or create a new one.
    In a real application, this would come from your authentication system.
    """
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/feeds')
def get_feeds():
    try:
        current_time = time.time()
        
        # Return cached data if it's still fresh
        if _feeds_cache['data'] and (current_time - _feeds_cache['timestamp'] < CACHE_DURATION):
            return jsonify(_feeds_cache['data'])
        
        response = supabase.table("rss_feeds")\
            .select("*")\
            .order('pub_date', desc=True)\
            .limit(2000)\
            .execute()
        
        # Update cache
        _feeds_cache['data'] = response.data
        _feeds_cache['timestamp'] = current_time
        
        return jsonify(response.data)
    except Exception as e:
        logger.error(f"Error fetching feeds: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/articles/read', methods=['POST'])
def toggle_read():
    try:
        user_id = get_current_user_id()
        logger.info(f"Toggle read request received for user: {user_id}")
        
        article_link = request.json.get('link')
        logger.debug(f"Article link received: {article_link}")
        
        if not article_link:
            logger.error("No article link provided in request")
            return jsonify({'error': 'Article link required'}), 400
        
        logger.info(f"Attempting to toggle read status for article: {article_link}")
        is_read = redis_service.toggle_article_read(user_id, article_link)
        logger.info(f"Toggle successful. New read status: {is_read}")
        
        return jsonify({'status': 'success', 'is_read': is_read})
    except Exception as e:
        logger.exception(f"Error in toggle_read: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/read', methods=['GET'])
def get_read_articles():
    try:
        user_id = get_current_user_id()
        logger.info(f"Fetching read articles for user: {user_id}")
        read_articles = redis_service.get_all_read_articles(user_id)
        logger.debug(f"Found {len(read_articles)} read articles")
        return jsonify({'read_articles': read_articles})
    except Exception as e:
        logger.exception(f"Error in get_read_articles: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/read', methods=['DELETE'])
def clear_read_history():
    user_id = get_current_user_id()
    redis_service.clear_read_history(user_id)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
