import pytest
import json
from unittest.mock import patch, MagicMock
import psycopg2
from src.database.user_operations import (
    insert_user, get_users, get_user_by_id, 
    update_user, delete_user, get_users_for_llm
)

class TestUserOperations:
    
    @patch('src.database.user_operations.get_db_connection')
    def test_insert_user_success(self, mock_get_db, sample_user, app_context):
        """Test successful user insertion with all fields returns user data"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        args = {'username': 'test_user', 'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
        response = insert_user(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['username'] == 'test_user'
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @patch('src.database.user_operations.get_db_connection')
    def test_insert_user_duplicate_error(self, mock_get_db, app_context):
        """Test user insertion fails with 409 error when username/email already exists"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.execute.side_effect = psycopg2.IntegrityError("duplicate key")
        
        args = {'username': 'test_user', 'email': 'test@example.com'}
        response_tuple = insert_user(args)
        
        assert response_tuple[1] == 409
        data = json.loads(response_tuple[0].data)
        assert 'error' in data
        mock_conn.rollback.assert_called_once()
    
    @patch('src.database.user_operations.get_db_connection')
    def test_get_users_success(self, mock_get_db, sample_users, app_context):
        """Test get_users returns all users from database in correct format"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchall.return_value = sample_users
        
        response = get_users({})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['users']) == 2
        assert data['users'][0]['username'] == 'john_doe'
    
    @patch('src.database.user_operations.get_db_connection')
    def test_get_user_by_id_found(self, mock_get_db, sample_user, app_context):
        """Test get_user_by_id returns specific user data when user exists"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        args = {'user_id': 1}
        response = get_user_by_id(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user']['id'] == 1
        assert data['user']['username'] == 'test_user'
    
    @patch('src.database.user_operations.get_db_connection')
    def test_get_user_by_id_not_found(self, mock_get_db, app_context):
        """Test get_user_by_id returns 404 error when user does not exist"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = None
        
        args = {'user_id': 999}
        response_tuple = get_user_by_id(args)
        
        assert response_tuple[1] == 404
        data = json.loads(response_tuple[0].data)
        assert data['error'] == 'User not found'
    
    @patch('src.database.user_operations.get_db_connection')
    def test_update_user_success(self, mock_get_db, sample_user, app_context):
        """Test successful user update returns updated user data"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        updated_user = sample_user.copy()
        updated_user['username'] = 'updated_user'
        mock_cursor.fetchone.side_effect = [sample_user, updated_user]
        
        args = {'user_id': 1, 'username': 'updated_user'}
        response = update_user(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['username'] == 'updated_user'
        mock_conn.commit.assert_called_once()
    
    @patch('src.database.user_operations.get_db_connection')
    def test_update_user_not_found(self, mock_get_db, app_context):
        """Test update_user returns 404 error when trying to update non-existent user"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = None
        
        args = {'user_id': 999, 'username': 'new_name'}
        response_tuple = update_user(args)
        
        assert response_tuple[1] == 404
        data = json.loads(response_tuple[0].data)
        assert data['error'] == 'User not found'
    
    @patch('src.database.user_operations.get_db_connection')
    def test_update_user_no_fields(self, mock_get_db, sample_user, app_context):
        """Test update_user returns 400 error when no fields are provided for update"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        args = {'user_id': 1}
        response_tuple = update_user(args)
        
        assert response_tuple[1] == 400
        data = json.loads(response_tuple[0].data)
        assert data['error'] == 'No fields to update'
    
    @patch('src.database.user_operations.get_db_connection')
    def test_delete_user_success(self, mock_get_db, sample_user, app_context):
        """Test successful user deletion returns success message"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = sample_user
        
        args = {'user_id': 1}
        response = delete_user(args)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['message'] == 'User deleted successfully'
        mock_conn.commit.assert_called_once()
    
    @patch('src.database.user_operations.get_db_connection')
    def test_delete_user_not_found(self, mock_get_db, app_context):
        """Test delete_user returns 404 error when trying to delete non-existent user"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchone.return_value = None
        
        args = {'user_id': 999}
        response_tuple = delete_user(args)
        
        assert response_tuple[1] == 404
        data = json.loads(response_tuple[0].data)
        assert data['error'] == 'User not found'
    
    @patch('src.database.user_operations.get_db_connection')
    def test_get_users_for_llm(self, mock_get_db, sample_users):
        """Test get_users_for_llm returns user data in format suitable for LLM processing"""
        mock_conn, mock_cursor = self.setup_mock_db(mock_get_db)
        mock_cursor.fetchall.return_value = sample_users
        
        result = get_users_for_llm()
        
        assert len(result) == 2
        assert result[0]['username'] == 'john_doe'
        assert result[1]['username'] == 'jane_smith'
    
    def setup_mock_db(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db.return_value = mock_conn
        return mock_conn, mock_cursor