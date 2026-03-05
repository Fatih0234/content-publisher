-- Enums
CREATE TYPE post_status AS ENUM (
    'queued',
    'publishing',
    'published',
    'failed'
);

CREATE TYPE actor_type AS ENUM (
    'person',
    'organization'
);

-- Tables
CREATE TABLE linkedin_accounts (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    label       text UNIQUE NOT NULL,
    actor_type  actor_type NOT NULL DEFAULT 'person',
    author_urn  text NOT NULL,
    access_token text NOT NULL,
    token_expires_at timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE scheduled_posts (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  uuid NOT NULL REFERENCES linkedin_accounts(id),
    body        text NOT NULL,
    publish_at  timestamptz NOT NULL,
    status      post_status NOT NULL DEFAULT 'queued',
    attempt_count int NOT NULL DEFAULT 0,
    locked_at   timestamptz,
    locked_by   text,
    published_at timestamptz,
    post_urn    text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE publish_attempts (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id     uuid NOT NULL REFERENCES scheduled_posts(id),
    status      post_status NOT NULL,
    http_status int,
    response_snippet text,
    error_message text,
    attempted_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_scheduled_posts_status_publish_at
    ON scheduled_posts (status, publish_at);

CREATE INDEX idx_scheduled_posts_account_status_publish_at
    ON scheduled_posts (account_id, status, publish_at);

-- RPC: claim due posts atomically
CREATE OR REPLACE FUNCTION claim_due_posts(p_limit int, p_worker_id text)
RETURNS SETOF scheduled_posts
LANGUAGE plpgsql
AS $$
DECLARE
    v_ids uuid[];
BEGIN
    -- Select claimable post IDs with row locking
    SELECT array_agg(id) INTO v_ids
    FROM (
        SELECT id
        FROM scheduled_posts
        WHERE status = 'queued'
          AND publish_at <= now()
          AND (locked_at IS NULL OR locked_at < now() - interval '30 minutes')
        ORDER BY publish_at
        LIMIT p_limit
        FOR UPDATE SKIP LOCKED
    ) sub;

    IF v_ids IS NULL OR array_length(v_ids, 1) = 0 THEN
        RETURN;
    END IF;

    -- Claim them
    UPDATE scheduled_posts
    SET status     = 'publishing',
        locked_at  = now(),
        locked_by  = p_worker_id,
        updated_at = now()
    WHERE id = ANY(v_ids);

    RETURN QUERY
        SELECT * FROM scheduled_posts WHERE id = ANY(v_ids);
END;
$$;
