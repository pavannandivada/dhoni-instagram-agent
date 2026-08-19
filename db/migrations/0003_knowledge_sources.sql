CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_system TEXT NOT NULL,
    source_collection TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    source_row_number INTEGER,

    title TEXT,
    content TEXT NOT NULL,

    source_url TEXT,
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
    rights_status TEXT,

    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    normalized_payload JSONB NOT NULL DEFAULT '{}'::jsonb,

    content_hash TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT knowledge_documents_source_unique
        UNIQUE (source_system, source_collection, source_record_id)
);

CREATE INDEX IF NOT EXISTS knowledge_documents_hash_idx
    ON knowledge_documents (content_hash);

CREATE INDEX IF NOT EXISTS knowledge_documents_verification_idx
    ON knowledge_documents (verification_status);

CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id TEXT NOT NULL UNIQUE,
    quote TEXT NOT NULL,
    context TEXT,
    source TEXT,
    source_url TEXT,
    quote_date DATE,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    used_at TIMESTAMPTZ,
    knowledge_document_id UUID UNIQUE
        REFERENCES knowledge_documents(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fact_id TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    fact TEXT NOT NULL,
    format TEXT,
    source TEXT,
    source_url TEXT,
    verified_date DATE,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    used_at TIMESTAMPTZ,
    knowledge_document_id UUID UNIQUE
        REFERENCES knowledge_documents(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id TEXT NOT NULL UNIQUE,
    asset_type TEXT NOT NULL,
    category TEXT,
    drive_file_id TEXT,
    file_name TEXT NOT NULL,
    source_url TEXT,
    creator TEXT,
    license TEXT,
    rights_status TEXT,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    last_used TIMESTAMPTZ,
    aspect_ratio NUMERIC(8,4),
    width INTEGER,
    height INTEGER,
    checksum TEXT,
    knowledge_document_id UUID UNIQUE
        REFERENCES knowledge_documents(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS special_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT NOT NULL UNIQUE,
    event_date DATE NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    source_url TEXT,
    priority INTEGER NOT NULL DEFAULT 0,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    used_at TIMESTAMPTZ,
    knowledge_document_id UUID UNIQUE
        REFERENCES knowledge_documents(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS quotes_verified_unused_idx
    ON quotes (verified, used);

CREATE INDEX IF NOT EXISTS facts_verified_unused_idx
    ON facts (verified, used);

CREATE INDEX IF NOT EXISTS assets_verified_unused_idx
    ON assets (verified, used);

CREATE INDEX IF NOT EXISTS special_events_date_idx
    ON special_events (event_date);
