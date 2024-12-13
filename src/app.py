from flask import Flask, jsonify, render_template, request
from supabase import create_client
from dotenv import load_dotenv
from functools import wraps
import os
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")

# Initialize Supabase client
try:
    supabase = create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
    )
except Exception as e:
    print(f"Failed to initialize Supabase: {e}")
    exit(1)

# Rate limiting decorator
def rate_limit(limit=30, window=60):
    requests = {}
    
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = time.time()
            client_ip = request.remote_addr
            
            # Clean old requests
            requests[client_ip] = [req for req in requests.get(client_ip, []) 
                                 if now - req < window]
            
            if len(requests.get(client_ip, [])) >= limit:
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            requests.setdefault(client_ip, []).append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

@app.route('/')
@rate_limit()
def index():
    try:
        categories_response = supabase.table('rss_feeds')\
            .select('category')\
            .not_.is_('category', None)\
            .execute()
        
        categories = sorted(set(entry['category'] for entry in categories_response.data if entry['category']))
        return render_template('index.html', categories=categories)
    except Exception as e:
        app.logger.error(f"Error fetching categories: {e}")
        return render_template('index.html', categories=[], error="Failed to load categories")

@app.route('/api/entries')
@rate_limit()
def get_entries():
    try:
        # Get pagination parameters
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(50, int(request.args.get('per_page', 20)))
        category = request.args.get('category')
        sort_order = request.args.get('sort', 'desc')
        
        # Build query
        query = supabase.table('rss_feeds').select(
            "category",
            "summary",
            "ai_title",
            "link",
            "pub_date"
        )
        
        # Apply filters
        if category and category != 'all':
            query = query.eq('category', category)
            
        # Apply sorting
        query = query.order('pub_date', desc=(sort_order == 'desc'))
        
        # Apply pagination
        query = query.range(
            (page - 1) * per_page,
            page * per_page - 1
        )
        
        # Execute query
        response = query.execute()
        
        return jsonify({
            "status": "success",
            "data": response.data,
            "page": page,
            "per_page": per_page,
            "total": len(response.data)  # In production, you'd want a separate count query
        })
    except Exception as e:
        app.logger.error(f"Error fetching entries: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to fetch entries"
        }), 500

@app.route('/api/check-updates')
@rate_limit(limit=60)  # Allow more frequent checks
def check_updates():
    try:
        last_update = request.args.get('last_update')
        if last_update:
            # Check for new entries since last update
            query = supabase.table('rss_feeds')\
                .select("count")\
                .gt('pub_date', last_update)\
                .execute()
            return jsonify({
                "status": "success",
                "new_entries": len(query.data)
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=os.environ.get("FLASK_ENV") == "development")
