-- Drop publishing infrastructure (no longer needed)
DROP FUNCTION IF EXISTS x_claim_due_posts(int, text);
DROP TABLE IF EXISTS x_publish_attempts;
DROP TABLE IF EXISTS x_scheduled_posts;
DROP TABLE IF EXISTS x_accounts;
DROP TYPE IF EXISTS x_post_status;

-- Simple suggestions table
CREATE TYPE x_suggestion_status AS ENUM ('pending', 'published', 'rejected');

CREATE TABLE x_suggestions (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    text       text NOT NULL,
    notes      text,
    status     x_suggestion_status NOT NULL DEFAULT 'pending',
    created_at timestamptz NOT NULL DEFAULT now()
);
