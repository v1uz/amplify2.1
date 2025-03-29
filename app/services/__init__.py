"""
Services package for Amplify SEO application.
"""
import logging

logger = logging.getLogger(__name__)

# Export analyzer function
try:
    from .analyzer import analyze_website
    logger.info("Analyzer module loaded successfully")
except ImportError as e:
    logger.error(f"Error importing analyzer: {str(e)}")
    def analyze_website(url, **kwargs):
        return {"error": "Analyzer module could not be loaded", "url": url}

# Remove the problematic import and use ICL generator instead
# Export ICL generator
try:
    from .icl_generator import ICLGenerator
    logger.info("ICL generator loaded successfully")
except ImportError as e:
    logger.error(f"Error importing ICL generator: {str(e)}")
    class ICLGenerator:
        def __init__(self):
            pass
        
        def generate_icl_prompt(self, url):
            domain = url.replace("http://", "").replace("https://", "").split('/')[0]
            return f"Analyze website {domain} for SEO optimization"