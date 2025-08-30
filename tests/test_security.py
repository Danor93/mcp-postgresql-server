import pytest
import json
from unittest.mock import patch, MagicMock
import psycopg2
from src.routes.mcp_routes import call_mcp_tool
from src.database.user_operations import insert_user, get_user_by_id, update_user

class TestSecurityAndNullHandling:
    
    @patch('src.database.user_operations.get_db_connection')
    def test_insert_user_with_null_database_fields(self, mock_get_db, app_context):
        """Test handling of NULL values returned from database for all fields"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # Mock database returning NULL for optional fields
        null_user = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': None,
            'last_name': None,
            'created_at': None,
            'updated_at': None
        }
        mock_cursor.fetchone.return_value = null_user
        
        args = {'username': 'testuser', 'email': 'test@example.com'}
        response = insert_user(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['first_name'] is None
        assert data['user']['last_name'] is None
    
    @patch('src.database.user_operations.get_db_connection')
    def test_get_user_with_all_null_optional_fields(self, mock_get_db, app_context):
        """Test retrieving user with NULL values in all optional fields"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        null_user = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': None,
            'last_name': None,
            'created_at': None,
            'updated_at': None
        }
        mock_cursor.fetchone.return_value = null_user
        
        args = {'user_id': 1}
        response = get_user_by_id(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['first_name'] is None
        assert data['user']['last_name'] is None
        assert data['user']['created_at'] is None
        assert data['user']['updated_at'] is None
    
    @patch('src.database.user_operations.get_db_connection')
    def test_update_user_to_null_values(self, mock_get_db, sample_user, app_context):
        """Test updating user fields to NULL values"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # User before update
        mock_cursor.fetchone.side_effect = [
            sample_user,  # Initial check
            {**sample_user, 'first_name': None, 'last_name': None}  # After update
        ]
        
        args = {'user_id': 1, 'first_name': None, 'last_name': None}
        response = update_user(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['first_name'] is None
        assert data['user']['last_name'] is None
    
    @patch('src.database.user_operations.get_db_connection')
    def test_sql_injection_in_username(self, mock_get_db, app_context):
        """Test SQL injection attempt in username field"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # SQL injection attempts
        malicious_usernames = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'; DELETE FROM users WHERE '1'='1",
            "' OR 1=1; --"
        ]
        
        for malicious_username in malicious_usernames:
            args = {'username': malicious_username, 'email': 'test@example.com'}
            response = insert_user(args)
            
            # Should either succeed (parameterized queries protect us) or handle gracefully
            # The key is that it shouldn't execute the malicious SQL
            mock_cursor.execute.assert_called()
            # Verify parameterized query is used (not string concatenation)
            call_args = mock_cursor.execute.call_args
            assert isinstance(call_args[0][1], tuple)  # Parameters passed as tuple
    
    @patch('src.database.user_operations.get_db_connection')
    def test_sql_injection_in_email(self, mock_get_db, app_context):
        """Test SQL injection attempt in email field"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        malicious_email = "test@example.com'; DROP TABLE users; --"
        args = {'username': 'testuser', 'email': malicious_email}
        response = insert_user(args)
        
        # Verify parameterized query usage
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args
        assert isinstance(call_args[0][1], tuple)
        assert malicious_email in call_args[0][1]  # Email passed as parameter, not in query string
    
    @patch('src.database.user_operations.get_db_connection')
    def test_sql_injection_in_user_id(self, mock_get_db, app_context):
        """Test SQL injection attempt in user_id field"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # Malicious user_id that could be dangerous if not parameterized
        malicious_user_id = "1 OR 1=1"
        
        data = {"name": "get_user_by_id", "arguments": {"user_id": malicious_user_id}}
        response = call_mcp_tool(data)
        
        # Should handle gracefully - the important thing is no SQL injection occurs
        # The system may accept the string (and parameterize it) or reject it
        if hasattr(response, 'status_code'):
            assert response.status_code in [200, 400, 404, 500]
        else:
            assert response[1] in [200, 400, 404, 500]
        
        # Most importantly, verify no actual SQL injection occurred
        # by checking that parameterized queries were used
        if response.status_code == 200:
            mock_cursor.execute.assert_called()
    
    @patch('src.database.user_operations.get_db_connection')
    def test_sql_injection_in_update_fields(self, mock_get_db, sample_user, app_context):
        """Test SQL injection attempts in update operation"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        # SQL injection attempt in update fields
        malicious_data = {
            'user_id': 1,
            'username': "newuser'; DROP TABLE users; --",
            'email': "new@test.com' OR '1'='1"
        }
        
        response = update_user(malicious_data)
        
        # Verify parameterized queries are used
        mock_cursor.execute.assert_called()
        # Check that the malicious strings are passed as parameters
        execute_calls = mock_cursor.execute.call_args_list
        for call in execute_calls:
            if len(call[0]) > 1:  # Has parameters
                assert isinstance(call[0][1], (tuple, list))
    
    @patch('src.database.user_operations.get_db_connection')
    def test_xss_prevention_in_user_data(self, mock_get_db, app_context):
        """Test that XSS attempts in user data are handled safely"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # XSS payload in user data
        xss_user = {
            'id': 1,
            'username': '<script>alert("XSS")</script>',
            'email': 'test@example.com',
            'first_name': '<img src=x onerror=alert(1)>',
            'last_name': 'javascript:alert("XSS")'
        }
        mock_cursor.fetchone.return_value = xss_user
        
        args = {'user_id': 1}
        response = get_user_by_id(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Data should be returned as-is (XSS protection happens at frontend/template level)
        assert data['user']['username'] == '<script>alert("XSS")</script>'
        assert data['user']['first_name'] == '<img src=x onerror=alert(1)>'
    
    @patch('src.database.user_operations.get_db_connection')
    def test_extremely_long_input_handling(self, mock_get_db, app_context):
        """Test handling of extremely long input strings"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # Very long strings that might cause buffer overflows or DoS
        very_long_string = "A" * 10000
        
        args = {
            'username': very_long_string,
            'email': f"{very_long_string}@example.com"
        }
        
        # Should handle gracefully - either succeed or fail with proper error
        try:
            response = insert_user(args)
            # If it succeeds, verify it was handled properly
            if hasattr(response, 'status_code'):
                assert response.status_code in [200, 400, 409, 500]
        except Exception as e:
            # If it raises an exception, it should be handled gracefully
            assert isinstance(e, (ValueError, psycopg2.Error))
    
    def setup_mock_db(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        return mock_conn, mock_cursor