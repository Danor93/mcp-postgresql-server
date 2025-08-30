import os
from langchain_ollama import OllamaLLM
from flask import jsonify
from src.database.user_operations import get_users_for_llm

def query_ollama_langchain(prompt: str) -> str:
    """Query Ollama using LangChain"""
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    
    llm = OllamaLLM(model=model_name, base_url=base_url)
    return llm.invoke(prompt)

def query_llm(prompt: str) -> str:
    """Query LLM using LangChain"""
    return query_ollama_langchain(prompt)

def query_with_llm(args):
    try:        
        users = get_users_for_llm()
        
        users_summary = f"Total users: {len(users)}\n"
        for user in users:
            users_summary += f"ID: {user['id']}, Username: {user['username']}, Email: {user['email']}, Name: {user.get('first_name', '')} {user.get('last_name', '')}\n"
        
        prompt = f"""You are a database assistant. The user asked: "{args['query']}"

Database content:
{users_summary}

Instructions:
- Provide clear, well-formatted responses
- Use proper spacing and indentation for readability
- Do NOT use markdown code blocks (```) 
- Do NOT include explanations or descriptions after the data
- If returning JSON, format it cleanly with proper line breaks
- Be concise and direct"""
        
        llm_response = query_llm(prompt)
        return jsonify({
            'success': True, 
            'llm_response': llm_response,
            'mode': 'langchain'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error querying with LLM: {str(e)}'}), 500