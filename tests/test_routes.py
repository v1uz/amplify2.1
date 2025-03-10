"""
Tests for the application routes.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import session

# Import app factory
from app import create_app


class TestRoutes:
    """Test suite for the application routes."""
    
    @pytest.fixture
    def app(self):
        """Fixture that creates an application for testing."""
        app = create_app('testing')
        app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-key',
            'SERVER_NAME': 'localhost'
        })
        
        # Create application context
        with app.app_context():
            yield app
            
    @pytest.fixture
    def client(self, app):
        """Fixture that creates a test client."""
        return app.test_client()
    
    def test_index_route(self, client):
        """Test the main index route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Amplify' in response.data
        
    def test_amplify_route(self, client):
        """Test the Amplify analysis interface route."""
        response = client.get('/amplify')
        assert response.status_code == 200
        assert b'Analyze your website' in response.data
        
    def test_preloader_route_without_url(self, client):
        """Test the preloader route without a URL parameter."""
        response = client.get('/preloader')
        # Should redirect to the amplify page
        assert response.status_code == 302
        assert '/amplify' in response.location
        
    def test_preloader_route_with_url(self, client):
        """Test the preloader route with a URL parameter."""
        response = client.get('/preloader?url=https://example.com')
        assert response.status_code == 200
        assert b'Analyzing website' in response.data
        
    def test_result_route_without_session(self, client):
        """Test the result route without session data."""
        response = client.get('/result')
        # Should redirect to the amplify page
        assert response.status_code == 302
        assert '/amplify' in response.location
        
    def test_result_route_with_session(self, client, app):
        """Test the result route with session data."""
        # Mock session data
        sample_results = {
            'metrics': {'title': 'Test Title'},
            'description': 'Test Description',
            'keywords': 'test, keywords',
            'prompt': 'Test prompt',
            'recommendations': ['Recommendation 1', 'Recommendation 2']
        }
        
        with client.session_transaction() as sess:
            sess['seo_results'] = sample_results
            
        response = client.get('/result')
        assert response.status_code == 200
        assert b'Test Title' in response.data
        assert b'Test Description' in response.data
        
    @pytest.mark.asyncio
    async def test_analyze_route_missing_url(self, client):
        """Test the analyze route with missing URL in payload."""
        response = await client.post('/analyze', 
                               json={},
                               content_type='application/json')
        data = json.loads(response.data)
        assert response.status_code == 400
        assert 'error' in data
        
    @pytest.mark.asyncio
    async def test_analyze_route_invalid_url(self, client):
        """Test the analyze route with an invalid URL."""
        # Mock the URL validator to return invalid
        with patch('app.routes.analysis_routes.validate_url', return_value=(False, 'invalid-url')):
            response = await client.post('/analyze',
                                  json={'url': 'invalid-url'},
                                  content_type='application/json')
            data = json.loads(response.data)
            assert response.status_code == 400
            assert 'error' in data
            
    @pytest.mark.asyncio
    async def test_analyze_route_fetch_error(self, client):
        """Test the analyze route when fetch_website_data returns an error."""
        # Mock the validator to return valid
        with patch('app.routes.analysis_routes.validate_url', return_value=(True, 'https://example.com')):
            # Mock fetch_website_data to return an error
            with patch('app.routes.analysis_routes.fetch_website_data', 
                      return_value=(None, "Connection error")):
                response = await client.post('/analyze',
                                     json={'url': 'https://example.com'},
                                     content_type='application/json')
                data = json.loads(response.data)
                assert response.status_code == 400
                assert 'error' in data
                assert 'Connection error' in data['error']
                
    @pytest.mark.asyncio
    async def test_analyze_route_success(self, client):
        """Test the analyze route with successful analysis."""
        # Sample HTML content
        html_content = "<html><head><title>Test</title></head><body><h1>Test</h1></body></html>"
        
        # Sample analysis results
        analysis_results = {
            'metrics': {'title': 'Test'},
            'description': 'Test Description',
            'keywords': 'test',
            'prompt': 'Test prompt',
            'recommendations': ['Recommendation 1']
        }
        
        # Mock dependencies
        with patch('app.routes.analysis_routes.validate_url', return_value=(True, 'https://example.com')):
            with patch('app.routes.analysis_routes.fetch_website_data', 
                      return_value=(html_content, None)):
                with patch('app.routes.analysis_routes.analyze_seo', 
                          return_value=analysis_results):
                    response = await client.post('/analyze',
                                         json={'url': 'https://example.com'},
                                         content_type='application/json')
                    data = json.loads(response.data)
                    assert response.status_code == 200
                    assert 'redirect' in data
                    assert '/result' in data['redirect']
                    
                    # Verify session was set
                    with client.session_transaction() as sess:
                        assert 'seo_results' in sess
                        assert sess['seo_results'] == analysis_results