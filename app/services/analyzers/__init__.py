"""
Analyzer Package Initialization
This module initializes the analyzer package and provides utilities for importing all analyzers.
"""

from app.services.analyzers.content_analyzer import ContentQualityAnalyzer
from app.services.analyzers.mobile_analyzer import MobileAnalyzer
from app.services.analyzers.technical_analyzer import TechnicalSEOAnalyzer
from app.services.analyzers.meta_analyzer import MetaAnalyzer
from app.services.analyzers.keyword_analyzer import KeywordOptimizationAnalyzer
from app.services.analyzers.competitive_analyzer import CompetitiveAnalyzer
import logging
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Set up logging
logger = logging.getLogger(__name__)

# Export all analyzer classes
__all__ = [
    'ContentQualityAnalyzer',
    'MobileAnalyzer',
    'TechnicalSEOAnalyzer',
    'MetaAnalyzer',
    'KeywordOptimizationAnalyzer',
    'CompetitiveAnalyzer'
]

def get_all_analyzers():
    """
    Get instances of all available analyzers
    
    Returns:
        list: List of analyzer instances
    """
    return [
        MetaAnalyzer(),
        ContentQualityAnalyzer(),
        KeywordOptimizationAnalyzer(),
        TechnicalSEOAnalyzer(),
        MobileAnalyzer(),
        CompetitiveAnalyzer()
    ]

# Add the legacy_analyze_seo function
async def legacy_analyze_seo(html_content, url):
    """
    Original SEO analysis implementation for backwards compatibility.
    
    Args:
        html_content (str): HTML content of the website
        url (str): URL of the website
        
    Returns:
        dict: A dictionary containing SEO analysis results
    """
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic metadata
        title = soup.title.string if soup.title else "Title not found"
        
        # Extract meta description
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_description_content = meta_description['content'] if meta_description and meta_description.has_attr('content') else " ".join([p.get_text(strip=True) for p in soup.find_all('p')[:2]])
        
        # Extract keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        keywords = keywords_meta['content'] if keywords_meta and keywords_meta.has_attr('content') else "Keywords not found"
        
        # Extract structural elements
        h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
        h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
        
        # Check for images without alt text
        img_without_alt = len([img for img in soup.find_all('img') if not img.get('alt')])
        
        # Count internal and external links
        internal_links = len([a for a in soup.find_all('a', href=True) if a['href'].startswith('/')])
        external_links = len([a for a in soup.find_all('a', href=True) if not a['href'].startswith('/') and urlparse(a['href']).netloc])
        
        # Use the modular analyzers
        raw_data = {"soup": soup}
        meta_analyzer = MetaAnalyzer()
        content_analyzer = ContentQualityAnalyzer()
        technical_analyzer = TechnicalSEOAnalyzer()
        mobile_analyzer = MobileAnalyzer()
        
        # Run specialized analyses
        meta_results = await meta_analyzer.analyze(url, raw_data)
        content_results = await content_analyzer.analyze(url, raw_data)
        technical_results = await technical_analyzer.analyze(url, raw_data)
        mobile_results = await mobile_analyzer.analyze(url, raw_data)
        
        # Compile recommendations
        all_recommendations = []
        for results in [meta_results, content_results, technical_results, mobile_results]:
            if isinstance(results, dict) and 'recommendations' in results:
                all_recommendations.extend(results['recommendations'])
        
        # PageSpeed data stub - you might want to add real implementation
        pagespeed_data = {"performance_score": 80, "recommendations": ["Optimize page loading"]}
        
        # Return in the original format
        return {
            'description': meta_description_content,
            'keywords': keywords,
            'prompt': f"Analysis for {url}",
            'recommendations': all_recommendations,
            'metrics': {
                'title': title,
                'h1_tags': h1_tags,
                'h2_tags': h2_tags,
                'img_without_alt': img_without_alt,
                'internal_links': internal_links,
                'external_links': external_links,
                'pagespeed': pagespeed_data,
                'meta_analysis': meta_results,
                'content_analysis': content_results,
                'technical_analysis': technical_results,
                'mobile_analysis': mobile_results
            }
        }
    
    except Exception as e:
        logger.error(f"Error in SEO analysis: {str(e)}")
        return {
            'description': "Error analyzing page",
            'keywords': "",
            'prompt': f"Error analyzing {url}",
            'recommendations': [f"Error: {str(e)}"],
            'metrics': {
                'title': "Error",
                'h1_tags': [],
                'h2_tags': [],
                'img_without_alt': 0,
                'internal_links': 0,
                'external_links': 0,
                'pagespeed': {}
            }
        }