from flask import Flask, render_template, jsonify
from supabase import create_client
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/feeds')
def get_feeds():
    try:
        response = supabase.table("rss_feeds")\
            .select("""
                id,
                title,
                title_en,
                description,
                description_en,
                link,
                pub_date,
                source_url,
                created_at,
                translated_at,
                summary,
                summarized_at,
                ai_title,
                ai_title_generated_at,
                category,
                category_generated_at
            """)\
            .order('pub_date', desc=True)\
            .limit(500)\
            .execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
