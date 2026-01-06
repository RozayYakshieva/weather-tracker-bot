import pytest
from unittest.mock import patch, MagicMock
from app.database.db import add_user, add_subscription


@patch("app.database.db.get_db_connection")
def test_add_user_success(mock_get_conn):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur

    result = add_user(12345, "testuser", "TestUser")

    mock_cur.execute.assert_called()
    mock_conn.commit.assert_called()
    assert result is True


@patch("app.database.db.get_db_connection")
@patch("app.database.db.add_user")
def test_add_subscription_success(mock_add_user, mock_get_conn):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cur
    mock_cur.fetchone.side_effect = [(1,), (999,)]  # user_id, subscription_id

    result = add_subscription(12345, "Москва", "08:30")

    assert result == 999
    mock_add_user.assert_called_once_with(12345)