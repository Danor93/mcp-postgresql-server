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
│   ├── middleware/
│   │   ├── auth.py              # JWT authentication
│   │   ├── rate_limiter.py      # Rate limiting middleware
│   │   └── security.py          # Security middleware
│   ├── services/
│   │   └── llm_service.py       # LangChain LLM service
│   └── routes/
│       ├── auth_routes.py       # Authentication endpoints
│       └── mcp_routes.py        # MCP tool definitions and routing
├── tests/                       # Comprehensive test suite (72 tests)
├── app.py                       # Main Flask application
├── pytest.ini                  # Test configuration
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
- `GET /mcp/tools` - List available MCP tools (requires auth)
- `POST /mcp/call_tool` - Execute MCP tool (requires auth)
- `POST /auth/login` - Generate authentication token
- `GET /auth/verify` - Verify token validity

## Authentication

All MCP endpoints require JWT authentication. Use the following steps:

### 1. Generate Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

Response:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { "id": 1, "username": "admin" }
}
```

### 2. Use Token in Requests

Add the token to the `Authorization` header:

```bash
curl -X POST http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"name": "get_users", "arguments": {}}'
```

## Testing

### With cURL:

```bash
# Health check
curl http://localhost:8000/health

# Get authentication token first
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  | jq -r .token)

# List available tools
curl http://localhost:8000/mcp/tools \
  -H "Authorization: Bearer $TOKEN"

# Get all users
curl http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "get_users", "arguments": {}}'

# Insert user
curl http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "insert_user", "arguments": {"username": "test_user", "email": "test@example.com", "first_name": "Test", "last_name": "User"}}'

# Natural language query (requires Ollama)
curl http://localhost:8000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "query_with_llm", "arguments": {"query": "Show me all users"}}'
```

### With Postman:

1. **Get Token**: POST `http://localhost:8000/auth/login`

   - Body: `{"username": "admin", "password": "password"}`
   - Copy the `token` from response

2. **Health Check**: GET `http://localhost:8000/health` (no auth required)

3. **List Tools**: GET `http://localhost:8000/mcp/tools`

   - Headers: `Authorization: Bearer YOUR_TOKEN`

4. **Call Tool**: POST `http://localhost:8000/mcp/call_tool`
   - Headers: `Authorization: Bearer YOUR_TOKEN`
   - Body: JSON tool call

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

### Local Tests

```bash
# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run specific test categories
python -m pytest -m sanity     # Quick health checks
python -m pytest -m unit       # Unit tests
python -m pytest -m integration # Integration tests
python -m pytest -m e2e        # End-to-end tests
```

### Docker Tests

```bash
# Run tests in Docker container
docker run --rm mcp-postgresql-server python -m pytest tests/

# Run with verbose output
docker run --rm mcp-postgresql-server python -m pytest tests/ -v
```
