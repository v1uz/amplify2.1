"""
URL validation utilities for the Amplify SEO application.
"""
import re
import urllib.parse
import ipaddress
import socket
import logging
from typing import Tuple, Dict, Any, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)

# Common TLDs for validation
COMMON_TLDS = {
    # Generic TLDs
    'com', 'org', 'net', 'int', 'edu', 'gov', 'mil', 'biz', 'info', 'name', 
    'pro', 'aero', 'coop', 'museum', 'app', 'dev', 'io', 'co', 'me', 'online',
    'store', 'xyz', 'site', 'shop', 'blog', 'tech', 'ai', 
    
    # Country code TLDs (selected)
    'ru', 'us', 'uk', 'ca', 'au', 'de', 'fr', 'es', 'it', 'cn', 'jp', 'br',
    'mx', 'in', 'kr', 'nl', 'se', 'no', 'fi', 'dk', 'pl', 'cz', 'at', 'ch',
    'be', 'ie', 'nz', 'sg', 'ae', 'za'
}

def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        Boolean indicating if the URL is valid
    """
    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        
        # Check for minimum requirements
        if not all([parsed.scheme, parsed.netloc]):
            return False
        
        # Check scheme
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Check for valid domain format
        domain = parsed.netloc.split(':')[0]  # Remove port if present
        
        # Check for IP address
        try:
            ipaddress.ip_address(domain)
            return True  # Valid IP address
        except ValueError:
            pass  # Not an IP, continue with domain validation
        
        # Check domain format
        domain_parts = domain.split('.')
        if len(domain_parts) < 2:
            return False
        
        # Check TLD
        tld = domain_parts[-1].lower()
        if len(tld) < 2:
            return False
            
        # Special check for common TLDs
        if len(domain_parts) == 2 and tld not in COMMON_TLDS:
            # For 2-part domains, check if TLD is common
            return False
            
        # Check domain characters
        domain_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$')
        for part in domain_parts:
            if not domain_pattern.match(part):
                return False
                
        return True
        
    except Exception:
        return False

def normalize_url(url: str) -> str:
    """
    Normalize a URL by adding protocol if missing, removing www, etc.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        
        # Upgrade HTTP to HTTPS
        scheme = 'https'
        
        # Remove www if present
        netloc = parsed.netloc
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        
        # Remove trailing slash from path
        path = parsed.path
        if path == '/':
            path = ''
        elif path.endswith('/'):
            path = path[:-1]
        
        # Remove fragment
        fragment = ''
        
        # Remove empty query
        query = parsed.query
        if not query:
            query = ''
        
        # Reconstruct URL
        normalized = urllib.parse.urlunparse((
            scheme,
            netloc,
            path,
            parsed.params,
            query,
            fragment
        ))
        
        return normalized
        
    except Exception:
        # If normalization fails, return original URL
        return url

def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        
        # Extract domain
        domain = parsed.netloc
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
            
        # Remove www if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
        
    except Exception:
        # If extraction fails, return original URL
        return url

def check_url_accessibility(url: str, timeout: int = 5) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a URL is accessible by attempting to resolve its domain.
    
    Args:
        url: URL to check
        timeout: Timeout in seconds
        
    Returns:
        Tuple with (success, info_dict)
    """
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        
        # Extract domain
        domain = parsed.netloc.split(':')[0]  # Remove port if present
        
        # Try to resolve domain
        ip = socket.gethostbyname(domain)
        
        return True, {
            'domain': domain,
            'ip': ip,
            'accessible': True,
            'error': None
        }
        
    except socket.gaierror:
        return False, {
            'domain': domain if 'domain' in locals() else None,
            'ip': None,
            'accessible': False,
            'error': 'Domain could not be resolved'
        }
    except Exception as e:
        return False, {
            'domain': domain if 'domain' in locals() else None,
            'ip': None,
            'accessible': False,
            'error': str(e)
        }

def get_url_info(url: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a URL.
    
    Args:
        url: URL to get information for
        
    Returns:
        Dictionary with URL information
    """
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        
        # Extract components
        scheme = parsed.scheme
        netloc = parsed.netloc
        path = parsed.path
        query = parsed.query
        fragment = parsed.fragment
        
        # Extract domain and subdomains
        domain_parts = netloc.split(':')[0].split('.')
        tld = domain_parts[-1] if len(domain_parts) > 1 else ''
        
        # Determine domain level
        if len(domain_parts) > 2:
            domain = f"{domain_parts[-2]}.{domain_parts[-1]}"
            subdomains = '.'.join(domain_parts[:-2])
        else:
            domain = netloc.split(':')[0]
            subdomains = None
            
        # Check if www is present
        has_www = netloc.startswith('www.')
        
        # Extract port if present
        port = None
        if ':' in netloc:
            port = netloc.split(':')[1]
            
        # Check accessibility
        accessible, access_info = check_url_accessibility(url)
        
        return {
            'original_url': url,
            'normalized_url': normalize_url(url),
            'scheme': scheme,
            'domain': domain,
            'subdomains': subdomains,
            'tld': tld,
            'has_www': has_www,
            'port': port,
            'path': path,
            'query': query,
            'query_params': dict(urllib.parse.parse_qsl(query)),
            'fragment': fragment,
            'accessible': accessible,
            'ip': access_info.get('ip')
        }
        
    except Exception as e:
        return {
            'original_url': url,
            'error': str(e),
            'valid': False
        }