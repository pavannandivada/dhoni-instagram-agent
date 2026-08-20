from dhoni_instagram_agent.ingestion.hashing import content_hash


def test_content_hash_is_order_independent() -> None:
    first = {"quote": "Hello", "source": "Interview"}
    second = {"source": "Interview", "quote": "Hello"}

    assert content_hash(first) == content_hash(second)


def test_content_hash_changes_when_content_changes() -> None:
    first = {"quote": "Hello"}
    second = {"quote": "Hello world"}

    assert content_hash(first) != content_hash(second)
