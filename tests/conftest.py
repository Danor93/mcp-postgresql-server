import pytest
import os
import tempfile
import psycopg2
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def app_context():
    with app.app_context():
        yield app

@pytest.fixture
def mock_db_connection():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor

@pytest.fixture
def sample_user():
    return {
        'id': 1,
        'username': 'test_user',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'created_at': '2024-01-01 00:00:00',
        'updated_at': '2024-01-01 00:00:00'
    }

@pytest.fixture
def sample_users():
    return [
        {
            'id': 1,
            'username': 'john_doe',
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        },
        {
            'id': 2,
            'username': 'jane_smith',
            'email': 'jane@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith'
        }
    ]