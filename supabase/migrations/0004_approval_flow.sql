-- Add approval statuses to post_status enum
ALTER TYPE post_status ADD VALUE IF NOT EXISTS 'pending_approval';
ALTER TYPE post_status ADD VALUE IF NOT EXISTS 'rejected';

-- Add discord_message_id to scheduled_posts
ALTER TABLE scheduled_posts ADD COLUMN IF NOT EXISTS discord_message_id text;

-- Add discord_message_id to x_suggestions
ALTER TABLE x_suggestions ADD COLUMN IF NOT EXISTS discord_message_id text;

-- Track processed content URLs to avoid duplicates
CREATE TABLE IF NOT EXISTS processed_content (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url   text UNIQUE NOT NULL,
    processed_at timestamptz NOT NULL DEFAULT now()
);
