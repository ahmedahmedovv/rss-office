from flask import Flask, jsonify
import os
from datetime import datetime
import pytz

app = Flask(__name__)

@app.route('/')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(pytz.UTC).isoformat(),
        "service": "rss-feed-processor"
    }), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint for uptime monitoring"""
    return "pong", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 