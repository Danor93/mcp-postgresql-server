import pytest
import json
from unittest.mock import patch, MagicMock

class TestIntegration:
    
    @patch('src.database.user_operations.get_db_connection')
    def test_full_user_crud_workflow(self, mock_get_db, client):
        """Test complete user CRUD workflow through API endpoints"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # Mock user data
        new_user = {'id': 1, 'username': 'testuser', 'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
        updated_user = new_user.copy()
        updated_user['first_name'] = 'Updated'
        
        # Set up mock responses for different operations
        # Insert (1), Get by ID (2), Update check (3), Update result (4), Delete check (5)
        mock_cursor.fetchone.side_effect = [new_user, new_user, new_user, updated_user, new_user]
        mock_cursor.fetchall.return_value = [new_user]
        
        # 1. Insert user
        insert_data = {
            "name": "insert_user",
            "arguments": {"username": "testuser", "email": "test@example.com", "first_name": "Test", "last_name": "User"}
        }
        response = client.post('/mcp/call_tool', data=json.dumps(insert_data), content_type='application/json')
        assert response.status_code == 200
        
        # 2. Get all users
        get_all_data = {"name": "get_users", "arguments": {}}
        response = client.post('/mcp/call_tool', data=json.dumps(get_all_data), content_type='application/json')
        assert response.status_code == 200
        
        # 3. Get user by ID
        get_by_id_data = {"name": "get_user_by_id", "arguments": {"user_id": 1}}
        response = client.post('/mcp/call_tool', data=json.dumps(get_by_id_data), content_type='application/json')
        assert response.status_code == 200
        
        # 4. Update user
        update_data = {"name": "update_user", "arguments": {"user_id": 1, "first_name": "Updated"}}
        response = client.post('/mcp/call_tool', data=json.dumps(update_data), content_type='application/json')
        assert response.status_code == 200
        
        # 5. Delete user
        delete_data = {"name": "delete_user", "arguments": {"user_id": 1}}
        response = client.post('/mcp/call_tool', data=json.dumps(delete_data), content_type='application/json')
        assert response.status_code == 200
    
    @patch('src.database.user_operations.get_db_connection')
    @patch('src.services.llm_service.query_llm')
    def test_llm_query_integration(self, mock_query_llm, mock_get_db, client):
        """Test LLM query integration through API endpoint"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'username': 'john', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'}
        ]
        mock_query_llm.return_value = "Found 1 user: John Doe"
        
        llm_data = {"name": "query_with_llm", "arguments": {"query": "How many users do we have?"}}
        response = client.post('/mcp/call_tool', data=json.dumps(llm_data), content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['mode'] == 'langchain'
        assert 'Found 1 user' in data['llm_response']
    
    @patch('app.get_db_connection')
    def test_health_check_integration_with_real_endpoints(self, mock_get_db, client):
        """Test health check integration with actual endpoint routing"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        
        # Health check should work independently
        response = client.get('/health')
        assert response.status_code == 200
        
        # Tools listing should work
        response = client.get('/mcp/tools')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['tools']) == 6
    
    def test_invalid_json_payload(self, client):
        """Test API endpoints handle invalid JSON payloads gracefully"""
        response = client.post('/mcp/call_tool', 
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_missing_content_type(self, client):
        """Test API endpoints handle missing content-type header"""
        response = client.post('/mcp/call_tool', 
                             data='{"name": "get_users", "arguments": {}}')
        
        # Flask should handle this gracefully
        assert response.status_code in [400, 415]
    
    def setup_mock_db(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        return mock_conn, mock_cursor