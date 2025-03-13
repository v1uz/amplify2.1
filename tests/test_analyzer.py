import pytest
from unittest.mock import patch
from app.services.analyzer import analyze_seo

class TestAnalyzer:
    """Tests for the analyzer.py module"""

    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Website - Sample Page</title>
            <meta name="description" content="A sample page for testing SEO analysis">
            <meta name="keywords" content="test, sample, SEO">
            <meta name="robots" content="index, follow">
        </head>
        <body>
            <h1>Welcome to Test Website</h1>
            <p>This is a sample paragraph for testing.</p>
            <h2>Subheading</h2>
            <p>Another paragraph with <strong>formatted</strong> text.</p>
            <img src="test.jpg" alt="Test Image">
            <img src="no-alt.jpg">
            <a href="/internal">Internal Link</a>
            <a href="https://example.com">External Link</a>
        </body>
        </html>
        """

    @pytest.fixture
    def sample_pagespeed_data(self):
        """Sample PageSpeed data for testing"""
        return {
            "performance_score": 85,
            "cumulative_layout_shift": "0.1",
            "first_contentful_paint": "1.2 s",
            "largest_contentful_paint": "2.5 s",
            "speed_index": "2.0 s",
            "total_blocking_time": "50 ms",
            "recommendations": [
                "Properly size images",
                "Use WOFF2 for web fonts"
            ]
        }

    # Remove @pytest.mark.asyncio and use synchronous calls
    def test_analyze_seo_basic(self, sample_html):
        """Test basic SEO analysis functionality without PageSpeed data."""
        # Mock the PageSpeed service to return empty data
        with patch('app.services.analyzer.get_pagespeed_insights_sync', return_value={}):
            result = analyze_seo(sample_html, "https://example.com")
        
        # Basic assertions
        assert isinstance(result, dict)
        assert 'metrics' in result
        assert 'recommendations' in result
        assert 'title' in result['metrics']
        
        # Verify content extraction
        assert "Test Website - Sample Page" == result['metrics']['title']
        assert len(result['metrics']['h1_tags']) == 1
        assert "Welcome to Test Website" in result['metrics']['h1_tags']
        
        # Verify recommendations are generated
        assert isinstance(result['recommendations'], list)
        assert len(result['recommendations']) > 0

    # Remove @pytest.mark.asyncio and use synchronous calls
    def test_analyze_seo_with_pagespeed(self, sample_html, sample_pagespeed_data):
        """Test SEO analysis with PageSpeed data integration."""
        # Mock the PageSpeed service to return sample data
        with patch('app.services.analyzer.get_pagespeed_insights_sync',
                  return_value=sample_pagespeed_data):
            result = analyze_seo(sample_html, "https://example.com")
        
        # Verify PageSpeed data integration
        assert 'pagespeed' in result['metrics']
        assert result['metrics']['pagespeed']['performance_score'] == 85
        
        # Check if PageSpeed recommendations are included
        pagespeed_rec = next((rec for rec in result['recommendations'] 
                              if "Properly size images" in rec), None)
        assert pagespeed_rec is not None

    # Remove @pytest.mark.asyncio and use synchronous calls
    def test_analyze_seo_missing_metadata(self):
        """Test analysis of a page with missing metadata."""
        html_without_meta = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Minimal Page</title>
        </head>
        <body>
            <p>Just a paragraph.</p>
        </body>
        </html>
        """
        
        # Mock the PageSpeed service to return empty data
        with patch('app.services.analyzer.get_pagespeed_insights_sync', return_value={}):
            result = analyze_seo(html_without_meta, "https://example.com")
        
        # Verify analysis of missing metadata
        meta_rec = next((rec for rec in result['recommendations'] 
                         if "мета-описание" in rec.lower()), None)
        assert meta_rec is not None

    # Remove @pytest.mark.asyncio and use synchronous calls
    def test_analyze_seo_pagespeed_error(self, sample_html):
        """Test handling of PageSpeed service errors."""
        error_message = "API key not provided"
        
        # Mock the PageSpeed service to return an error
        with patch('app.services.analyzer.get_pagespeed_insights_sync',
                  return_value={"error": error_message}):
            result = analyze_seo(sample_html, "https://example.com")
        
        # Verify error is included in recommendations
        error_rec = next((rec for rec in result['recommendations'] 
                          if error_message in rec), None)
        assert error_rec is not None