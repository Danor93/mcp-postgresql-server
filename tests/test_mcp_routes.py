import pytest
import json
from unittest.mock import patch, MagicMock
from src.routes.mcp_routes import get_mcp_tools, call_mcp_tool

class TestMCPRoutes:
    
    def test_get_mcp_tools_returns_correct_tools(self, app_context):
        """Test that get_mcp_tools returns all expected MCP tools with correct structure"""
        response = get_mcp_tools()
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tools' in data
        assert data['langchain_mode'] == True
        
        tool_names = [tool['name'] for tool in data['tools']]
        expected_tools = ['insert_user', 'get_users', 'get_user_by_id', 'update_user', 'delete_user', 'query_with_llm']
        
        for tool in expected_tools:
            assert tool in tool_names
    
    def test_insert_user_tool_schema(self, app_context):
        """Test insert_user tool has correct input schema with required fields"""
        response = get_mcp_tools()
        data = json.loads(response.data)
        tools = data['tools']
        
        insert_user_tool = next(tool for tool in tools if tool['name'] == 'insert_user')
        schema = insert_user_tool['inputSchema']
        
        assert schema['type'] == 'object'
        assert 'username' in schema['properties']
        assert 'email' in schema['properties']
        assert 'first_name' in schema['properties']
        assert 'last_name' in schema['properties']
        assert schema['required'] == ['username', 'email']
    
    def test_get_user_by_id_tool_schema(self, app_context):
        """Test get_user_by_id tool has correct input schema with user_id requirement"""
        response = get_mcp_tools()
        data = json.loads(response.data)
        tools = data['tools']
        
        tool = next(tool for tool in tools if tool['name'] == 'get_user_by_id')
        schema = tool['inputSchema']
        
        assert schema['type'] == 'object'
        assert 'user_id' in schema['properties']
        assert schema['properties']['user_id']['type'] == 'integer'
        assert schema['required'] == ['user_id']
    
    def test_query_with_llm_tool_schema(self, app_context):
        """Test query_with_llm tool has correct input schema for natural language queries"""
        response = get_mcp_tools()
        data = json.loads(response.data)
        tools = data['tools']
        
        tool = next(tool for tool in tools if tool['name'] == 'query_with_llm')
        schema = tool['inputSchema']
        
        assert schema['type'] == 'object'
        assert 'query' in schema['properties']
        assert schema['properties']['query']['type'] == 'string'
        assert schema['required'] == ['query']
    
    @patch('src.routes.mcp_routes.insert_user')
    def test_call_mcp_tool_routes_to_correct_function(self, mock_insert_user):
        """Test call_mcp_tool correctly routes to insert_user function with arguments"""
        mock_response = {"success": True, "user": {"id": 1}}
        mock_insert_user.return_value = mock_response
        
        data = {"name": "insert_user", "arguments": {"username": "test", "email": "test@example.com"}}
        response = call_mcp_tool(data)
        
        assert response == mock_response
        mock_insert_user.assert_called_once_with({"username": "test", "email": "test@example.com"})
    
    def test_call_mcp_tool_unknown_tool_returns_error(self, app_context):
        """Test call_mcp_tool returns 400 error for unknown tool names"""
        data = {"name": "nonexistent_tool", "arguments": {}}
        response = call_mcp_tool(data)
        
        assert response[1] == 400
        data_response = json.loads(response[0].data)
        assert 'error' in data_response
        assert 'Unknown tool: nonexistent_tool' in data_response['error']
    
    @patch('src.routes.mcp_routes.get_users')
    def test_call_mcp_tool_handles_exceptions(self, mock_get_users, app_context):
        """Test call_mcp_tool returns 500 error when underlying function raises exception"""
        mock_get_users.side_effect = Exception("Database connection failed")
        
        data = {"name": "get_users", "arguments": {}}
        response = call_mcp_tool(data)
        
        assert response[1] == 500
        data_response = json.loads(response[0].data)
        assert 'error' in data_response
        assert 'Database connection failed' in data_response['error']
    
    def test_all_tools_have_required_schema_fields(self, app_context):
        """Test all MCP tools have required schema fields (name, description, inputSchema)"""
        response = get_mcp_tools()
        data = json.loads(response.data)
        tools = data['tools']
        
        for tool in tools:
            assert 'name' in tool
            assert 'description' in tool
            assert 'inputSchema' in tool
            assert isinstance(tool['name'], str)
            assert isinstance(tool['description'], str)
            assert isinstance(tool['inputSchema'], dict)