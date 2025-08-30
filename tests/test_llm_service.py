import pytest
import json
import os
from unittest.mock import patch, MagicMock
from src.services.llm_service import query_ollama_langchain, query_llm, query_with_llm

class TestLLMService:
    
    @patch('src.services.llm_service.OllamaLLM')
    def test_query_ollama_langchain_success(self, mock_ollama_llm):
        """Test query_ollama_langchain successfully calls Ollama with correct parameters"""
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = "Test LLM response"
        mock_ollama_llm.return_value = mock_llm_instance
        
        result = query_ollama_langchain("test prompt")
        
        assert result == "Test LLM response"
        mock_ollama_llm.assert_called_once()
        mock_llm_instance.invoke.assert_called_once_with("test prompt")
    
    @patch('src.services.llm_service.OllamaLLM')
    def test_query_ollama_langchain_uses_env_variables(self, mock_ollama_llm):
        """Test query_ollama_langchain uses environment variables for model and base URL"""
        with patch.dict(os.environ, {'OLLAMA_MODEL': 'custom-model', 'OLLAMA_BASE_URL': 'http://custom:1234'}):
            mock_llm_instance = MagicMock()
            mock_ollama_llm.return_value = mock_llm_instance
            
            query_ollama_langchain("test")
            
            mock_ollama_llm.assert_called_once_with(
                model='custom-model', 
                base_url='http://custom:1234'
            )
    
    @patch('src.services.llm_service.OllamaLLM')
    def test_query_ollama_langchain_default_values(self, mock_ollama_llm):
        """Test query_ollama_langchain uses default values when env variables not set"""
        with patch.dict(os.environ, {}, clear=True):
            mock_llm_instance = MagicMock()
            mock_ollama_llm.return_value = mock_llm_instance
            
            query_ollama_langchain("test")
            
            mock_ollama_llm.assert_called_once_with(
                model='llama3.2',
                base_url='http://host.docker.internal:11434'
            )
    
    @patch('src.services.llm_service.query_ollama_langchain')
    def test_query_llm_delegates_to_ollama(self, mock_query_ollama):
        """Test query_llm function properly delegates to query_ollama_langchain"""
        mock_query_ollama.return_value = "LLM response"
        
        result = query_llm("test prompt")
        
        assert result == "LLM response"
        mock_query_ollama.assert_called_once_with("test prompt")
    
    @patch('src.services.llm_service.get_users_for_llm')
    @patch('src.services.llm_service.query_llm')
    def test_query_with_llm_success(self, mock_query_llm, mock_get_users, app_context):
        """Test query_with_llm successfully processes natural language database queries"""
        mock_users = [
            {'id': 1, 'username': 'john', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'}
        ]
        mock_get_users.return_value = mock_users
        mock_query_llm.return_value = "Here are the users: John Doe (john)"
        
        args = {'query': 'Show me all users'}
        response = query_with_llm(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['mode'] == 'langchain'
        assert 'llm_response' in data
        mock_get_users.assert_called_once()
        mock_query_llm.assert_called_once()
    
    @patch('src.services.llm_service.get_users_for_llm')
    def test_query_with_llm_database_error(self, mock_get_users, app_context):
        """Test query_with_llm returns 500 error when database operation fails"""
        mock_get_users.side_effect = Exception("Database connection failed")
        
        args = {'query': 'Show me all users'}
        response = query_with_llm(args)
        
        assert response[1] == 500
        data = json.loads(response[0].data)
        assert 'error' in data
        assert 'Error querying with LLM' in data['error']
    
    @patch('src.services.llm_service.get_users_for_llm')
    @patch('src.services.llm_service.query_llm')
    def test_query_with_llm_formats_user_data_correctly(self, mock_query_llm, mock_get_users, app_context):
        """Test query_with_llm formats user data correctly for LLM processing"""
        mock_users = [
            {'id': 1, 'username': 'john', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'id': 2, 'username': 'jane', 'email': 'jane@example.com', 'first_name': None, 'last_name': None}
        ]
        mock_get_users.return_value = mock_users
        mock_query_llm.return_value = "Users listed"
        
        args = {'query': 'List users'}
        query_with_llm(args)
        
        # Verify the prompt was called and contains user data
        mock_query_llm.assert_called_once()
        call_args = mock_query_llm.call_args[0][0]
        assert 'Total users: 2' in call_args
        assert 'Username: john' in call_args
        assert 'Username: jane' in call_args