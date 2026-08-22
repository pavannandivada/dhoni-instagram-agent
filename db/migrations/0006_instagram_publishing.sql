ALTER TABLE content_calendar
    ADD COLUMN IF NOT EXISTS instagram_creation_id TEXT;

CREATE INDEX IF NOT EXISTS content_calendar_instagram_creation_idx
    ON content_calendar (instagram_creation_id);
