import pytest
import json
from unittest.mock import patch, MagicMock
from src.routes.mcp_routes import call_mcp_tool
from src.services.llm_service import query_with_llm

class TestInputValidation:
    
    @patch('src.database.user_operations.get_db_connection')
    def test_insert_user_missing_required_fields(self, mock_get_db, app_context):
        """Test insert_user handles missing required fields gracefully"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        
        # Test missing username
        data = {"name": "insert_user", "arguments": {"email": "test@example.com"}}
        response = call_mcp_tool(data)
        
        assert response[1] == 500
        error_data = json.loads(response[0].data)
        assert 'error' in error_data
    
    @patch('src.database.user_operations.get_db_connection')
    def test_insert_user_empty_required_fields(self, mock_get_db, app_context):
        """Test insert_user handles empty required fields"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = {'id': 1, 'username': '', 'email': ''}
        
        data = {"name": "insert_user", "arguments": {"username": "", "email": ""}}
        response = call_mcp_tool(data)
        
        # Should succeed with empty values (database allows it)
        assert response.status_code == 200
    
    def test_get_user_by_id_invalid_user_id_type(self, app_context):
        """Test get_user_by_id handles invalid user_id types"""
        data = {"name": "get_user_by_id", "arguments": {"user_id": "not_a_number"}}
        response = call_mcp_tool(data)
        
        assert response[1] == 500
        error_data = json.loads(response[0].data)
        assert 'error' in error_data
    
    def test_call_mcp_tool_missing_arguments(self, app_context):
        """Test call_mcp_tool handles missing arguments field"""
        data = {"name": "get_users"}
        response = call_mcp_tool(data)
        
        # Should use empty dict as default and work
        assert response.status_code == 200 or response[1] == 200
    
    def test_call_mcp_tool_missing_name(self, app_context):
        """Test call_mcp_tool handles missing tool name"""
        data = {"arguments": {}}
        response = call_mcp_tool(data)
        
        assert response[1] == 400
        error_data = json.loads(response[0].data)
        assert 'Unknown tool: None' in error_data['error']
    
    @patch('src.services.llm_service.get_users_for_llm')
    @patch('src.services.llm_service.query_llm')
    def test_query_with_llm_empty_query(self, mock_query_llm, mock_get_users, app_context):
        """Test query_with_llm handles empty query strings"""
        mock_get_users.return_value = []
        mock_query_llm.return_value = "No specific query provided"
        
        args = {'query': ''}
        response = query_with_llm(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    @patch('src.services.llm_service.get_users_for_llm')
    @patch('src.services.llm_service.query_llm')
    def test_query_with_llm_missing_query(self, mock_query_llm, mock_get_users, app_context):
        """Test query_with_llm handles missing query field"""
        mock_get_users.return_value = []
        
        args = {}
        response = query_with_llm(args)
        
        assert response[1] == 500
        error_data = json.loads(response[0].data)
        assert 'error' in error_data
    
    def setup_mock_db(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        return mock_conn, mock_cursor