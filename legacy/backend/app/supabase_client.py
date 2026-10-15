import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise EnvironmentError(
        "❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file"
    )

# Client for user-facing operations (signup, login)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Admin client for backend operations (optional, uses service role key)
if SUPABASE_SERVICE_KEY:
    supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
else:
    supabase_admin = None
