"""
Regression Tests
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import app
from src.middleware.auth import JWTAuth


@pytest.mark.regression
class TestRegressionSimple:
    
    def get_auth_header(self):
        """Helper to generate valid auth header for tests"""
        with app.app_context():
            auth = JWTAuth()
            token = auth.generate_token(1, 'testuser')
            return {'Authorization': f'Bearer {token}'}
    
    def setup_mock_db(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        return mock_conn, mock_cursor
    
    @pytest.mark.regression
    @patch('src.database.user_operations.get_db_connection')
    def test_complete_user_crud_workflow(self, mock_get_db, client):
        """
        Regression Test: Complete user CRUD workflow
        
        This test ensures all CRUD operations work together correctly
        and prevents regressions in the core functionality.
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # Mock user data
        new_user = {
            'id': 1, 
            'username': 'testuser', 
            'email': 'test@example.com', 
            'first_name': 'Test', 
            'last_name': 'User'
        }
        updated_user = new_user.copy()
        updated_user['first_name'] = 'Updated'
        
        # Set up mock responses for different operations
        mock_cursor.fetchone.side_effect = [
            new_user,     # Insert operation
            new_user,     # Get by ID operation
            new_user,     # Update check
            updated_user, # Update result
            new_user      # Delete check
        ]
        mock_cursor.fetchall.return_value = [new_user]
        
        headers = self.get_auth_header()
        
        # 1. Insert user
        insert_data = {
            "name": "insert_user",
            "arguments": {
                "username": "testuser", 
                "email": "test@example.com", 
                "first_name": "Test", 
                "last_name": "User"
            }
        }
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(insert_data), 
                             content_type='application/json', 
                             headers=headers)
        assert response.status_code == 200
        
        # 2. Get all users
        get_all_data = {"name": "get_users", "arguments": {}}
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(get_all_data), 
                             content_type='application/json', 
                             headers=headers)
        assert response.status_code == 200
        
        # 3. Get user by ID
        get_by_id_data = {"name": "get_user_by_id", "arguments": {"user_id": 1}}
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(get_by_id_data), 
                             content_type='application/json', 
                             headers=headers)
        assert response.status_code == 200
        
        # 4. Update user
        update_data = {"name": "update_user", "arguments": {"user_id": 1, "first_name": "Updated"}}
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(update_data), 
                             content_type='application/json', 
                             headers=headers)
        assert response.status_code == 200
        
        # 5. Delete user
        delete_data = {"name": "delete_user", "arguments": {"user_id": 1}}
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(delete_data), 
                             content_type='application/json', 
                             headers=headers)
        assert response.status_code == 200
    
    @pytest.mark.regression
    def test_authentication_regression(self, client):
        """
        Regression Test: Authentication system works correctly
        
        Ensures authentication doesn't break with code changes.
        """
        # Test protected endpoint without auth
        response = client.get('/mcp/tools')
        assert response.status_code == 401
        
        # Test protected endpoint with auth
        headers = self.get_auth_header()
        response = client.get('/mcp/tools', headers=headers)
        assert response.status_code == 200
        
        # Test malformed token
        bad_headers = {'Authorization': 'Bearer invalid.token'}
        response = client.get('/mcp/tools', headers=bad_headers)
        assert response.status_code == 401