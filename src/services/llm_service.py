import os
import json
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
- Return data as JSON only, no explanations
- For user data, format as an array of user objects with id, username, email, and name fields
- Do NOT group data by columns (avoid arrays of IDs, arrays of usernames, etc.)
- Each user should be a complete object: {{"id": 1, "username": "john_doe", "email": "john@example.com", "name": "John Doe"}}
- Do NOT use markdown code blocks (```)
- Return only valid JSON"""
        
        llm_response = query_llm(prompt)
        
        # Try to parse the LLM response as JSON
        try:
            parsed_response = json.loads(llm_response)
            return jsonify({
                'success': True,
                'data': parsed_response,
                'mode': 'langchain'
            })
        except json.JSONDecodeError:
            # If it's not valid JSON, return as text
            return jsonify({
                'success': True,
                'llm_response': llm_response,
                'mode': 'langchain'
            })
        
    except Exception as e:
        return jsonify({'error': f'Error querying with LLM: {str(e)}'}), 500