import pytest

from dhoni_instagram_agent.rag.generator import GroundedGenerator


def test_clean_caption_accepts_two_complete_sentences() -> None:
    caption = "MS Dhoni led India with calm determination. His leadership remains memorable."

    assert GroundedGenerator._clean_caption(caption) == caption


def test_clean_caption_rejects_truncated_sentence() -> None:
    with pytest.raises(RuntimeError, match="complete sentences"):
        GroundedGenerator._clean_caption("MS Dhoni is known for his leadership of India. He")


def test_clean_caption_rejects_single_sentence() -> None:
    with pytest.raises(RuntimeError, match="complete sentences"):
        GroundedGenerator._clean_caption("MS Dhoni is known for his leadership of India.")
