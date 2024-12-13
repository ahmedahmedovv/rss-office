import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    try:
        # Initialize Supabase client using environment variables
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            print("Error: Please set SUPABASE_URL and SUPABASE_KEY in your .env file")
            return
            
        supabase: Client = create_client(url, key)
        
        # Insert "hello world" into a messages table
        data = supabase.table("messages").insert({
            "message": "hello world"
        }).execute()
        
        print("Successfully saved 'hello world' to Supabase!")
        print("Inserted data:", data.data)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
