-- Enums
CREATE TYPE x_post_status AS ENUM (
    'queued',
    'publishing',
    'published',
    'failed',
    'canceled'
);

-- Tables
CREATE TABLE x_accounts (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    label                text UNIQUE NOT NULL,
    username             text NOT NULL,
    user_id              text NOT NULL,
    consumer_key         text NOT NULL,
    consumer_secret      text NOT NULL,
    access_token         text NOT NULL,
    access_token_secret  text NOT NULL,
    is_active            boolean NOT NULL DEFAULT true,
    created_at           timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE x_scheduled_posts (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id    uuid NOT NULL REFERENCES x_accounts(id),
    text          text NOT NULL,
    publish_at    timestamptz NOT NULL,
    status        x_post_status NOT NULL DEFAULT 'queued',
    locked_at     timestamptz,
    locked_by     text,
    x_tweet_id    text,
    last_error    text,
    attempt_count int NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE x_publish_attempts (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id          uuid NOT NULL REFERENCES x_scheduled_posts(id),
    attempted_at     timestamptz NOT NULL DEFAULT now(),
    status           x_post_status NOT NULL,
    http_status      int,
    response_snippet text,
    error_message    text
);

-- Indexes
CREATE INDEX idx_x_scheduled_posts_status_publish_at
    ON x_scheduled_posts (status, publish_at);

CREATE INDEX idx_x_scheduled_posts_account_status_publish_at
    ON x_scheduled_posts (account_id, status, publish_at);

-- RPC: claim due X posts atomically
CREATE OR REPLACE FUNCTION x_claim_due_posts(p_limit int, p_worker_id text)
RETURNS SETOF x_scheduled_posts
LANGUAGE plpgsql
AS $$
DECLARE
    v_ids uuid[];
BEGIN
    SELECT array_agg(id) INTO v_ids
    FROM (
        SELECT id
        FROM x_scheduled_posts
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

    UPDATE x_scheduled_posts
    SET status     = 'publishing',
        locked_at  = now(),
        locked_by  = p_worker_id,
        updated_at = now()
    WHERE id = ANY(v_ids);

    RETURN QUERY
        SELECT * FROM x_scheduled_posts WHERE id = ANY(v_ids);
END;
$$;
