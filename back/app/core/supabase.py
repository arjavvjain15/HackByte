from supabase import create_client
from app.core.config import get_env


def get_supabase_client():
    url = get_env("SUPABASE_URL")
    key = get_env("SUPABASE_SERVICE_KEY")
    return create_client(url, key)
