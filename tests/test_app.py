import pytest
import json
from unittest.mock import patch, MagicMock
from app import app

class TestFlaskApp:
    
    @patch('app.get_db_connection')
    @patch('app.query_ollama_langchain')
    def test_health_check_healthy(self, mock_llm, mock_db, client):
        """Test health check endpoint returns healthy status when DB and Ollama are available"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        mock_llm.return_value = "test response"
        
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'
        assert data['langchain_mode'] == True
        assert data['ollama'] == 'connected'
    
    @patch('app.get_db_connection')
    def test_health_check_db_error(self, mock_db, client):
        """Test health check endpoint returns unhealthy status when database connection fails"""
        mock_db.side_effect = Exception("Database connection failed")
        
        response = client.get('/health')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'
        assert 'error' in data
    
    @patch('app.get_db_connection')
    @patch('app.query_ollama_langchain')
    def test_health_check_ollama_unavailable(self, mock_llm, mock_db, client):
        """Test health check endpoint shows ollama unavailable when LLM service fails"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value = mock_conn
        mock_llm.side_effect = Exception("Ollama unavailable")
        
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'
        assert data['ollama'] == 'unavailable'
    
    def test_list_tools(self, client):
        """Test MCP tools endpoint returns list of all available tools with correct count"""
        response = client.get('/mcp/tools')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tools' in data
        assert data['langchain_mode'] == True
        assert len(data['tools']) == 6
    
    @patch('src.database.user_operations.get_db_connection')
    def test_call_tool_get_users(self, mock_get_db, client):
        """Test MCP call_tool endpoint successfully calls get_users tool"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchall.return_value = []
        
        test_data = {"name": "get_users", "arguments": {}}
        
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'users' in data
    
    def test_call_tool_unknown_tool(self, client):
        """Test MCP call_tool endpoint returns 400 error for unknown tool names"""
        test_data = {"name": "unknown_tool", "arguments": {}}
        
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Unknown tool' in data['error']
    
    def setup_mock_db(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        return mock_conn, mock_cursor