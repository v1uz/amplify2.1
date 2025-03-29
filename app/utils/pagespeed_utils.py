"""
PageSpeed service module.
This module handles fetching website content and PageSpeed Insights data.
"""

import aiohttp
import asyncio
import ssl
import certifi
import logging
from flask import current_app
from urllib.parse import urlparse
import requests
import time
from typing import Dict, Any
from urllib.parse import quote_plus

# Set up logging
logger = logging.getLogger(__name__)


def get_pagespeed_data(url: str, strategy: str = 'mobile', timeout: int = 60) -> Dict[str, Any]:
    """
    Fetch and analyze PageSpeed data for a given URL.
    
    Args:
        url: The URL to analyze
        strategy: Analysis strategy ('mobile' or 'desktop')
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing PageSpeed metrics and scores
    """
    
    logger.info(f"Getting PageSpeed data for URL: {url}")
    start_time = time.time()
    
    # Try to get API key from app config
    try:
        api_key = current_app.config.get('PAGESPEED_API_KEY', '')
    except RuntimeError:
        # We're not in a Flask app context
        api_key = ''

    if not api_key:
        logger.warning("PAGESPEED_API_KEY is not set")
        return {"error": "Google PageSpeed Insights API key not configured", "performance_score": 0}
        
    # Normalize and encode URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    encoded_url = quote_plus(url)
    
    # Build request URL
    base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": encoded_url,
        "strategy": strategy
    }
    
    # Add API key if available
    if api_key:
        params["key"] = api_key
    
    # Implement retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Increase timeout with each retry
            current_timeout = timeout * (attempt + 1)
            logger.info(f"PageSpeed API request attempt {attempt+1}/{max_retries} with timeout {current_timeout}s")
            
            # Make synchronous request
            response = requests.get(base_url, params=params, timeout=current_timeout)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse response
                data = response.json()
                
                # Extract relevant metrics
                lighthouse = data.get('lighthouseResult', {})
                categories = lighthouse.get('categories', {})
                performance_score = int(categories.get('performance', {}).get('score', 0) * 100)
                
                # Extract Core Web Vitals and other metrics
                audits = lighthouse.get('audits', {})
                fcp = audits.get('first-contentful-paint', {}).get('displayValue', 'N/A')
                lcp = audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
                tti = audits.get('interactive', {}).get('displayValue', 'N/A')
                cls = audits.get('cumulative-layout-shift', {}).get('displayValue', 'N/A')

                # Extract improvement opportunities
                opportunities = []
                for audit_id, audit in audits.items():
                    if audit.get('score') is not None and audit.get('score') < 0.9 and 'title' in audit:
                        opportunities.append(audit.get('title'))

                # Prepare result
                result = {
                    'performance_score': performance_score,
                    'first_contentful_paint': fcp,
                    'largest_contentful_paint': lcp,
                    'time_to_interactive': tti,
                    'cumulative_layout_shift': cls,
                    'recommendations': opportunities[:5]  # Limit to top 5 recommendations
                }
                
                # Log execution time
                execution_time = time.time() - start_time
                logger.info(f"PageSpeed data retrieved in {execution_time:.2f} seconds")
                
                return result
            
            elif response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown 400 error')
                logger.error(f"PageSpeed API 400 error: {error_message}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after 400 error...")
                    continue
                return {"performance_score": 0, "error": f"PageSpeed API error: {error_message}"}
            
            elif response.status_code == 429:
                # Rate limiting - implement exponential backoff
                from time import sleep
                wait_time = min(2 ** attempt, 60)  # Exponential backoff
                logger.warning(f"Rate limited by PageSpeed API. Waiting {wait_time} seconds...")
                sleep(wait_time)
                continue
            else:
                logger.error(f"Failed to get PageSpeed data: {response.status_code}")
                if attempt < max_retries - 1:
                    # Try again if we have retries left
                    logger.info(f"Retrying after status code {response.status_code}...")
                    continue
                return {"performance_score": 0, "error": f"PageSpeed API returned status code {response.status_code}"}
                
        except requests.exceptions.Timeout:
            logger.warning(f"PageSpeed API timeout on attempt {attempt+1}/{max_retries}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying after timeout...")
                continue
            return {"performance_score": 0, "error": "API request timed out after multiple attempts"}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request error: {str(e)}"
            logger.error(error_msg)
            if attempt < max_retries - 1:
                logger.info(f"Retrying after request exception...")
                continue
            return {"performance_score": 0, "error": error_msg}
    
    return {"performance_score": 0, "error": "Failed to get PageSpeed data after multiple attempts"}

# Keep the async functions for future use
async def fetch_website_data(url):
    """
    Asynchronously fetch website content with comprehensive error handling.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        tuple: (content, error) where content is the HTML content if successful, 
               and error is an error message if the request failed
    """
    try:
        # Basic URL validation
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = "https://" + url

        logger.info(f"Fetching data from: {url}")
        
        # Create an SSL context with the certifi CA bundle
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }, timeout=aiohttp.ClientTimeout(total=15), ssl=ssl_context) as response:
                response.raise_for_status()
                text = await response.text()
                return text, None
    except aiohttp.ClientResponseError as e:
        status_code = getattr(e, 'status', 0)
        error_msg = f"HTTP error {status_code}: {str(e)}"
        logger.error(error_msg)
        if status_code == 404:
            return None, "Page not found (404)"
        elif status_code == 403:
            return None, "Access forbidden (403)"
        elif status_code == 429:
            return None, "Too many requests (429)"
        return None, f"Error fetching URL: {str(e)}"
    except aiohttp.ClientConnectorError as e:
        logger.error(f"Connection error: {str(e)}")
        return None, "Could not connect to server. Please check the URL."
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching {url}")
        return None, "Timeout. Server not responding."
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {str(e)}")
        return None, f"An error occurred: {str(e)}"

async def get_pagespeed_insights(url):
    """
    Asynchronously fetch PageSpeed Insights data with caching.
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        dict: PageSpeed analysis results
    """
    try:
        # Try to get API key from app config
        try:
            api_key = current_app.config.get('PAGESPEED_API_KEY', '')
        except RuntimeError:
            # We're not in a Flask app context
            api_key = ''

        if not api_key:
            logger.warning("PAGESPEED_API_KEY is not set")
            return {"error": "Google PageSpeed Insights API key not configured"}
            
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={api_key}"
        
        logger.info(f"Calling PageSpeed API for: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                response.raise_for_status()
                data = await response.json()

        # Extract relevant metrics
        lighthouse = data.get('lighthouseResult', {})
        performance_score = lighthouse.get('categories', {}).get('performance', {}).get('score', 0) * 100
        
        # Extract Core Web Vitals and other metrics
        audits = lighthouse.get('audits', {})
        fcp = audits.get('first-contentful-paint', {}).get('displayValue', 'N/A')
        lcp = audits.get('largest-contentful-paint', {}).get('displayValue', 'N/A')
        tti = audits.get('interactive', {}).get('displayValue', 'N/A')
        cls = audits.get('cumulative-layout-shift', {}).get('displayValue', 'N/A')

        # Extract improvement opportunities
        opportunities = []
        for audit_id, audit in audits.items():
            if audit.get('score') is not None and audit.get('score') < 0.9 and 'title' in audit:
                opportunities.append(audit.get('title'))

        # Prepare result
        result = {
            'performance_score': performance_score,
            'first_contentful_paint': fcp,
            'largest_contentful_paint': lcp,
            'time_to_interactive': tti,
            'cumulative_layout_shift': cls,
            'recommendations': opportunities[:5]  # Limit to top 5 recommendations
        }
        
        return result
        
    except aiohttp.ClientResponseError as e:
        error_msg = f"PageSpeed API error: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    except asyncio.TimeoutError:
        error_msg = "PageSpeed API timeout"
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Error getting PageSpeed data: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}