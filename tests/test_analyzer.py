"""
Tests for the SEO analyzer module.
"""

import pytest
import asyncio
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

# Import the module to test
from app.services.analyzer import analyze_seo


class TestAnalyzer:
    """Test suite for the analyzer module."""
    
    @pytest.fixture
    def sample_html(self):
        """Fixture that provides a sample HTML document for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Website - Sample Page</title>
            <meta name="description" content="This is a sample description for testing SEO analyzer">
            <meta name="keywords" content="test, seo, analyzer">
        </head>
        <body>
            <h1>Welcome to the Test Website</h1>
            <h2>Sample Section</h2>
            <p>This is a paragraph with some text.</p>
            <img src="image1.jpg" alt="Image with alt">
            <img src="image2.jpg">
            <a href="/internal-link">Internal Link</a>
            <a href="https://example.com">External Link</a>
        </body>
        </html>
        """
        
    @pytest.fixture
    def sample_pagespeed_data(self):
        """Fixture that provides sample PageSpeed data."""
        return {
            'performance_score': 85,
            'first_contentful_paint': '1.2 s',
            'largest_contentful_paint': '2.5 s',
            'time_to_interactive': '3.0 s',
            'cumulative_layout_shift': '0.1',
            'recommendations': ['Optimize images', 'Reduce JavaScript']
        }
    
    @pytest.mark.asyncio
    async def test_analyze_seo_basic(self, sample_html):
        """Test basic SEO analysis functionality without PageSpeed data."""
        # Mock the PageSpeed service to return empty data
        with patch('app.services.analyzer.get_pagespeed_insights', return_value={}):
            result = await analyze_seo(sample_html, "https://example.com")
            
        # Assert the basic structure is correct
        assert isinstance(result, dict)
        assert 'description' in result
        assert 'keywords' in result
        assert 'prompt' in result
        assert 'recommendations' in result
        assert 'metrics' in result
        
        # Assert the content is extracted correctly
        assert result['description'] == "This is a sample description for testing SEO analyzer"
        assert result['keywords'] == "test, seo, analyzer"
        assert result['metrics']['title'] == "Test Website - Sample Page"
        assert "Welcome to the Test Website" in result['metrics']['h1_tags']
        assert len(result['metrics']['h1_tags']) == 1
        assert len(result['metrics']['h2_tags']) == 1
        assert result['metrics']['img_without_alt'] == 1
        assert result['metrics']['internal_links'] == 1
        assert result['metrics']['external_links'] == 1
        
    @pytest.mark.asyncio
    async def test_analyze_seo_with_pagespeed(self, sample_html, sample_pagespeed_data):
        """Test SEO analysis with PageSpeed data integration."""
        # Mock the PageSpeed service to return sample data
        with patch('app.services.analyzer.get_pagespeed_insights', 
                  return_value=sample_pagespeed_data):
            result = await analyze_seo(sample_html, "https://example.com")
            
        # Assert PageSpeed data is integrated correctly
        assert result['metrics']['pagespeed'] == sample_pagespeed_data
        assert "Optimize images" in result['recommendations']
        assert "Reduce JavaScript" in result['recommendations']
        
    @pytest.mark.asyncio
    async def test_analyze_seo_missing_metadata(self):
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
        with patch('app.services.analyzer.get_pagespeed_insights', return_value={}):
            result = await analyze_seo(html_without_meta, "https://example.com")
        
        # Assert recommendations for missing metadata are included
        assert any("мета-описание" in rec for rec in result['recommendations'])
        assert any("мета-ключевые слова" in rec for rec in result['recommendations'])
        assert any("тег H1" in rec for rec in result['recommendations'])
        
    @pytest.mark.asyncio
    async def test_analyze_seo_pagespeed_error(self, sample_html):
        """Test handling of PageSpeed service errors."""
        error_message = "API key not provided"
        
        # Mock the PageSpeed service to return an error
        with patch('app.services.analyzer.get_pagespeed_insights', 
                  return_value={"error": error_message}):
            result = await analyze_seo(sample_html, "https://example.com")
            
        # Assert error is handled and included in recommendations
        assert result['metrics']['pagespeed']['error'] == error_message
        assert error_message in " ".join(result['recommendations'])