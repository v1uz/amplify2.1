"""
Website analyzer module for Amplify SEO application.

This module contains functions for analyzing websites and extracting
relevant information for SEO analysis.
"""
import html
import logging
import time
import openai
import requests
from bs4 import BeautifulSoup
import re
from app.utils.pagespeed_utils import get_pagespeed_data
from app.utils.cache_manager import cache
from flask import request
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, List, Optional, Union
from flask import current_app
openai.api_key = "OPENAI_API_KEY"

logger = logging.getLogger(__name__)

# Import BERT description generator
from app.services.bert_service import BERTDescriptionGenerator

try:
    from app.services.description_enhancer import enhance_description, process_website_content
    description_enhancement_available = True
    logger.info("Description enhancer loaded successfully")
except ImportError as e:
    logger.error(f"Error importing description enhancer: {str(e)}")
    process_website_content = None
    description_enhancement_available = False

def analyze_website(url: str, generate_description: bool = True, enhance_with_gpt: bool = True, 
                   description_tone: str = "professional") -> Dict[str, Any]:
    """
    Analyze a website and extract SEO-relevant information.
    
    Args:
        url: URL of the website to analyze
        generate_description: Whether to generate a description using BERT
        enhance_with_gpt: Whether to enhance the BERT description with GPT
        description_tone: Tone to use for the enhanced description
        
    Returns:
        Dictionary containing analysis results
    """
    
    if request.args.get('no_cache'):
        cache.delete(f"analysis_{url}")
        
    logger.info(f"Starting analysis for: {url}")
    start_time = time.time()
    
    results = {
        "url": url,
        "metrics": {},
        "content": "",
        "descriptions": {}
    }
    
    # Normalize URL if needed
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Fetch the website content with improved error handling
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        # Handle 403 Forbidden errors with a more detailed error message
        if response.status_code == 403:
            logger.error(f"Access forbidden (403) for URL: {url}. The website may be blocking web scrapers.")
            results["error"] = f"Access forbidden (403) for URL: {url}. The website may be blocking web scrapers or require authentication."
            results["execution_time"] = time.time() - start_time
            return results
            
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(f"Failed to fetch URL: {url}, status code: {response.status_code}")
            results["error"] = f"Failed to fetch URL: {url}, status code: {response.status_code}"
            results["execution_time"] = time.time() - start_time
            return results
            
    except requests.exceptions.SSLError:
        logger.warning(f"SSL error encountered for {url}, retrying with verification disabled")
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch URL after SSL bypass: {url}, status code: {response.status_code}")
                results["error"] = f"Failed to fetch URL: {url}, status code: {response.status_code}"
                results["execution_time"] = time.time() - start_time
                return results
        except Exception as e:
            logger.error(f"Error fetching URL with SSL verification disabled: {str(e)}")
            results["error"] = f"Error fetching URL: {str(e)}"
            results["execution_time"] = time.time() - start_time
            return results
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error when fetching URL: {url}")
        results["error"] = f"Timeout error when fetching URL: {url}. The server took too long to respond."
        results["execution_time"] = time.time() - start_time
        return results
        
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error when fetching URL: {url}")
        results["error"] = f"Connection error when fetching URL: {url}. The server could not be reached."
        results["execution_time"] = time.time() - start_time
        return results
        
    except Exception as e:
        logger.error(f"Unexpected error when fetching URL {url}: {str(e)}")
        results["error"] = f"Error fetching URL: {str(e)}"
        results["execution_time"] = time.time() - start_time
        return results
    
    # Parse HTML and run analysis components
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        results["content"] = response.text
        
        # Extract the title with error handling
        try:
            title = soup.title.string if soup.title else None
            results["metrics"]["title"] = title
        except Exception as e:
            logger.error(f"Error extracting title: {str(e)}")
            results["metrics"]["title"] = None
        
        # Run all analysis components with individual error handling
        try:
            results["metrics"]["meta_analysis"] = analyze_meta_tags(soup)
        except Exception as e:
            logger.error(f"Error analyzing meta tags: {str(e)}")
            results["metrics"]["meta_analysis"] = {"error": str(e)}
        
        try:
            results["metrics"]["content_analysis"] = analyze_content(soup)
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            results["metrics"]["content_analysis"] = {"error": str(e)}
        
        try:
            results["metrics"]["technical_analysis"] = analyze_technical(soup, url)
        except Exception as e:
            logger.error(f"Error analyzing technical aspects: {str(e)}")
            results["metrics"]["technical_analysis"] = {"error": str(e)}
        
        try:
            results["metrics"]["mobile_analysis"] = analyze_mobile(soup)
        except Exception as e:
            logger.error(f"Error analyzing mobile aspects: {str(e)}")
            results["metrics"]["mobile_analysis"] = {"error": str(e)}
            
        # Calculate overall score
        try:
            meta_score = results["metrics"]["meta_analysis"].get("meta_score", 0)
            content_score = results["metrics"]["content_analysis"].get("readability_score", 0)
            technical_score = results["metrics"]["technical_analysis"].get("technical_score", 0)
            mobile_score = results["metrics"]["mobile_analysis"].get("mobile_score", 0)
            
            # Calculate weighted average of component scores
            overall_score = int((meta_score * 0.3) + (content_score * 0.3) + 
                        (technical_score * 0.25) + (mobile_score * 0.15))
            
            results["metrics"]["overall_score"] = overall_score
        except Exception as e:
            logger.error(f"Error calculating overall score: {str(e)}")
            results["metrics"]["overall_score"] = 0
            
    except Exception as e:
        logger.error(f"Error parsing HTML content: {str(e)}")
        results["error"] = f"Error parsing website content: {str(e)}"
        results["execution_time"] = time.time() - start_time
        return results
    
    # Generate descriptions if requested
    if generate_description:
        try:
            descriptions = generate_enhanced_description(
                html_content=response.text,
                enhance=enhance_with_gpt and description_enhancement_available,
                tone=description_tone
            )
            results["descriptions"] = descriptions
            
            # Generate customer profile
            try:
                analyzer = SEOAnalyzer()
                icl_result = analyzer._perform_analysis_with_icl(url, f"Create a customer profile for website: {url}")
                if icl_result.get('success', False):
                    results["ideal_customer_profile"] = {
                        "demographics": icl_result['analysis'],
                        "interests": "Generated by ChatGPT",
                        "behavior": "See full analysis above",
                        "needs": "Generated by ChatGPT",
                        "pain_points": "Generated by ChatGPT"
                    }
                else:
                    results["ideal_customer_profile"] = {"error": icl_result.get('error', 'Unknown error')}
            except Exception as e:
                logger.error(f"Error generating customer profile: {str(e)}")
                results["ideal_customer_profile"] = {"error": str(e)}
        except Exception as e:
            logger.error(f"Error generating descriptions: {str(e)}")
            results["descriptions"] = {"error": str(e)}

    # PageSpeed analysis
    try:
        # Initialize PageSpeed parameters
        pagespeed_timeout = 30  # Define timeout variable explicitly
        
        results["metrics"]["pagespeed"] = get_pagespeed_data(url)
    except Exception as e:
        logger.error(f"PageSpeed analysis failed: {str(e)}")
        results["metrics"]["pagespeed"] = {
            "performance_score": 0, 
            "status": "error", 
            "message": str(e)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing website {url}: {str(e)}")
        results["error"] = f"Error analyzing website: {str(e)}"

# Calculate execution time
    execution_time = time.time() - start_time
    results["execution_time"] = execution_time

    logger.info(f"Analysis completed for {url} in {execution_time:.2f} seconds")

    return results

def analyze_meta_tags(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Analyze meta tags in the HTML.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML
        
    Returns:
        Dictionary with meta tag analysis
    """
    meta_analysis = {
        "meta_score": 0,
        "title": {
            "has_title": False,
            "length": 0,
            "content": ""
        },
        "description": {
            "has_description": False,
            "length": 0,
            "content": ""
        },
        "keywords": {
            "has_keywords": False,
            "count": 0,
            "content": []
        }
    }
    
    # Check title
    title_tag = soup.title
    if title_tag and title_tag.string:
        title_content = title_tag.string.strip()
        meta_analysis["title"]["has_title"] = True
        meta_analysis["title"]["length"] = len(title_content)
        meta_analysis["title"]["content"] = title_content
    
    # Check meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc_content = meta_desc['content'].strip()
        meta_analysis["description"]["has_description"] = True
        meta_analysis["description"]["length"] = len(desc_content)
        meta_analysis["description"]["content"] = desc_content
    
    # Check meta keywords
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    if meta_keywords and meta_keywords.get('content'):
        keywords_content = meta_keywords['content'].strip()
        keywords_list = [k.strip() for k in keywords_content.split(',')]
        meta_analysis["keywords"]["has_keywords"] = True
        meta_analysis["keywords"]["count"] = len(keywords_list)
        meta_analysis["keywords"]["content"] = keywords_list
    
    # Calculate meta score (simple scoring)
    score = 0
    
    # Title scoring
    if meta_analysis["title"]["has_title"]:
        title_length = meta_analysis["title"]["length"]
        if 30 <= title_length <= 60:
            score += 30  # Optimal title length
        elif title_length < 30:
            score += 15  # Too short
        else:
            score += 20  # Too long
    
    # Description scoring
    if meta_analysis["description"]["has_description"]:
        desc_length = meta_analysis["description"]["length"]
        if 120 <= desc_length <= 158:
            score += 30  # Optimal description length
        elif desc_length < 120:
            score += 15  # Too short
        else:
            score += 20  # Too long
    
    # Keywords scoring
    if meta_analysis["keywords"]["has_keywords"]:
        keywords_count = meta_analysis["keywords"]["count"]
        if 5 <= keywords_count <= 10:
            score += 10  # Optimal number of keywords
        elif keywords_count < 5:
            score += 5  # Too few
        else:
            score += 7  # Too many
    
    # Add robots meta check
    robots_meta = soup.find('meta', attrs={'name': 'robots'})
    meta_analysis["robots"] = {
        "has_robots": bool(robots_meta),
        "content": robots_meta['content'] if robots_meta and robots_meta.get('content') else ""
    }
    
    if meta_analysis["robots"]["has_robots"]:
        score += 10
    
    # Add viewport check
    viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
    meta_analysis["viewport"] = {
        "has_viewport": bool(viewport_meta),
        "content": viewport_meta['content'] if viewport_meta and viewport_meta.get('content') else ""
    }
    
    if meta_analysis["viewport"]["has_viewport"]:
        score += 10
    
    # Add charset check
    charset_meta = soup.find('meta', attrs={'charset': True})
    meta_analysis["charset"] = {
        "has_charset": bool(charset_meta),
        "content": charset_meta['charset'] if charset_meta and charset_meta.get('charset') else ""
    }
    
    if meta_analysis["charset"]["has_charset"]:
        score += 10
    
    # Set final score
    meta_analysis["meta_score"] = min(score, 100)
    
    return meta_analysis


def analyze_content(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Analyze the content of the HTML.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML
        
    Returns:
        Dictionary with content analysis
    """
    content_analysis = {
        "readability_score": 0,
        "word_count": 0,
        "heading_count": {
            "h1": 0,
            "h2": 0,
            "h3": 0,
            "h4": 0,
            "h5": 0,
            "h6": 0
        },
        "has_headings": False,
        "image_count": 0,
        "images_with_alt": 0,
        "link_count": 0
    }
    
    # Extract all text from the page
    body = soup.body
    if not body:
        return content_analysis
    
    # Get all text
    texts = body.find_all(text=True)
    visible_texts = [t.strip() for t in texts if t.parent.name not in [
        'style', 'script', 'head', 'title', 'meta', '[document]'
    ]]
    content_text = ' '.join(visible_texts).strip()
    
    # Count words
    words = re.findall(r'\b\w+\b', content_text)
    content_analysis["word_count"] = len(words)
    
    # Count headings
    for i in range(1, 7):
        headings = soup.find_all(f'h{i}')
        content_analysis["heading_count"][f"h{i}"] = len(headings)
    
    # Check if there are any headings
    total_headings = sum(content_analysis["heading_count"].values())
    content_analysis["has_headings"] = total_headings > 0
    
    # Count images
    images = soup.find_all('img')
    content_analysis["image_count"] = len(images)
    
    # Count images with alt text
    images_with_alt = [img for img in images if img.get('alt')]
    content_analysis["images_with_alt"] = len(images_with_alt)
    
    # Count links
    links = soup.find_all('a')
    content_analysis["link_count"] = len(links)
    
    # Calculate readability score (simple implementation)
    score = 0
    
    # Word count scoring
    if content_analysis["word_count"] > 300:
        score += 20
    elif content_analysis["word_count"] > 100:
        score += 10
    
    # Headings scoring
    if content_analysis["has_headings"]:
        score += 20
        if content_analysis["heading_count"]["h1"] == 1:
            score += 10  # One H1 is optimal
        if content_analysis["heading_count"]["h2"] > 0:
            score += 10  # Has H2 headings
    
    # Image scoring
    if content_analysis["image_count"] > 0:
        score += 10
        if content_analysis["images_with_alt"] == content_analysis["image_count"]:
            score += 10  # All images have alt text
    
    # Link scoring
    if content_analysis["link_count"] > 0:
        score += 10
    
    # Paragraph analysis
    paragraphs = soup.find_all('p')
    if len(paragraphs) > 3:
        score += 10
    
    # Set final score
    content_analysis["readability_score"] = min(score, 100)
    
    return content_analysis


def analyze_technical(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """
    Analyze technical SEO aspects of the HTML.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML
        url: URL of the website
        
    Returns:
        Dictionary with technical analysis
    """
    technical_analysis = {
        "technical_score": 0,
        "canonical": {
            "has_canonical": False,
            "url": ""
        },
        "schema_markup": {
            "has_schema": False,
            "types": []
        },
        "hreflang": {
            "has_hreflang": False,
            "langs": []
        }
    }
    
    # Check canonical URL
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if canonical and canonical.get('href'):
        technical_analysis["canonical"]["has_canonical"] = True
        technical_analysis["canonical"]["url"] = canonical['href']
    
    # Check for schema markup
    schema_tags = soup.find_all(['script', 'div'], attrs={'type': 'application/ld+json'})
    if schema_tags:
        technical_analysis["schema_markup"]["has_schema"] = True
        schema_types = []
        for tag in schema_tags:
            try:
                if tag.string:
                    import json
                    schema_data = json.loads(tag.string)
                    if '@type' in schema_data:
                        schema_types.append(schema_data['@type'])
            except:
                pass
        technical_analysis["schema_markup"]["types"] = schema_types
    
    # Check for hreflang
    hreflang_tags = soup.find_all('link', attrs={'rel': 'alternate', 'hreflang': True})
    if hreflang_tags:
        technical_analysis["hreflang"]["has_hreflang"] = True
        langs = [tag['hreflang'] for tag in hreflang_tags if tag.get('hreflang')]
        technical_analysis["hreflang"]["langs"] = langs
    
    # Calculate technical score
    score = 0
    
    # Canonical scoring
    if technical_analysis["canonical"]["has_canonical"]:
        score += 30
    
    # Schema markup scoring
    if technical_analysis["schema_markup"]["has_schema"]:
        score += 30
        if technical_analysis["schema_markup"]["types"]:
            score += 10  # Has identified schema types
    
    # Hreflang scoring
    if technical_analysis["hreflang"]["has_hreflang"]:
        score += 20
    
    # Set final score
    technical_analysis["technical_score"] = min(score, 100)
    
    return technical_analysis


def analyze_mobile(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Analyze mobile optimization aspects of the HTML.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML
        
    Returns:
        Dictionary with mobile optimization analysis
    """
    mobile_analysis = {
        "mobile_score": 0,
        "viewport": {
            "has_viewport": False,
            "content": ""
        },
        "responsive_css": {
            "has_media_queries": False,
            "media_query_count": 0
        },
        "touch_targets": {
            "small_buttons": 0
        }
    }
    
    # Check viewport meta tag
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if viewport and viewport.get('content'):
        mobile_analysis["viewport"]["has_viewport"] = True
        mobile_analysis["viewport"]["content"] = viewport['content']
    
    # Check for responsive CSS (media queries)
    style_tags = soup.find_all('style')
    for style in style_tags:
        if style.string and '@media' in style.string:
            mobile_analysis["responsive_css"]["has_media_queries"] = True
            mobile_analysis["responsive_css"]["media_query_count"] += style.string.count('@media')
    
    # Also check for linked stylesheets (can't analyze but can check if present)
    link_tags = soup.find_all('link', attrs={'rel': 'stylesheet'})
    mobile_analysis["responsive_css"]["stylesheet_count"] = len(link_tags)
    
    # Basic touch target analysis
    small_buttons = 0
    buttons = soup.find_all(['button', 'a'])
    for button in buttons:
        # Check if style contains dimensions (very basic check)
        style = button.get('style', '')
        if 'width' in style and any(f'{i}px' in style for i in range(1, 30)):
            small_buttons += 1
    
    mobile_analysis["touch_targets"]["small_buttons"] = small_buttons
    
    # Calculate mobile score
    score = 0
    
    # Viewport scoring
    if mobile_analysis["viewport"]["has_viewport"]:
        score += 40
        if 'width=device-width' in mobile_analysis["viewport"]["content"]:
            score += 10  # Has proper device width
    
    # Responsive CSS scoring
    if mobile_analysis["responsive_css"]["has_media_queries"]:
        score += 30
        if mobile_analysis["responsive_css"]["media_query_count"] > 2:
            score += 10  # Has multiple media queries
    
    # Touch targets scoring
    if mobile_analysis["touch_targets"]["small_buttons"] == 0:
        score += 10  # No small buttons detected
    
    # Set final score
    mobile_analysis["mobile_score"] = min(score, 100)
    
    return mobile_analysis


def generate_enhanced_description(html_content: str, enhance: bool = True, 
                                tone: str = "professional") -> Dict[str, Any]:
    descriptions = {
        "bert_description": "",
        "enhanced_description": "",
        "bert_confidence": 0.0,
        "generation_time": 0
    }
    
    start_time = time.time()
    gpt_result = None  # Initialize the variable
    
    try:
        # Extract meta description directly first
        soup = BeautifulSoup(html_content, 'html.parser')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = ""
        if meta_desc and meta_desc.get('content'):
            meta_description = meta_desc['content'].strip()
            descriptions["bert_description"] = meta_description
            descriptions["bert_confidence"] = 1.0  # High confidence for meta description
        
        # Always enhance when meta description exists and enhancement is requested
        if enhance and meta_description and description_enhancement_available:
            try:
                # Try direct GPT enhancement with the meta description
                gpt_result = process_website_content(html_content, tone=tone)
                
                if gpt_result and "description" in gpt_result and gpt_result["description"]:
                    descriptions["enhanced_description"] = html.unescape(gpt_result["description"])
                    descriptions["generation_method"] = "gpt-direct-from-meta"
                    descriptions["generation_time"] = time.time() - start_time
                    return descriptions
            except Exception as e:
                logger.warning(f"GPT enhancement failed: {str(e)}")
                # Fall back to meta description
                descriptions["enhanced_description"] = meta_description
                
        # If meta description exists but no enhancement occurred
        if meta_description and not descriptions["enhanced_description"]:
            descriptions["enhanced_description"] = meta_description
            
        # Continue with BERT fallback only if no meta description found
        if not meta_description:
            bert_generator = BERTDescriptionGenerator()
            bert_result = bert_generator.process_webpage_content(html_content)
            
            if bert_result is None:
                logger.error("BERT generator returned None result")
                descriptions["error"] = "BERT description generation failed"
                descriptions["generation_time"] = time.time() - start_time
                return descriptions
            
            descriptions["bert_description"] = html.unescape(bert_result.get("description", ""))
            descriptions["bert_confidence"] = bert_result.get("confidence", 0.0)
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        descriptions["error"] = str(e)
    
    logger.info(f"Meta description found: {meta_description}")
    if gpt_result:  # Only log if gpt_result is defined
        logger.info(f"GPT enhancement result: {gpt_result}")
    logger.info(f"Final descriptions: {descriptions}")
    return descriptions


from app.services.icl_generator import ICLGenerator

class SEOAnalyzer:
    def __init__(self):
        self.icl_generator = ICLGenerator()
        
    def analyze_website(self, url):
        """Analyze a website's SEO with ICL-based approach"""
        # Generate ICL prompt based on the website's meta data
        icl_prompt = self.icl_generator.generate_icl_prompt(url)
        
        # Use the ICL prompt to perform analysis
        # This could involve sending the prompt to an LLM API
        analysis_results = self._perform_analysis_with_icl(url, icl_prompt)
        
        return analysis_results
        
    def _perform_analysis_with_icl(self, url, icl_prompt):
        """Perform analysis using the ICL prompt"""
        # Here you would implement the LLM API call
        # For example, using OpenAI's API or similar
        
        # Example implementation (placeholder)
        try:
            # This is where you'd make the API call to ChatGPT
            response = openai.ChatCompletion.create(
                 model="gpt-4",
                 messages=[
                     {"role": "system", "content": "You are the SEO expert who best describes the profile of the ideal client. "},
                     {"role": "user", "content": icl_prompt}
                 ]
             )
            analysis = response.choices[0].message.content
            logger.info(f"Customer profile source: {analysis[:100]}")
            
            # Placeholder for actual implementation
            
            return {
                "success": True,
                "url": url,
                "analysis": analysis
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }