"""
pytest Configuration and Shared Fixtures

This file contains pytest configuration and shared fixtures that are automatically
available to all test files in the test suite. The conftest.py file is a special
pytest file that pytest automatically discovers and loads, making all fixtures
defined here available across the entire test suite without explicit imports.

Purpose:
    - Provide reusable test fixtures across all test files
    - Configure Flask test client for HTTP endpoint testing
    - Supply consistent test data for database operations
    - Set up mock objects and application contexts
    - Eliminate code duplication in test setup

Key pytest Concepts Demonstrated:
    - @pytest.fixture: Creates reusable test setup code
    - Fixture scope: How long fixtures live (function, class, module, session)
    - Fixture yielding: Providing setup and teardown in one fixture
    - Automatic fixture discovery: Available without explicit imports

Usage in Tests:
    def test_something(client, sample_user):
        # 'client' and 'sample_user' fixtures are automatically injected
        # No need to import or create them in individual test files

Benefits:
    - DRY principle: Don't Repeat Yourself in test setup
    - Consistency: All tests use the same test data structures
    - Maintainability: Change test data in one place affects all tests
    - Clean test code: Tests focus on logic, not setup
"""

import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    """
    Flask Test Client Fixture
    
    Provides a configured Flask test client for making HTTP requests in tests.
    This fixture is essential for integration tests that need to test HTTP endpoints.
    
    Configuration:
    - Sets TESTING=True to enable Flask test mode
    - Disables error catching so exceptions are visible in tests
    - Provides app context for the entire test session
    
    Usage:
        def test_health_endpoint(client):
            response = client.get('/health')
            assert response.status_code == 200
    
    Scope: Function (new client for each test)
    Returns: Flask test client with application context
    
    Technical Details:
    - Uses Flask's built-in test_client() for HTTP simulation
    - Maintains application context throughout test execution
    - Enables testing of routes, middleware, and error handling
    - Supports all HTTP methods (GET, POST, PUT, DELETE, etc.)
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def app_context():
    """
    Flask Application Context Fixture
    
    Provides Flask application context for tests that need to access
    Flask application features without making HTTP requests.
    
    Use Cases:
    - Testing functions that require Flask application context
    - Accessing Flask configuration in tests
    - Testing utilities that depend on Flask's global objects
    - Unit testing Flask-dependent code without HTTP layer
    
    Usage:
        def test_some_flask_function(app_context):
            # Can access Flask globals like current_app, g, etc.
            result = some_function_that_needs_flask_context()
            assert result is not None
    
    Scope: Function (new context for each test)
    Returns: Flask application instance with active context
    
    Difference from 'client' fixture:
    - 'client': For HTTP endpoint testing (integration tests)
    - 'app_context': For Flask-dependent unit tests
    """
    with app.app_context():
        yield app


@pytest.fixture
def mock_db_connection():
    """
    Database Connection Mock Fixture
    
    Provides pre-configured mock database connection and cursor objects
    for tests that need to mock database interactions.
    
    Components:
    - mock_conn: Mock database connection object
    - mock_cursor: Mock database cursor object
    - Proper connection/cursor relationship setup
    
    Usage:
        def test_database_function(mock_db_connection):
            mock_conn, mock_cursor = mock_db_connection
            mock_cursor.fetchone.return_value = {'id': 1, 'name': 'test'}
            
            # Test code that uses database
            result = some_database_function()
            
            # Verify database interactions
            mock_cursor.execute.assert_called_once()
    
    Scope: Function (fresh mocks for each test)
    Returns: Tuple of (mock_connection, mock_cursor)
    
    Benefits:
    - Consistent mock setup across tests
    - Eliminates repetitive mock creation code
    - Ensures proper mock object relationships
    - Simplifies database testing patterns
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def sample_user():
    """
    Sample User Data Fixture
    
    Provides a consistent, realistic user record for testing database operations
    and API responses. This fixture represents a typical user entity with all
    standard fields populated.
    
    Data Structure:
    - id: Primary key (integer)
    - username: Unique username string
    - email: Valid email address format
    - first_name: User's first name
    - last_name: User's last name  
    - created_at: Timestamp string (ISO format)
    - updated_at: Timestamp string (ISO format)
    
    Usage:
        def test_user_creation(sample_user):
            # sample_user contains realistic test data
            assert sample_user['username'] == 'test_user'
            assert sample_user['email'] == 'test@example.com'
    
    Use Cases:
    - Testing CRUD operations with realistic data
    - Verifying API response structures
    - Setting up test scenarios with known data
    - Database operation validation
    
    Scope: Function (same data for each test, but independent instances)
    Returns: Dictionary representing a user record
    
    Design Principles:
    - Realistic data that could exist in production
    - All fields populated (tests edge cases separately)
    - Consistent across all tests for predictable behavior
    - Easy to understand and maintain
    """
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
    """
    Sample Users List Fixture
    
    Provides a list of multiple user records for testing operations that work
    with multiple entities, such as listing users, bulk operations, and
    multi-user scenarios.
    
    Data Contains:
    - Two distinct user records with different data
    - Realistic names and email addresses
    - Sequential IDs for database-like behavior
    - Varied data to test different scenarios
    
    Usage:
        def test_get_all_users(sample_users):
            # sample_users is a list of user dictionaries
            assert len(sample_users) == 2
            assert sample_users[0]['username'] == 'john_doe'
            assert sample_users[1]['username'] == 'jane_smith'
    
    Use Cases:
    - Testing list/query operations that return multiple records
    - Verifying pagination and filtering functionality
    - Testing bulk operations and batch processing
    - Multi-user scenario testing
    - Ensuring consistent test data for list-based operations
    
    Scope: Function (fresh list for each test)
    Returns: List of dictionaries, each representing a user record
    
    Relationship to sample_user fixture:
    - sample_user: Single user for individual operations
    - sample_users: Multiple users for collection operations
    - Both use similar data structures for consistency
    
    Design Considerations:
    - Small but sufficient data set (2 users)
    - Different names to avoid confusion in tests
    - Realistic data that represents typical use cases
    - Easy to extend if more users needed for specific tests
    """
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

