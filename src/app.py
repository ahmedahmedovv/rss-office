from flask import Flask, render_template, jsonify, request, session, send_from_directory
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
    # Add timestamp to force fresh JavaScript files
    timestamp = int(time.time())
    return render_template('index.html', cache_buster=timestamp)

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

@app.route('/api/feeds')
def get_feeds():
    try:
        # Direct database query without caching
        response = supabase.table("rss_feeds") \
                          .select("*") \
                          .order('pub_date', desc=True) \
                          .limit(3000) \
                          .execute()
        
        logger.info(f"Fresh API call returned {len(response.data)} records")
        
        return jsonify({
            'data': response.data,
            'count': len(response.data)
        })
    except Exception as e:
        logger.exception(f"Error in get_feeds: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add a simple test endpoint that returns a single article
@app.route('/api/test-article')
def test_article():
    return jsonify({
        'data': [{
            'id': 1,
            'title': 'Test Article',
            'description': 'This is a test article',
            'link': 'https://example.com',
            'pub_date': '2024-12-13T22:08:00+00:00'
        }],
        'count': 1
    })

@app.route('/api/debug/article-counts')
def debug_article_counts():
    try:
        # Get total count from database
        db_count = supabase.table("rss_feeds").select("count", count='exact').execute()
        
        # Test different limit values
        limit_1000 = supabase.table("rss_feeds").select("*").order('pub_date', desc=True).limit(1000).execute()
        limit_2000 = supabase.table("rss_feeds").select("*").order('pub_date', desc=True).limit(2000).execute()
        
        return jsonify({
            'database_total_count': db_count.count,
            'response_count_limit_1000': len(limit_1000.data),
            'response_count_limit_2000': len(limit_2000.data),
            'cache_age_seconds': time.time() - _feeds_cache['timestamp'] if _feeds_cache['timestamp'] else None,
            'cache_status': 'fresh' if _feeds_cache['data'] and (time.time() - _feeds_cache['timestamp'] < CACHE_DURATION) else 'stale',
            'note': 'If limit_2000 shows 1000, there might be a server-side limit'
        })
    except Exception as e:
        logger.exception(f"Error in debug_article_counts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/detailed-counts')
def debug_detailed_counts():
    try:
        # Get database count
        db_count = supabase.table("rss_feeds").select("count", count='exact').execute()
        
        # Get current cache state
        cache_data = _feeds_cache['data']
        cache_count = len(cache_data) if cache_data else 0
        
        # Get fresh data with different limits
        limit_2000 = supabase.table("rss_feeds").select("*").order('pub_date', desc=True).limit(2000).execute()
        
        # Get data exactly as the main endpoint does
        main_endpoint_data = supabase.table("rss_feeds").select("*").order('pub_date', desc=True).limit(3000).execute()
        
        return jsonify({
            'database_total_count': db_count.count,
            'cache_details': {
                'count': cache_count,
                'age_seconds': time.time() - _feeds_cache['timestamp'] if _feeds_cache['timestamp'] else None,
                'status': 'fresh' if _feeds_cache['data'] and (time.time() - _feeds_cache['timestamp'] < CACHE_DURATION) else 'stale'
            },
            'api_responses': {
                'limit_2000_count': len(limit_2000.data),
                'main_endpoint_count': len(main_endpoint_data.data)
            },
            'first_few_ids': {
                'cache': [item['id'] for item in cache_data[:5]] if cache_data else None,
                'fresh_data': [item['id'] for item in main_endpoint_data.data[:5]] if main_endpoint_data.data else None
            },
            'timestamp_range': {
                'newest': main_endpoint_data.data[0]['pub_date'] if main_endpoint_data.data else None,
                'oldest': main_endpoint_data.data[-1]['pub_date'] if main_endpoint_data.data else None
            }
        })
    except Exception as e:
        logger.exception(f"Error in debug_detailed_counts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/sample-data')
def debug_sample_data():
    try:
        if not _feeds_cache['data']:
            return jsonify({
                'status': 'error',
                'message': 'No data in cache'
            })
            
        # Return first 5 items and data structure info
        sample_data = _feeds_cache['data'][:5]
        return jsonify({
            'total_records': len(_feeds_cache['data']),
            'sample_records': sample_data,
            'data_structure': {
                'keys_available': list(sample_data[0].keys()) if sample_data else [],
                'first_item_preview': sample_data[0] if sample_data else None
            }
        })
    except Exception as e:
        logger.exception(f"Error in debug_sample_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
