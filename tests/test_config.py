"""
Unit Tests - Database Configuration

These unit tests verify the database configuration module works correctly in isolation.
The tests focus on the get_db_connection() function which handles database connectivity
setup, environment variable processing, and connection parameter configuration.

Run these tests with:
    pytest tests/test_config.py -v
    pytest -m unit
    pytest -m "unit and not slow"

What makes these Unit Tests:
    - Test single configuration function in isolation
    - Mock psycopg2.connect to avoid real database connections
    - Fast execution with no external dependencies
    - Test various environment variable configurations
    - Verify connection parameter handling and defaults

Key Testing Patterns:
    - Mock psycopg2.connect directly
    - Use patch.dict to modify environment variables safely
    - Test both success and error scenarios
    - Verify connection parameters are passed correctly
    - Check default value handling
"""

import pytest
import os
import psycopg2
from unittest.mock import patch, MagicMock
from src.config.database import get_db_connection


@pytest.mark.unit
class TestDatabaseConfig:
    """
    Unit tests for database configuration functionality.
    
    These tests verify that the database connection function correctly
    reads environment variables, applies defaults, and configures
    the PostgreSQL connection with appropriate parameters.
    """
    
    @pytest.mark.unit
    @patch('src.config.database.psycopg2.connect')
    def test_get_db_connection_uses_env_variables(self, mock_connect):
        """
        Unit Test: get_db_connection with environment variables
        
        Tests: get_db_connection() -> psycopg2.connection
        Input: Environment variables set for all database parameters
        Mocks: psycopg2.connect returning a mock connection
        
        Verifies:
        - Function reads all environment variables correctly
        - Connection parameters are passed to psycopg2.connect
        - RealDictCursor is configured for JSON-friendly results
        - Returns the database connection object
        
        Expected behavior:
        - Reads POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
        - Calls psycopg2.connect with exact parameter values
        - Configures cursor_factory for dictionary-style results
        """
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
    
    @pytest.mark.unit
    @patch('src.config.database.psycopg2.connect')
    def test_get_db_connection_default_host(self, mock_connect):
        """
        Unit Test: get_db_connection with default host
        
        Tests: get_db_connection() -> psycopg2.connection
        Input: Environment variables without POSTGRES_HOST
        Mocks: psycopg2.connect with localhost default
        
        Verifies:
        - Function uses 'localhost' when POSTGRES_HOST is not set
        - Other environment variables are read correctly
        - Connection parameters include default host value
        - Function handles missing environment variables gracefully
        
        Expected behavior:
        - Defaults to host='localhost' when POSTGRES_HOST not in environment
        - Still reads other required environment variables
        - Maintains proper connection configuration
        """
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
    
    @pytest.mark.unit
    @patch('src.config.database.psycopg2.connect')
    def test_get_db_connection_uses_real_dict_cursor(self, mock_connect):
        """
        Unit Test: get_db_connection cursor factory configuration
        
        Tests: get_db_connection() -> psycopg2.connection
        Input: Standard environment variables
        Mocks: psycopg2.connect to verify cursor_factory parameter
        
        Verifies:
        - Function configures RealDictCursor as cursor factory
        - This enables dictionary-style access to query results
        - Cursor factory is passed correctly to psycopg2.connect
        - Configuration supports JSON serialization of results
        
        Expected behavior:
        - Sets cursor_factory=psycopg2.extras.RealDictCursor
        - Enables row['column_name'] syntax instead of row[0]
        - Facilitates JSON response formatting in API endpoints
        """
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
    
    @pytest.mark.unit
    @patch('src.config.database.psycopg2.connect')
    def test_get_db_connection_handles_connection_error(self, mock_connect):
        """
        Unit Test: get_db_connection error handling
        
        Tests: get_db_connection() -> raises psycopg2.OperationalError
        Input: Valid environment variables
        Mocks: psycopg2.connect raising connection error
        
        Verifies:
        - Function properly propagates database connection errors
        - OperationalError is raised when connection fails
        - No error handling masks the underlying database issue
        - Function doesn't catch or transform connection errors
        
        Expected behavior:
        - When psycopg2.connect fails, exception is propagated
        - Calling code can handle connection errors appropriately
        - No silent failures or generic error masking
        
        Note: This tests error propagation, not error handling
        """
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
        
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'invalid',
            'POSTGRES_DB': 'test',
            'POSTGRES_USER': 'test',
            'POSTGRES_PASSWORD': 'test'
        }):
            with pytest.raises(psycopg2.OperationalError):
                get_db_connection()