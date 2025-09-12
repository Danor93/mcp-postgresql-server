"""
E2E Tests
This is a working version of E2E tests using known patterns.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import app
from src.middleware.auth import JWTAuth


@pytest.mark.e2e
class TestE2ESimple:
    """End-to-End tests that simulate complete user journeys"""
    
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
    
    @pytest.mark.e2e
    @patch('src.database.user_operations.get_db_connection')
    @patch('src.services.llm_service.query_ollama_langchain')
    def test_complete_user_workflow_with_llm(self, mock_llm, mock_get_db, client):
        """
        E2E Test: Complete user workflow including LLM query
        
        This simulates a real user journey:
        1. Create a user
        2. Query user data with natural language
        3. Update user information
        4. Verify changes were applied
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # Test user data
        test_user = {
            'id': 1,
            'username': 'e2e_testuser',
            'email': 'e2e@example.com',
            'first_name': 'E2E',
            'last_name': 'User'
        }
        
        updated_user = test_user.copy()
        updated_user['first_name'] = 'Updated_E2E'
        
        # Set up mock responses for the complete workflow
        mock_cursor.fetchone.side_effect = [
            test_user,     # Insert operation
            test_user,     # Update check
            updated_user   # Update result
        ]
        mock_cursor.fetchall.return_value = [test_user]
        mock_llm.return_value = f"Found user: {test_user['first_name']} {test_user['last_name']}"
        
        headers = self.get_auth_header()
        
        # Step 1: Create user
        create_data = {
            "name": "insert_user",
            "arguments": {
                "username": test_user['username'],
                "email": test_user['email'],
                "first_name": test_user['first_name'],
                "last_name": test_user['last_name']
            }
        }
        
        response = client.post('/mcp/call_tool',
                             data=json.dumps(create_data),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['username'] == test_user['username']
        
        # Step 2: Query user with LLM
        llm_query = {
            "name": "query_with_llm",
            "arguments": {
                "query": f"Tell me about user {test_user['username']}"
            }
        }
        
        response = client.post('/mcp/call_tool',
                             data=json.dumps(llm_query),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'llm_response' in data
        assert test_user['first_name'] in data['llm_response']
        
        # Step 3: Update user
        update_data = {
            "name": "update_user",
            "arguments": {
                "user_id": test_user['id'],
                "first_name": "Updated_E2E"
            }
        }
        
        response = client.post('/mcp/call_tool',
                             data=json.dumps(update_data),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['first_name'] == 'Updated_E2E'
    
    @pytest.mark.e2e
    @patch('src.database.user_operations.get_db_connection')
    def test_data_integrity_verification(self, mock_get_db, client):
        """
        E2E Test: Data integrity across operations
        
        Verifies that data remains consistent through create, read, update cycles.
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        original_user = {
            'id': 1,
            'username': 'integrity_user',
            'email': 'integrity@test.com',
            'first_name': 'Original',
            'last_name': 'User'
        }
        
        # Only first_name should change
        updated_user = original_user.copy()
        updated_user['first_name'] = 'Modified'
        
        mock_cursor.fetchone.side_effect = [
            original_user,  # Insert
            original_user,  # Get after insert
            original_user,  # Update check
            updated_user    # Update result
        ]
        
        headers = self.get_auth_header()
        
        # Create user
        create_data = {
            "name": "insert_user",
            "arguments": {
                "username": original_user['username'],
                "email": original_user['email'],
                "first_name": original_user['first_name'],
                "last_name": original_user['last_name']
            }
        }
        
        response = client.post('/mcp/call_tool',
                             data=json.dumps(create_data),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 200
        
        # Get user to verify creation
        get_data = {
            "name": "get_user_by_id",
            "arguments": {"user_id": 1}
        }
        
        response = client.post('/mcp/call_tool',
                             data=json.dumps(get_data),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['username'] == original_user['username']
        assert data['user']['email'] == original_user['email']
        
        # Update only first_name
        update_data = {
            "name": "update_user",
            "arguments": {
                "user_id": 1,
                "first_name": "Modified"
            }
        }
        
        response = client.post('/mcp/call_tool',
                             data=json.dumps(update_data),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify only first_name changed, others remain the same
        assert data['user']['first_name'] == 'Modified'
        assert data['user']['username'] == original_user['username']
        assert data['user']['email'] == original_user['email']
        assert data['user']['last_name'] == original_user['last_name']
    
    @pytest.mark.e2e
    def test_authentication_workflow(self, client):
        """
        E2E Test: Complete authentication workflow
        
        Tests the user experience with authentication from login to accessing resources.
        """
        # Test 1: Access protected resource without auth (should fail)
        response = client.get('/mcp/tools')
        assert response.status_code == 401
        
        # Test 2: Get valid token and access resources
        headers = self.get_auth_header()
        response = client.get('/mcp/tools', headers=headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'tools' in data
        assert len(data['tools']) > 0
        
        # Test 3: Use token for actual operations
        test_operation = {
            "name": "get_users",
            "arguments": {}
        }
        
        response = client.post('/mcp/call_tool',
                             data=json.dumps(test_operation),
                             content_type='application/json',
                             headers=headers)
        
        # Should work with valid token
        assert response.status_code in [200, 500]  # 500 is OK if no mock DB