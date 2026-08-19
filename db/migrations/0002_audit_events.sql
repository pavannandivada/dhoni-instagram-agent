-- A durable, append-only baseline for platform-level operational events.
CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS audit_events_subject_idx
    ON audit_events (subject_type, subject_id, created_at DESC);

CREATE INDEX IF NOT EXISTS audit_events_event_type_idx
    ON audit_events (event_type, created_at DESC);
