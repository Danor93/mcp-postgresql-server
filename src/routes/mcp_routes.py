from flask import jsonify
from src.database.user_operations import insert_user, get_users, get_user_by_id, update_user, delete_user
from src.services.llm_service import query_with_llm

def get_mcp_tools():
    tools = [
        {
            "name": "insert_user",
            "description": "Insert a new user into the database",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Unique username"},
                    "email": {"type": "string", "description": "User's email address"},
                    "first_name": {"type": "string", "description": "User's first name (optional)"},
                    "last_name": {"type": "string", "description": "User's last name (optional)"}
                },
                "required": ["username", "email"]
            }
        },
        {
            "name": "get_users",
            "description": "Get all users from the database",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "get_user_by_id", 
            "description": "Get a specific user by ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "The ID of the user to retrieve"}
                },
                "required": ["user_id"]
            }
        },
        {
            "name": "update_user",
            "description": "Update an existing user",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "user_id": {"type": "integer", "description": "The ID of the user to update"},
                    "username": {"type": "string", "description": "New username (optional)"},
                    "email": {"type": "string", "description": "New email (optional)"},
                    "first_name": {"type": "string", "description": "New first name (optional)"},
                    "last_name": {"type": "string", "description": "New last name (optional)"}
                },
                "required": ["user_id"]
            }
        },
        {
            "name": "delete_user",
            "description": "Delete a user from the database", 
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "The ID of the user to delete"}
                },
                "required": ["user_id"]
            }
        },
        {
            "name": "query_with_llm",
            "description": "Query the database using natural language with LLM assistance (LangChain mode)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language query about the database"}
                },
                "required": ["query"]
            }
        }
    ]
    return jsonify({"tools": tools, "langchain_mode": True})

def call_mcp_tool(data):
    tool_name = data.get('name')
    arguments = data.get('arguments', {})
    
    try:
        if tool_name == "insert_user":
            return insert_user(arguments)
        elif tool_name == "get_users":
            return get_users(arguments)
        elif tool_name == "get_user_by_id":
            return get_user_by_id(arguments)
        elif tool_name == "update_user":
            return update_user(arguments)
        elif tool_name == "delete_user":
            return delete_user(arguments)
        elif tool_name == "query_with_llm":
            return query_with_llm(arguments)
        else:
            return jsonify({'error': f'Unknown tool: {tool_name}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500