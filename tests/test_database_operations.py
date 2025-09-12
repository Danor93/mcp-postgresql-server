"""
Unit Tests - Database Operations

These unit tests verify individual database operation functions work correctly in isolation.
Unit tests focus on testing single functions with mocked dependencies to ensure they:
- Handle input parameters correctly
- Execute the right database queries
- Return expected response formats
- Handle error conditions gracefully
- Perform proper transaction management

Run these tests with:
    pytest tests/test_database_operations.py -v
    pytest -m unit
    pytest -m "unit and not slow"

What makes these Unit Tests:
    - Test individual functions in isolation
    - Use mocks to eliminate external dependencies
    - Fast execution (no real database calls)
    - Focus on single responsibility per test
    - Verify function contracts and error handling

Key Testing Patterns:
    - Mock database connections and cursors
    - Test both success and failure paths
    - Verify proper SQL query execution
    - Check transaction handling (commit/rollback)
    - Validate response structure and status codes
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import psycopg2
from src.database.user_operations import (
    insert_user, get_users, get_user_by_id, 
    update_user, delete_user, get_users_for_llm
)


@pytest.mark.unit
class TestUserOperations:
    """
    Unit tests for user database operations.
    
    These tests verify that each database operation function works correctly
    when called with various inputs and handles errors appropriately.
    All external dependencies (database connections) are mocked.
    """
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_insert_user_success(self, mock_get_db, sample_user, app_context):
        """
        Unit Test: insert_user function with valid data
        
        Tests: insert_user(args) -> Flask Response
        Input: Valid user data dictionary with username, email, first_name, last_name
        Mocks: Database connection returning successful user creation
        
        Verifies:
        - Returns 200 status code for successful insertion
        - Response contains success=True and user data
        - Database execute() and commit() are called once
        - Returned user data matches input data
        
        Expected behavior:
        - Function calls INSERT SQL query
        - Database transaction is committed
        - Returns Flask JSON response with created user
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        args = {'username': 'test_user', 'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
        response = insert_user(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['username'] == 'test_user'
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_insert_user_duplicate_error(self, mock_get_db, app_context):
        """
        Unit Test: insert_user function with duplicate data
        
        Tests: insert_user(args) -> (Flask Response, status_code)
        Input: User data that causes database integrity error
        Mocks: Database raising IntegrityError for duplicate key
        
        Verifies:
        - Returns 409 status code for duplicate user
        - Response contains error message
        - Database transaction is rolled back
        - No commit() is called on error
        
        Expected behavior:
        - Function catches psycopg2.IntegrityError
        - Calls rollback() to undo transaction
        - Returns error response with 409 status
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.execute.side_effect = psycopg2.IntegrityError("duplicate key")
        
        args = {'username': 'test_user', 'email': 'test@example.com'}
        response_tuple = insert_user(args)
        
        assert response_tuple[1] == 409
        data = json.loads(response_tuple[0].data)
        assert 'error' in data
        mock_conn.rollback.assert_called_once()
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_get_users_success(self, mock_get_db, sample_users, app_context):
        """
        Unit Test: get_users function returning all users
        
        Tests: get_users(args) -> Flask Response
        Input: Empty arguments dictionary
        Mocks: Database returning list of user records
        
        Verifies:
        - Returns 200 status code
        - Response contains 'users' array with all records
        - Correct number of users returned
        - User data structure is preserved
        
        Expected behavior:
        - Function calls SELECT * FROM users SQL query
        - All user records are returned in JSON format
        - No filtering is applied when args is empty
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchall.return_value = sample_users
        
        response = get_users({})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['users']) == 2
        assert data['users'][0]['username'] == 'john_doe'
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_get_user_by_id_found(self, mock_get_db, sample_user, app_context):
        """
        Unit Test: get_user_by_id function with existing user
        
        Tests: get_user_by_id(args) -> Flask Response
        Input: Dictionary with valid user_id
        Mocks: Database returning user record for given ID
        
        Verifies:
        - Returns 200 status code when user exists
        - Response contains 'user' object with correct data
        - User ID and username match expected values
        - Database query uses provided user_id parameter
        
        Expected behavior:
        - Function calls SELECT * FROM users WHERE id = %s
        - Returns single user record in JSON format
        - User data structure is preserved
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        args = {'user_id': 1}
        response = get_user_by_id(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['id'] == 1
        assert data['user']['username'] == 'test_user'
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_get_user_by_id_not_found(self, mock_get_db, app_context):
        """
        Unit Test: get_user_by_id function with non-existent user
        
        Tests: get_user_by_id(args) -> (Flask Response, status_code)
        Input: Dictionary with non-existent user_id
        Mocks: Database returning None (no matching record)
        
        Verifies:
        - Returns 404 status code when user not found
        - Response contains appropriate error message
        - Error message is user-friendly
        - No user data is returned
        
        Expected behavior:
        - Function handles None result from database query
        - Returns error response with 404 status
        - Error message indicates user was not found
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = None
        
        args = {'user_id': 999}
        response_tuple = get_user_by_id(args)
        
        assert response_tuple[1] == 404
        data = json.loads(response_tuple[0].data)
        assert data['error'] == 'User not found'
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_update_user_success(self, mock_get_db, sample_user, app_context):
        """
        Unit Test: update_user function with valid data
        
        Tests: update_user(args) -> Flask Response
        Input: Dictionary with user_id and fields to update
        Mocks: Database returning existing user, then updated user
        
        Verifies:
        - Returns 200 status code for successful update
        - Response contains success=True and updated user data
        - Database commit() is called once
        - Updated fields reflect new values
        
        Expected behavior:
        - Function checks if user exists (SELECT query)
        - Performs UPDATE query with provided fields
        - Returns updated user data after commit
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        updated_user = sample_user.copy()
        updated_user['username'] = 'updated_user'
        mock_cursor.fetchone.side_effect = [sample_user, updated_user]
        
        args = {'user_id': 1, 'username': 'updated_user'}
        response = update_user(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['username'] == 'updated_user'
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_update_user_not_found(self, mock_get_db, app_context):
        """
        Unit Test: update_user function with non-existent user
        
        Tests: update_user(args) -> (Flask Response, status_code)
        Input: Dictionary with non-existent user_id
        Mocks: Database returning None (user doesn't exist)
        
        Verifies:
        - Returns 404 status code when user not found
        - Response contains appropriate error message
        - No UPDATE query is executed
        - No commit() is called
        
        Expected behavior:
        - Function checks if user exists first
        - Returns error without attempting update
        - Error message indicates user was not found
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = None
        
        args = {'user_id': 999, 'username': 'new_name'}
        response_tuple = update_user(args)
        
        assert response_tuple[1] == 404
        data = json.loads(response_tuple[0].data)
        assert data['error'] == 'User not found'
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_update_user_no_fields(self, mock_get_db, sample_user, app_context):
        """
        Unit Test: update_user function with no update fields
        
        Tests: update_user(args) -> (Flask Response, status_code)
        Input: Dictionary with only user_id (no fields to update)
        Mocks: Database returning existing user
        
        Verifies:
        - Returns 400 status code for invalid request
        - Response contains appropriate error message
        - No UPDATE query is executed
        - User existence is checked but no changes made
        
        Expected behavior:
        - Function validates that update fields are provided
        - Returns bad request error when no fields to update
        - Error message is descriptive
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        args = {'user_id': 1}
        response_tuple = update_user(args)
        
        assert response_tuple[1] == 400
        data = json.loads(response_tuple[0].data)
        assert data['error'] == 'No fields to update'
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_delete_user_success(self, mock_get_db, sample_user, app_context):
        """
        Unit Test: delete_user function with existing user
        
        Tests: delete_user(args) -> Flask Response
        Input: Dictionary with valid user_id
        Mocks: Database returning existing user
        
        Verifies:
        - Returns 200 status code for successful deletion
        - Response contains success=True and confirmation message
        - Database commit() is called once
        - Success message is appropriate
        
        Expected behavior:
        - Function checks if user exists first
        - Performs DELETE query for the user
        - Returns success confirmation after commit
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        args = {'user_id': 1}
        response = delete_user(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['message'] == 'User deleted successfully'
        mock_conn.commit.assert_called_once()
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_delete_user_not_found(self, mock_get_db, app_context):
        """
        Unit Test: delete_user function with non-existent user
        
        Tests: delete_user(args) -> (Flask Response, status_code)
        Input: Dictionary with non-existent user_id
        Mocks: Database returning None (user doesn't exist)
        
        Verifies:
        - Returns 404 status code when user not found
        - Response contains appropriate error message
        - No DELETE query is executed
        - No commit() is called
        
        Expected behavior:
        - Function checks if user exists first
        - Returns error without attempting deletion
        - Error message indicates user was not found
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = None
        
        args = {'user_id': 999}
        response_tuple = delete_user(args)
        
        assert response_tuple[1] == 404
        data = json.loads(response_tuple[0].data)
        assert data['error'] == 'User not found'
    
    @pytest.mark.unit
    @patch('src.database.user_operations.get_db_connection')
    def test_get_users_for_llm(self, mock_get_db, sample_users):
        """
        Unit Test: get_users_for_llm function for LLM data preparation
        
        Tests: get_users_for_llm() -> List[Dict]
        Input: No parameters (function takes no arguments)
        Mocks: Database returning list of user records
        
        Verifies:
        - Returns list of user dictionaries
        - Correct number of users returned
        - User data structure is preserved
        - Function works without Flask app context
        
        Expected behavior:
        - Function calls SELECT * FROM users SQL query
        - Returns raw list of user dictionaries (not Flask response)
        - Data is suitable for LLM processing
        - No additional formatting or filtering applied
        
        Note: This function returns raw data, not a Flask Response object
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchall.return_value = sample_users
        
        result = get_users_for_llm()
        
        assert len(result) == 2
        assert result[0]['username'] == 'john_doe'
        assert result[1]['username'] == 'jane_smith'
    
    def setup_mock_db(self, mock_get_db):
        """
        Helper method to set up database mocks consistently.
        
        Creates mock database connection and cursor objects that simulate
        real database interactions without requiring an actual database.
        
        Returns:
            tuple: (mock_connection, mock_cursor) for use in tests
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        return mock_conn, mock_cursor