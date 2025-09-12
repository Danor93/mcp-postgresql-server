"""
Integration Tests - Flask Application Endpoints

These integration tests verify that Flask application endpoints work correctly
when multiple components interact together. Integration tests focus on testing
the interaction between routing, middleware, database connections, and external
services without mocking all dependencies.

Run these tests with:
    pytest tests/test_app.py -v
    pytest -m integration
    pytest -m "integration and not slow"

What makes these Integration Tests:
    - Test HTTP endpoints through Flask test client
    - Mock external dependencies (database, LLM) but test routing logic
    - Verify middleware integration (authentication, rate limiting)
    - Test error handling across component boundaries
    - Focus on API contract and component interaction

Key Testing Patterns:
    - Use Flask test client for HTTP requests
    - Mock external services but test business logic
    - Test both success and error response formats
    - Verify authentication and authorization flow
    - Check endpoint behavior under various conditions
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import app
from src.middleware.auth import JWTAuth


@pytest.mark.integration
class TestFlaskApp:
    """
    Integration tests for Flask application endpoints.
    
    These tests verify that HTTP endpoints work correctly when components
    interact together, including routing, middleware, and business logic.
    """
    
    def get_auth_header(self):
        """Helper to generate valid auth header for tests"""
        with app.app_context():
            auth = JWTAuth()
            token = auth.generate_token(1, 'testuser')
            return {'Authorization': f'Bearer {token}'}
    
    @pytest.mark.integration
    @patch('app.get_db_connection')
    @patch('app.query_ollama_langchain')
    def test_health_check_healthy(self, mock_llm, mock_db, client):
        """
        Integration Test: Health endpoint with all services available
        
        Tests: GET /health -> 200 with healthy status
        Input: HTTP GET request to health endpoint
        Mocks: Database connection and LLM service both working
        
        Verifies:
        - Endpoint returns 200 status code
        - Response contains 'healthy' status
        - Database status is 'connected'
        - Ollama status is 'connected'
        - LangChain mode is enabled
        
        Integration aspects:
        - Flask routing to health endpoint
        - Database connection checking
        - LLM service availability testing
        - JSON response formatting
        """
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
    
    @pytest.mark.integration
    @patch('app.get_db_connection')
    def test_health_check_db_error(self, mock_db, client):
        """
        Integration Test: Health endpoint with database failure
        
        Tests: GET /health -> 500 with error status
        Input: HTTP GET request to health endpoint
        Mocks: Database connection raising exception
        
        Verifies:
        - Endpoint returns 500 status code for system errors
        - Response contains 'unhealthy' status
        - Error information is included in response
        - System handles database failures gracefully
        
        Integration aspects:
        - Error propagation from database layer to HTTP response
        - Exception handling in Flask endpoint
        - Appropriate HTTP status code mapping
        """
        mock_db.side_effect = Exception("Database connection failed")
        
        response = client.get('/health')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'
        assert 'error' in data
    
    @pytest.mark.integration
    @patch('app.get_db_connection')
    @patch('app.query_ollama_langchain')
    def test_health_check_ollama_unavailable(self, mock_llm, mock_db, client):
        """
        Integration Test: Health endpoint with LLM service failure
        
        Tests: GET /health -> 200 with partial service availability
        Input: HTTP GET request to health endpoint
        Mocks: Database working, LLM service failing
        
        Verifies:
        - Endpoint returns 200 status code (system still functional)
        - Response contains 'healthy' status (core services working)
        - Database status is 'connected'
        - Ollama status is 'unavailable'
        - System degrades gracefully when optional services fail
        
        Integration aspects:
        - Partial system failure handling
        - Service dependency management
        - Graceful degradation behavior
        """
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
    
    @pytest.mark.integration
    def test_list_tools(self, client):
        """
        Integration Test: MCP tools listing with authentication
        
        Tests: GET /mcp/tools -> 200 with tools list
        Input: HTTP GET request with valid authentication
        Mocks: Uses authentication middleware
        
        Verifies:
        - Endpoint returns 200 status code
        - Response contains 'tools' array
        - Correct number of tools returned (6)
        - LangChain mode is enabled
        - Authentication middleware allows access
        
        Integration aspects:
        - Authentication middleware integration
        - MCP tools registration and listing
        - JSON response structure
        - Route protection verification
        """
        headers = self.get_auth_header()
        response = client.get('/mcp/tools', headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tools' in data
        assert data['langchain_mode'] == True
        assert len(data['tools']) == 6
    
    @pytest.mark.integration
    @patch('src.database.user_operations.get_db_connection')
    def test_call_tool_get_users(self, mock_get_db, client):
        """
        Integration Test: MCP tool execution through API
        
        Tests: POST /mcp/call_tool -> 200 with tool results
        Input: JSON payload with tool name and arguments
        Mocks: Database connection for user operations
        
        Verifies:
        - Endpoint returns 200 status code
        - Tool execution completes successfully
        - Response contains expected data structure ('users')
        - Authentication is required and working
        
        Integration aspects:
        - HTTP request routing to tool execution
        - JSON payload validation and processing
        - Tool dispatcher integration
        - Database layer interaction through tools
        - Authentication middleware enforcement
        """
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchall.return_value = []
        
        test_data = {"name": "get_users", "arguments": {}}
        
        headers = self.get_auth_header()
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(test_data),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'users' in data
    
    @pytest.mark.integration
    def test_call_tool_unknown_tool(self, client):
        """
        Integration Test: MCP tool execution error handling
        
        Tests: POST /mcp/call_tool -> 400 with error
        Input: JSON payload with unknown tool name
        Mocks: None (tests error path)
        
        Verifies:
        - Endpoint returns 400 status code for bad requests
        - Response contains error information
        - Error message mentions 'Unknown tool'
        - Invalid tool names are handled gracefully
        
        Integration aspects:
        - Input validation in HTTP layer
        - Error response formatting
        - Tool dispatcher error handling
        - Proper HTTP status code for client errors
        """
        test_data = {"name": "unknown_tool", "arguments": {}}
        
        headers = self.get_auth_header()
        response = client.post('/mcp/call_tool', 
                             data=json.dumps(test_data),
                             content_type='application/json',
                             headers=headers)
        
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