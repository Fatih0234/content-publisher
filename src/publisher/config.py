import os
from dotenv import load_dotenv

load_dotenv(override=True)

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
LINKEDIN_VERSION: str = os.getenv("LINKEDIN_VERSION", "202501")
WORKER_ID: str = os.getenv("WORKER_ID", "local")
MAX_ATTEMPTS: int = int(os.getenv("MAX_ATTEMPTS", "3"))
CLAIM_LIMIT: int = int(os.getenv("CLAIM_LIMIT", "10"))
REQUEUE_BACKOFF_MINUTES: int = 15
