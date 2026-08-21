CREATE TABLE content_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id TEXT NOT NULL UNIQUE,
    scheduled_date DATE,
    scheduled_time TIME,
    content_type TEXT NOT NULL,
    topic TEXT,
    quote_stat TEXT,
    source_url TEXT,
    asset_id TEXT,
    caption TEXT,
    overlay_text TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    published BOOLEAN NOT NULL DEFAULT FALSE,
    instagram_media_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX content_calendar_status_idx
    ON content_calendar (status);

CREATE INDEX content_calendar_scheduled_idx
    ON content_calendar (scheduled_date, scheduled_time);
