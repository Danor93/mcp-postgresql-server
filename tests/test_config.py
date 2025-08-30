import pytest
import os
import psycopg2
from unittest.mock import patch, MagicMock
from src.config.database import get_db_connection

class TestDatabaseConfig:
    
    @patch('src.config.database.psycopg2.connect')
    def test_get_db_connection_uses_env_variables(self, mock_connect):
        """Test get_db_connection uses environment variables for database connection"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'testhost',
            'POSTGRES_DB': 'testdb',
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass'
        }):
            result = get_db_connection()
            
            mock_connect.assert_called_once_with(
                host='testhost',
                database='testdb',
                user='testuser',
                password='testpass',
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            assert result == mock_conn
    
    @patch('src.config.database.psycopg2.connect')
    def test_get_db_connection_default_host(self, mock_connect):
        """Test get_db_connection uses localhost as default host when POSTGRES_HOST not set"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        with patch.dict(os.environ, {
            'POSTGRES_DB': 'testdb',
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass'
        }, clear=True):
            get_db_connection()
            
            args, kwargs = mock_connect.call_args
            assert kwargs['host'] == 'localhost'
    
    @patch('src.config.database.psycopg2.connect')
    def test_get_db_connection_uses_real_dict_cursor(self, mock_connect):
        """Test get_db_connection configures RealDictCursor for JSON-friendly results"""
        mock_connect.return_value = MagicMock()
        
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'test',
            'POSTGRES_DB': 'test',
            'POSTGRES_USER': 'test',
            'POSTGRES_PASSWORD': 'test'
        }):
            get_db_connection()
            
            args, kwargs = mock_connect.call_args
            assert kwargs['cursor_factory'] == psycopg2.extras.RealDictCursor
    
    @patch('src.config.database.psycopg2.connect')
    def test_get_db_connection_handles_connection_error(self, mock_connect):
        """Test get_db_connection properly propagates database connection errors"""
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
        
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'invalid',
            'POSTGRES_DB': 'test',
            'POSTGRES_USER': 'test',
            'POSTGRES_PASSWORD': 'test'
        }):
            with pytest.raises(psycopg2.OperationalError):
                get_db_connection()