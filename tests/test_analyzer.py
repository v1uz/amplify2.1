import pytest
from unittest.mock import patch
from bs4 import BeautifulSoup
import asyncio

# Import from the modular structure
from app.services.analyzers.meta_analyzer import MetaAnalyzer
from app.services.analyzers.content_analyzer import ContentQualityAnalyzer
from app.services.analyzers.technical_analyzer import TechnicalSEOAnalyzer
from app.services.analyzers.mobile_analyzer import MobileAnalyzer

class TestAnalyzers:
    """Tests for the analyzer modules"""

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
    def sample_parsed_html(self, sample_html):
        """Parse sample HTML with BeautifulSoup"""
        return {"soup": BeautifulSoup(sample_html, 'html.parser')}

    @pytest.mark.asyncio
    async def test_meta_analyzer(self, sample_parsed_html):
        """Test meta analyzer functionality"""
        meta_analyzer = MetaAnalyzer()
        result = await meta_analyzer.analyze("https://example.com", sample_parsed_html)
        
        # Basic assertions
        assert isinstance(result, dict)
        assert "title" in result
        assert "description" in result
        assert "recommendations" in result
        
        # Verify content extraction
        assert result["title"]["content"] == "Test Website - Sample Page"
        
        # Verify recommendations are generated
        assert isinstance(result["recommendations"], list)

    @pytest.mark.asyncio
    async def test_content_analyzer(self, sample_parsed_html):
        """Test content analyzer functionality"""
        content_analyzer = ContentQualityAnalyzer()
        result = await content_analyzer.analyze("https://example.com", sample_parsed_html)
        
        # Assertions for content analyzer
        assert "word_count" in result
        assert "readability_score" in result
        assert "recommendations" in result