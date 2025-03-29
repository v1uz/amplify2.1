import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

class ContentExtractor:
    """Utility for extracting content from webpages for analysis."""
    
    def __init__(self, headers: Optional[Dict[str, str]] = None):
        """
        Initialize the content extractor.
        
        Args:
            headers: Optional HTTP headers to use for requests
        """
        self.headers = headers or {
            'User-Agent': 'Amplify SEO Analyzer/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml'
        }
    
    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a URL.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Extract the content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            # Get the main text content
            text = soup.get_text(separator='\n')
            
            # Clean the text
            text = self._clean_text(text)
            
            # Extract metadata
            title = self._get_title(soup)
            description = self._get_meta_description(soup)
            
            return {
                "url": url,
                "title": title,
                "meta_description": description,
                "content": text,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {
                "url": url,
                "content": "",
                "status": "error",
                "error": str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: The raw extracted text
            
        Returns:
            Cleaned text
        """
        # Replace multiple newlines with a single one
        text = re.sub(r'\n+', '\n', text)
        
        # Replace multiple spaces with a single one
        text = re.sub(r'\s+', ' ', text)
        
        # Split into lines and trim each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    def _get_title(self, soup: BeautifulSoup) -> str:
        """Extract the page title."""
        title_tag = soup.find('title')
        return title_tag.get_text() if title_tag else ""
    
    def _get_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract the meta description."""
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta.get('content', "") if meta else ""