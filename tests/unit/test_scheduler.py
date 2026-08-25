from unittest.mock import MagicMock, patch

from dhoni_instagram_agent.api import app


def test_publish_due_endpoint_returns_no_due_post() -> None:
    connection = MagicMock()
    connection.__enter__.return_value = connection

    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.fetchone.return_value = None

    connection.cursor.return_value = cursor

    with patch("psycopg.connect", return_value=connection):
        result = app.publish_due_instagram_post()

    assert result["status"] == "NO_DUE_POST"
