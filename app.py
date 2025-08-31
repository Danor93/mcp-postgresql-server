import os
from flask import Flask, request, jsonify
from src.config.database import get_db_connection
from src.routes.mcp_routes import get_mcp_tools, call_mcp_tool
from src.services.llm_service import query_ollama_langchain
from src.middleware.security import validate_json_input, MCPToolCallSchema, validate_sql_query_params
from src.middleware.rate_limiter import init_rate_limiter, configure_rate_limits

app = Flask(__name__)
limiter = init_rate_limiter(app)
rate_limits = configure_rate_limits(limiter)

@app.route('/health', methods=['GET'])
@limiter.limit(rate_limits['health_check'])
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        
        status = {
            'status': 'healthy',
            'database': 'connected',
            'langchain_mode': True
        }
        
        # Test Ollama connection via LangChain
        try:
            test_llm = query_ollama_langchain("test")
            status['ollama'] = 'connected'
        except:
            status['ollama'] = 'unavailable'
            
        return jsonify(status)
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/mcp/tools', methods=['GET'])
@limiter.limit(rate_limits['list_tools'])
@validate_sql_query_params()
def list_tools():
    return get_mcp_tools()

@app.route('/mcp/call_tool', methods=['POST'])
@limiter.limit(rate_limits['call_tool'])
@validate_json_input(MCPToolCallSchema)
def call_tool():
    data = request.validated_json
    return call_mcp_tool(data)

if __name__ == '__main__':
    print("Starting MCP server in LangChain mode")
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '8000'))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(debug=debug, host=host, port=port)