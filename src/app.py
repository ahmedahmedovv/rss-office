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
    return render_template('index.html')

@app.route('/api/entries')
def get_entries():
    # Fetch entries from Supabase with correct table name and columns
    response = supabase.table('rss_feeds').select(
        "title",
        "source_url",  # This is the source
        "category",
        "pub_date"     # This is the published date
    ).order('pub_date', desc=True).execute()
    return jsonify(response.data)

if __name__ == '__main__':
    app.run(debug=True)
