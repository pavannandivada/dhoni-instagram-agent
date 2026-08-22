CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    knowledge_document_id UUID NOT NULL
        REFERENCES knowledge_documents(id)
        ON DELETE CASCADE,

    embedding_model TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    content_hash TEXT NOT NULL,

    embedding VECTOR(768) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT knowledge_embeddings_document_model_unique
        UNIQUE (
            knowledge_document_id,
            embedding_model
        )
);

CREATE INDEX IF NOT EXISTS knowledge_embeddings_cosine_idx
    ON knowledge_embeddings
    USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS knowledge_embeddings_hash_idx
    ON knowledge_embeddings (content_hash);
