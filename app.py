import os
from flask import Flask, request, jsonify
from src.config.database import get_db_connection
from src.routes.mcp_routes import get_mcp_tools, call_mcp_tool
from src.services.llm_service import query_ollama_langchain

app = Flask(__name__)

@app.route('/health', methods=['GET'])
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
def list_tools():
    return get_mcp_tools()

@app.route('/mcp/call_tool', methods=['POST'])
def call_tool():
    data = request.get_json()
    return call_mcp_tool(data)

if __name__ == '__main__':
    print("Starting MCP server in LangChain mode")
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '8000'))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(debug=debug, host=host, port=port)