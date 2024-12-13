supabase-py
Python client for Supabase

Documentation: supabase.com/docs
Usage:
GitHub OAuth in your Python Flask app
Python data loading with Supabase
Set up a Local Development Environment
Clone the Repository
git clone https://github.com/supabase/supabase-py.git
cd supabase-py
Create and Activate a Virtual Environment
We recommend activating your virtual environment. For example, we like poetry and conda! Click here for more about Python virtual environments and working with conda and poetry.

Using venv (Python 3 built-in):

python3 -m venv env
source env/bin/activate  # On Windows, use .\env\Scripts\activate
Using conda:

conda create --name supabase-py
conda activate supabase-py
PyPi installation
Install the package (for Python >= 3.9):

# with pip
pip install supabase

# with conda
conda install -c conda-forge supabase
Local installation
You can also install locally after cloning this repo. Install Development mode with pip install -e, which makes it editable, so when you edit the source code the changes will be reflected in your python module.

Usage
Set your Supabase environment variables in a dotenv file, or using the shell:

export SUPABASE_URL="my-url-to-my-awesome-supabase-instance"
export SUPABASE_KEY="my-supa-dupa-secret-supabase-api-key"
Init client:

import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
Use the supabase client to interface with your database.

Sign-up
user = supabase.auth.sign_up({ "email": users_email, "password": users_password })
Sign-in
user = supabase.auth.sign_in_with_password({ "email": users_email, "password": users_password })
Insert Data
data = supabase.table("countries").insert({"name":"Germany"}).execute()

# Assert we pulled real data.
assert len(data.data) > 0
Select Data
data = supabase.table("countries").select("*").eq("country", "IL").execute()

# Assert we pulled real data.
assert len(data.data) > 0
Update Data
data = supabase.table("countries").update({"country": "Indonesia", "capital_city": "Jakarta"}).eq("id", 1).execute()
Update data with duplicate keys
country = {
  "country": "United Kingdom",
  "capital_city": "London" # This was missing when it was added
}

data = supabase.table("countries").upsert(country).execute()
assert len(data.data) > 0
Delete Data
data = supabase.table("countries").delete().eq("id", 1).execute()
Call Edge Functions
def test_func():
  try:
    resp = supabase.functions.invoke("hello-world", invoke_options={'body':{}})
    return resp
  except (FunctionsRelayError, FunctionsHttpError) as exception:
    err = exception.to_dict()
    print(err.get("message"))
Download a file from Storage
bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).download("photo1.png")
Upload a file
bucket_name: str = "photos"
new_file = getUserFile()

data = supabase.storage.from_(bucket_name).upload("/user1/profile.png", new_file)
Remove a file
bucket_name: str = "photos"

data = supabase.storage.from_(bucket_name).remove(["old_photo.png", "image5.jpg"])
List all files
bucket_name: str = "charts"

data = supabase.storage.from_(bucket_name).list()
Move and rename files
bucket_name: str = "charts"
old_file_path: str = "generic/graph1.png"
new_file_path: str = "important/revenue.png"

data = supabase.storage.from_(bucket_name).move(old_file_path, new_file_path)
Roadmap