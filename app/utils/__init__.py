"""
Utility functions for the Amplify SEO application.
"""
import logging
import time
import re
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, HTML tags, and normalizing spaces.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Replace newlines, tabs, and multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    return text.strip()

def validate_url(url: str) -> str:
    """
    Validate and normalize URL by ensuring it has a protocol prefix.
    
    Args:
        url: URL to validate and normalize
        
    Returns:
        Normalized URL
    """
    # Add http:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Parse and normalize URL
    parsed = urllib.parse.urlparse(url)
    
    # Convert to lowercase
    normalized_url = parsed.geturl()
    
    return normalized_url

def truncate_text(text: str, max_length: int = 100, append_ellipsis: bool = True) -> str:
    """
    Truncate text to a specified maximum length.
    
    Args:
        text: Input text to truncate
        max_length: Maximum length for truncated text
        append_ellipsis: Whether to append ellipsis to truncated text
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
        
    if len(text) <= max_length:
        return text
        
    truncated = text[:max_length].strip()
    if append_ellipsis:
        truncated += "..."
        
    return truncated

def extract_keywords(text: str, max_keywords: int = 10, min_word_length: int = 3) -> List[str]:
    """
    Extract keywords from text using a simple frequency-based approach.
    
    Args:
        text: Input text to extract keywords from
        max_keywords: Maximum number of keywords to extract
        min_word_length: Minimum length of words to consider as keywords
        
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
    
    # Load stop words (common words to exclude)
    stop_words = set([
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
        "at", "from", "by", "with", "about", "against", "between", "into",
        "through", "during", "before", "after", "above", "below", "to", "from",
        "up", "down", "in", "out", "on", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "all", "any", "both",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
        "can", "will", "just", "don", "should", "now", "d", "ll", "m", "o",
        "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn",
        "hasn", "haven", "isn", "ma", "mightn", "mustn", "needn", "shan",
        "shouldn", "wasn", "weren", "won", "wouldn", "для", "как", "что", "это"
    ])
    
    # Clean text
    clean = clean_text(text.lower())
    
    # Extract words
    words = re.findall(r'\b[a-zA-Zа-яА-Я0-9]+\b', clean)
    
    # Filter words
    filtered_words = [word for word in words 
                     if len(word) >= min_word_length and word not in stop_words]
    
    # Count word frequencies
    word_counts = {}
    for word in filtered_words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Extract top keywords
    keywords = [word for word, count in sorted_words[:max_keywords]]
    
    return keywords

def debug_bert_service(bert_service: Any, url: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
    """
    Debug the BERT service to identify issues with description generation.
    Can be called from a route handler for diagnostics.
    
    Args:
        bert_service: Instance of BERTDescriptionGenerator
        url: Optional URL to fetch content from
        content: Optional content string to analyze directly
        
    Returns:
        Dictionary with debug information
    """
    debug_info = {
        "model_loaded": bert_service.model_loaded,
        "device": bert_service.device if hasattr(bert_service, 'device') else 'unknown',
        "tests": []
    }
    
    # Test 1: Check if model is loaded
    if not bert_service.model_loaded:
        debug_info["tests"].append({
            "name": "model_loading",
            "passed": False,
            "message": "Model not loaded. Check paths and permissions."
        })
        return debug_info
    
    # Use provided content or a test string
    test_content = content or """
    VivaChoco is a premium chocolate factory specializing in handcrafted chocolates 
    using the finest cocoa beans from around the world. Our mission is to create 
    exceptional chocolate experiences through sustainable and ethical practices.
    Founded in 2010, we have grown to become a recognized brand with products
    available in specialty stores across the country.
    """
    
    # Test 2: Content validation
    is_valid = bert_service.is_valid_content(test_content)
    debug_info["tests"].append({
        "name": "content_validation",
        "passed": is_valid,
        "message": "Content validation " + ("passed" if is_valid else "failed")
    })
    
    if not is_valid:
        return debug_info
    
    # Test 3: Key content extraction
    try:
        start_time = time.time()
        extracted = bert_service.extract_key_content(test_content)
        extraction_time = time.time() - start_time
        
        debug_info["tests"].append({
            "name": "content_extraction",
            "passed": bool(extracted),
            "message": f"Extracted {len(extracted)} chars in {extraction_time:.2f}s",
            "extracted_length": len(extracted)
        })
    except Exception as e:
        debug_info["tests"].append({
            "name": "content_extraction",
            "passed": False,
            "message": f"Extraction error: {str(e)}"
        })
        return debug_info
    
    # Test 4: Description generation with short timeout
    try:
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                bert_service.generate_description, 
                extracted, 
                max_length=150,
                timeout=5
            )
            try:
                result = future.result(timeout=7)  # Extra time beyond internal timeout
                generation_time = time.time() - start_time
                
                debug_info["tests"].append({
                    "name": "description_generation",
                    "passed": bool(result.get("description")),
                    "time_taken": generation_time,
                    "result": result
                })
                
                if not result.get("description") and result.get("error"):
                    debug_info["tests"].append({
                        "name": "generation_error",
                        "passed": False,
                        "message": result["error"]
                    })
            except Exception as e:
                debug_info["tests"].append({
                    "name": "description_generation",
                    "passed": False,
                    "message": f"Generation timeout or error: {str(e)}"
                })
    except Exception as e:
        debug_info["tests"].append({
            "name": "description_generation",
            "passed": False,
            "message": f"Unexpected error: {str(e)}"
        })
    
    return debug_info

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.0f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"

def safe_json_serialize(obj: Any) -> Dict[str, Any]:
    """
    Safely serialize objects to JSON, handling common non-serializable types.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable dictionary
    """
    def _serialize(o):
        if isinstance(o, (set, frozenset)):
            return list(o)
        return str(o)
    
    try:
        # First try with custom serializer
        return json.loads(json.dumps(obj, default=_serialize))
    except (TypeError, ValueError):
        # If that fails, convert to string representation
        if isinstance(obj, dict):
            return {str(k): safe_json_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [safe_json_serialize(item) for item in obj]
        else:
            return str(obj)

def cache_key(url: str, params: Optional[Dict] = None) -> str:
    """
    Generate a cache key for a URL and optional parameters.
    
    Args:
        url: URL to generate key for
        params: Optional parameters to include in key
        
    Returns:
        Cache key string
    """
    # Normalize URL
    normalized_url = validate_url(url.lower())
    
    # If no params, just use the URL
    if not params:
        return f"url:{normalized_url}"
    
    # Sort params to ensure consistent key
    param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    
    # Generate key
    return f"url:{normalized_url}|params:{param_str}"