"""
description_enhancer.py - Module for generating and enhancing website descriptions using GPT
"""

import logging
import re
import time
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException

from openai import OpenAI

from app.utils.cache_manager import cache
from app.config import Config

# Get config variables from Config class
GPT_API_KEY = Config.GPT_API_KEY
MAX_TOKEN_LENGTH = Config.MAX_TOKEN_LENGTH
GPT_RATE_LIMIT = Config.GPT_RATE_LIMIT

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI API
client = OpenAI(api_key=GPT_API_KEY)

def extract_website_content(html_content: str) -> str:
    """Extract relevant content from website HTML, focusing on about sections"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove navigation, scripts, etc.
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # First try to find "about us" sections
        about_elements = soup.find_all(['div', 'section'], id=lambda x: x and 'about' in x.lower())
        about_elements += soup.find_all(['div', 'section'], class_=lambda x: x and 'about' in x.lower())
        about_elements += soup.find_all(['h1', 'h2', 'h3'], text=lambda x: x and 'about' in x.lower())
        
        if about_elements:
            return " ".join([el.get_text(strip=True) for el in about_elements[:3]])
        
        # Try main content
        main = soup.find('main') or soup.find('article')
        if main:
            return main.get_text(strip=True)
        
        # Fallback to body text with filtering
        body_text = soup.body.get_text(strip=True)
        # Filter out common navigation/footer text
        clean_text = re.sub(r'(cart|login|search|menu|\$\d+\.\d+)', '', body_text)
        return clean_text[:1500]  # Limit length
    except Exception as e:
        logger.error(f"Error extracting content: {e}")
        return ""

def generate_description(content: str, tone: str = "professional", language: str = 'en', max_retries: int = 3) -> Dict[str, Any]:
    """Generate company description directly with ChatGPT"""
    if not content:
        return {"description": "", "confidence": 0.0, "error": "No content provided"}
    
    # Check cache
    cache_key = f"gpt_description_{hash(content)}_{tone}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Detect language
    try:
        language = detect(content)
    except LangDetectException:
        pass
    
    # Adjust system message for language
    system_message = f"You are a professional copywriter creating concise, engaging business descriptions with a {tone} tone."
    if language == 'ru':
        system_message += " Пожалуйста, отвечайте на русском языке."
    
    prompt = (
        f"Create a professional 3-5 sentence company description from this website text. "
        f"Focus on what the business does, its unique qualities, and target audience. "
        f"Include only factual information from the text:\n\n{content}"
    )
    
    # Call OpenAI API with retries
    retry_count = 0
    description_text = ""
    
    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKEN_LENGTH,
                temperature=0.7
            )
            
            description_text = response.choices[0].message.content.strip()
            break
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                retry_count += 1
                logger.warning(f"Rate limit hit, retrying ({retry_count}/{max_retries})")
                time.sleep(GPT_RATE_LIMIT)
            else:
                logger.error(f"Error generating with GPT: {str(e)}")
                return {"description": "", "confidence": 0.0, "error": str(e)}
            
            if not description_text and retry_count >= max_retries:
                return {"description": "", "confidence": 0.0, "error": "Failed after multiple attempts"}
    
    # Create result
    result = {
        "description": description_text,
        "confidence": 0.95,
        "generation_method": "gpt-3.5-turbo"
    }
    
    # Cache the result
    cache.set(cache_key, result, ttl=86400)  # Cache for 24 hours
    
    return result

def enhance_description(bert_description: Dict[str, Any], tone: str = "professional", use_cache: bool = True) -> Dict[str, Any]:
    """
    Legacy function for compatibility - enhances BERT descriptions with GPT
    
    Args:
        bert_description: BERT-generated description
        tone: Desired tone
        use_cache: Whether to use cached results
        
    Returns:
        Enhanced description
    """
    # Skip enhancement for invalid inputs
    if ("error" in bert_description or 
        not bert_description.get("description") or 
        bert_description.get("confidence", 0.0) <= 0.1 or
        "inf" in str(bert_description.get("confidence", ""))):
        logger.warning(f"Skipping enhancement due to poor BERT output: {bert_description}")
        return bert_description
    
    # Validate description content
    desc = bert_description.get("description", "")
    if re.match(r'^(Email|Viber|Tel).+[0-9].+$', desc, re.IGNORECASE):
        return {"description": desc, "confidence": 0.0, "error": "Invalid description content"}
    
    # Check cache
    if use_cache:
        cache_key = f"enhanced_{hash(desc)}_{tone}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    
    # Enhance with GPT
    raw_description = bert_description.get("description", "")
    confidence = bert_description.get("confidence", 0.0)
    
    # Prepare prompt
    prompt = f"Enhance the following company description. Make it more detailed, engaging, and {tone}:\n\n{raw_description}"
    
    # Call OpenAI API with retries
    retry_count = 0
    enhanced_text = ""
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are an expert content enhancer with a {tone} tone."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKEN_LENGTH,
                temperature=0.7
            )
            
            enhanced_text = response.choices[0].message.content.strip()
            break
            
        except Exception as e:
            if "rate limit" in str(e).lower():
                retry_count += 1
                logger.warning(f"Rate limit hit, retrying ({retry_count}/{max_retries})")
                time.sleep(GPT_RATE_LIMIT)
            else:
                logger.error(f"Error enhancing with GPT: {str(e)}")
                return bert_description
            
            if not enhanced_text and retry_count >= max_retries:
                return bert_description
    
    # Create enhanced result
    result = {
        "original_description": raw_description,
        "enhanced_description": enhanced_text,
        "confidence": confidence,
        "enhancement_method": "gpt-3.5-turbo"
    }
    
    # Cache the result
    if use_cache:
        cache_key = f"enhanced_{hash(desc)}_{tone}"
        cache.set(cache_key, result, ttl=86400)
    
    return result

def process_website_content(html_content: str, tone: str = "professional", use_cache: bool = True) -> Dict[str, Any]:
    """
    Process website HTML directly to generate a description using GPT
    
    Args:
        html_content: Raw HTML content
        tone: Desired tone for the description
        use_cache: Whether to use cached results
        
    Returns:
        Dict with generated description
    """
    # Extract relevant content
    extracted_content = extract_website_content(html_content)
    if not extracted_content:
        return {"description": "", "error": "No relevant content extracted"}
    
    # Generate description with GPT
    return generate_description(extracted_content, tone=tone)