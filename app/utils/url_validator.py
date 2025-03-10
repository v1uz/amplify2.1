"""
URL validation utility module.
This module provides functionality for URL validation and normalization.
"""

from urllib.parse import urlparse
import re
import logging

# Set up logging
logger = logging.getLogger(__name__)

def validate_url(url):
    """
    Normalize URL to use https:// and validate format with detailed debugging.
    
    Args:
        url (str): The URL to validate and normalize
        
    Returns:
        tuple: (is_valid, normalized_url) where is_valid is a boolean indicating
               if the URL is valid, and normalized_url is the normalized URL
    """
    # Log original URL
    logger.debug(f"Validating URL: {url}")
    
    # Basic sanity checks
    if not url or not isinstance(url, str):
        logger.warning(f"Invalid URL input: {url}")
        return False, url
    
    # Trim whitespace
    url = url.strip()
    
    # Use a more comprehensive URL regex pattern
    url_pattern = re.compile(
        r'^(https?:\/\/)?' +  # protocol
        r'(([a-z\d]([a-z\d-]*[a-z\d])*)\.)+[a-z]{2,}' +  # domain name
        r'(\:\d+)?' +  # port
        r'(\/[-a-z\d%_.~+]*)*' +  # path
        r'(\?[;&a-z\d%_.~+=-]*)?' +  # query string
        r'(\#[-a-z\d_]*)?$',  # fragment
        re.IGNORECASE
    )
    
    # If URL doesn't match the basic pattern, check if it's missing the scheme
    if not url_pattern.match(url):
        # Try adding a scheme to see if it would be valid then
        test_url = f"https://{url}"
        if not url_pattern.match(test_url):
            logger.warning(f"URL did not match valid pattern: {url}")
            return False, url
    
    # Use urlparse for more detailed validation
    parsed = urlparse(url.strip())
    
    # If no scheme is provided, or if the scheme is http, normalize to https://
    if not parsed.scheme:
        logger.info(f"No scheme detected, normalizing to 'https://' for {url}")
        # Remove any existing http:// or https:// to avoid duplication
        url_without_scheme = url.replace('http://', '').replace('https://', '').strip('/')
        url = f'https://{url_without_scheme}'
        parsed = urlparse(url)
    # If scheme is http, upgrade to https
    elif parsed.scheme == 'http':
        logger.info(f"HTTP scheme detected, upgrading to HTTPS for {url}")
        url = f'https://{parsed.netloc}{parsed.path}'
        if parsed.params:
            url += f';{parsed.params}'
        if parsed.query:
            url += f'?{parsed.query}'
        if parsed.fragment:
            url += f'#{parsed.fragment}'
        parsed = urlparse(url)
    # If scheme is https, proceed as is
    elif parsed.scheme == 'https':
        logger.debug(f"HTTPS scheme already present for {url}")
    else:
        logger.warning(f"Unsupported scheme {parsed.scheme}, normalizing to https://")
        url_without_scheme = url.replace(f'{parsed.scheme}://', '').strip('/')
        url = f'https://{url_without_scheme}'
        parsed = urlparse(url)

    # Validate that scheme and netloc are present after normalization
    has_scheme = bool(parsed.scheme)
    has_netloc = bool(parsed.netloc)
    
    # Check for domain validity
    has_valid_domain = '.' in parsed.netloc and not parsed.netloc.startswith('.')
    
    is_valid = has_scheme and has_netloc and has_valid_domain
    
    logger.debug(f"Parsed URL: Scheme={parsed.scheme}, Netloc={parsed.netloc}, "
                 f"Path={parsed.path}, Valid={is_valid}")
    
    return is_valid, url