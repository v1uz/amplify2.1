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
from app import cache
from urllib.parse import urlparse

# Set up logging
logger = logging.getLogger(__name__)

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
    # Check cache first
    if hasattr(cache, "__contains__") and url in cache:
        logger.info(f"Cache hit for PageSpeed data: {url}")
        return cache[url]

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
        
        # Store in cache if it exists and supports item assignment
        if hasattr(cache, "__setitem__"):
            cache[url] = result
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