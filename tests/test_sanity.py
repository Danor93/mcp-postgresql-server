"""
Sanity Tests

These are quick smoke tests that verify the system is alive and basic functionality works.
Sanity tests should run in under 1 minute total and serve as a first line of defense
to ensure the application can start and respond to basic requests.

Run only sanity tests with:
    pytest tests/test_sanity.py -v
    pytest -m sanity

Run all tests except sanity:
    pytest -m "not sanity"
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import app
from src.config.database import get_db_connection
from src.middleware.auth import JWTAuth


@pytest.mark.sanity
class TestSanityChecks:
    """
    Quick sanity tests that verify core system functionality.
    These tests use mocks to avoid real database connections,
    making them fast and reliable.
    """
    
    @pytest.fixture
    def client(self):
        """
        Create a test client for the Flask app.
        This fixture is run before each test method.
        """
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def auth_header(self):
        """
        Generate a valid JWT token for authenticated requests.
        This demonstrates how to handle authentication in tests.
        """
        with app.app_context():
            auth = JWTAuth()
            token = auth.generate_token(1, 'testuser')
            return {'Authorization': f'Bearer {token}'}
    
    @pytest.mark.sanity
    @patch('src.config.database.psycopg2.connect')
    def test_database_connection_can_be_created(self, mock_connect):
        """
        Sanity Test 1: Verify database connection function can be called.
        
        This is a sanity test because:
        - It's quick (uses mocks, no real DB connection)
        - It verifies a critical component (database connectivity)
        - Failure means the system cannot function at all
        
        We use mocks to avoid needing a real database for sanity tests.
        """
        # Setup mock
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Test that get_db_connection can be called without errors
        result = get_db_connection()
        
        # Verify the connection was created
        assert result is not None
        assert mock_connect.called
    
    @pytest.mark.sanity
    def test_api_health_endpoint_exists(self, client):
        """
        Sanity Test 2: Verify the API is running and health endpoint responds.
        
        This is a sanity test because:
        - It's the most basic check that the API is alive
        - Used by load balancers and monitoring systems
        - Takes milliseconds to run
        
        We don't care about the response content, just that it doesn't 404.
        """
        response = client.get('/health')
        
        # For sanity, we just check it's not a 404
        # The response might be 200 (healthy) or 500 (unhealthy)
        # Both are fine for sanity - it means the endpoint exists
        assert response.status_code in [200, 500]
    
    @pytest.mark.sanity
    def test_authentication_endpoint_exists(self, client):
        """
        Sanity Test 3: Verify authentication system is loaded.
        
        This is a sanity test because:
        - Authentication is critical infrastructure
        - We only check the endpoint exists, not that login works
        - Ensures auth middleware is properly loaded
        
        We send dummy credentials - we don't care if login succeeds.
        """
        # Send a login request with dummy data
        response = client.post('/auth/login',
                             json={'username': 'dummy', 'password': 'dummy'})
        
        # For sanity, we just verify the endpoint exists (not 404)
        # It might return 401 (unauthorized) or 400 (bad request)
        # Both are fine - they mean auth system is working
        assert response.status_code != 404
        assert response.status_code in [200, 400, 401]
    
    @pytest.mark.sanity
    def test_mcp_tools_endpoint_exists(self, client, auth_header):
        """
        Sanity Test 4: Verify MCP tools endpoint exists and requires auth.
        
        This is a sanity test because:
        - MCP tools are the core API functionality
        - We only verify the endpoint exists and auth works
        - No database calls needed
        
        This verifies the MCP routes are properly loaded.
        """
        # Test without auth - should fail
        response = client.get('/mcp/tools')
        assert response.status_code == 401  # Unauthorized
        
        # Test with auth - should succeed
        response = client.get('/mcp/tools', headers=auth_header)
        assert response.status_code == 200


# Additional sanity test to verify test configuration
@pytest.mark.sanity
def test_pytest_configuration():
    """
    Meta-test: Verify pytest is configured correctly.
    
    This sanity test verifies:
    - pytest can run
    - Markers are recognized
    - Basic assertions work
    
    If this fails, the test infrastructure itself is broken.
    """
    assert True
    assert 1 + 1 == 2
    
    # Verify we can import our application modules
    from app import app
    from src.config.database import get_db_connection
    assert app is not None
    assert get_db_connection is not None