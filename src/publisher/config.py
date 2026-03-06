import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Required
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

# Optional — scheduler tuning
LINKEDIN_VERSION: str = os.getenv("LINKEDIN_VERSION", "202501")
WORKER_ID: str = os.getenv("WORKER_ID", "local")
MAX_ATTEMPTS: int = int(os.getenv("MAX_ATTEMPTS", "3"))
CLAIM_LIMIT: int = int(os.getenv("CLAIM_LIMIT", "10"))
REQUEUE_BACKOFF_MINUTES: int = int(os.getenv("REQUEUE_BACKOFF_MINUTES", "15"))

# Optional — content generation
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
LINKEDIN_ACCOUNT_LABEL: str = os.getenv("LINKEDIN_ACCOUNT_LABEL", "")

# Optional — Discord
DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_WEBHOOK_DRAFTS: str = os.getenv("DISCORD_WEBHOOK_DRAFTS", "")
DISCORD_WEBHOOK_PUBLISHED: str = os.getenv("DISCORD_WEBHOOK_PUBLISHED", "")
DISCORD_WEBHOOK_ERRORS: str = os.getenv("DISCORD_WEBHOOK_ERRORS", "")
DISCORD_CHANNEL_DRAFTS_ID: str = os.getenv("DISCORD_CHANNEL_DRAFTS_ID", "")
