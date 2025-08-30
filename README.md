# MCP PostgreSQL Server

A clean, modular Flask application with PostgreSQL integration using MCP (Model Context Protocol) for database operations with LangChain/Ollama integration.

## Prerequisites

- **Docker & Docker Compose** - For PostgreSQL database
- **Python 3.11+** - For the Flask application
- **Ollama** - For LLM functionality ([Download here](https://ollama.ai/))

## Project Structure

```
├── src/
│   ├── config/
│   │   └── database.py          # Database connection configuration
│   ├── database/
│   │   ├── user_operations.py   # User CRUD operations
│   │   └── init.sql             # Database initialization
│   ├── services/
│   │   └── llm_service.py       # LangChain LLM service
│   └── routes/
│       └── mcp_routes.py        # MCP tool definitions and routing
├── app.py                       # Main Flask application
├── .env                         # Environment variables (create from .env.example)
├── .env.example                 # Environment variables template
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker configuration
└── Dockerfile                   # Container build instructions
```

## Quick Start (Docker - Recommended)

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env file with your settings if needed
```

### 2. Start the entire stack
```bash
docker-compose up -d
```

### 3. Test the service
```bash
curl http://localhost:8000/health
```

## Manual Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env file with your settings
```

### 4. Start PostgreSQL Container
```bash
docker-compose up postgres -d
```

### 5. Run MCP Server
```bash
python app.py
```

## Configuration

### Environment Variables

All configuration is handled through environment variables. See `.env.example` for all available options:

- **Database**: PostgreSQL connection settings
- **Ollama**: LLM model and endpoint configuration  
- **Flask**: Server host, port, and debug settings
- **Docker**: Container-specific overrides

The application uses **LangChain exclusively** for LLM interactions.

## MCP Tools

The unified server provides these MCP tools:
- `insert_user` - Create new user
- `get_users` - Retrieve all users  
- `get_user_by_id` - Get specific user
- `update_user` - Update existing user
- `delete_user` - Delete user
- `query_with_llm` - Natural language database queries

## API Endpoints

- `GET /health` - Health check (shows mode and connections)
- `GET /mcp/tools` - List available MCP tools
- `POST /mcp/call_tool` - Execute MCP tool

## Testing

### With cURL:
```bash
# Health check
curl http://localhost:8000/health

# List available tools
curl http://localhost:8000/mcp/tools

# Get all users
curl http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{"name": "get_users", "arguments": {}}'

# Insert user
curl http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{"name": "insert_user", "arguments": {"username": "test_user", "email": "test@example.com", "first_name": "Test", "last_name": "User"}}'

# Natural language query (requires Ollama)
curl http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{"name": "query_with_llm", "arguments": {"query": "Show me all users"}}'
```

### With Postman:
1. **Health Check**: GET `http://localhost:8000/health`
2. **List Tools**: GET `http://localhost:8000/mcp/tools`
3. **Call Tool**: POST `http://localhost:8000/mcp/call_tool` with JSON body

### Example Tool Call Body:
```json
{
  "name": "query_with_llm",
  "arguments": {
    "query": "Show me all users in a clean format"
  }
}
```

## Ollama Setup

1. **Install Ollama** from https://ollama.ai/
2. **Start Ollama service**:
   ```bash
   ollama serve
   ```
3. **Pull the required model**:
   ```bash
   ollama pull llama3.2
   ```
4. **Verify Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Running Tests

The test suite includes comprehensive tests for database operations, API endpoints, security, and LLM integration.

### Prerequisites for Testing
```bash
pip install pytest
```

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Files
```bash
pytest tests/test_config.py          # Database configuration tests
pytest tests/test_integration.py     # Full workflow integration tests  
pytest tests/test_llm_service.py     # LLM service and LangChain tests
pytest tests/test_mcp_routes.py      # MCP routes and schema tests
pytest tests/test_security.py        # Security and SQL injection tests
pytest tests/test_validation.py      # Input validation tests
```

### Run Tests with Verbose Output
```bash
pytest tests/ -v
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=src
```