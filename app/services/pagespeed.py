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
from app.utils.url_validator import validate_url

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
        is_valid, formatted_url = validate_url(url)
        if not is_valid:
            return None, "Неверный формат URL"

        logger.info(f"Fetching data from: {formatted_url}")
        
        # Create an SSL context with the certifi CA bundle
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        async with aiohttp.ClientSession() as session:
            async with session.get(formatted_url, headers={
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
            return None, "Страница не найдена (404)"
        elif status_code == 403:
            return None, "Доступ запрещен (403)"
        elif status_code == 429:
            return None, "Слишком много запросов (429)"
        return None, f"Ошибка при получении URL: {str(e)}"
    except aiohttp.ClientConnectorError as e:
        logger.error(f"Connection error: {str(e)}")
        return None, "Не удалось подключиться к серверу. Проверьте URL."
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching {url}")
        return None, "Время ожидания истекло. Сервер не отвечает."
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {str(e)}")
        return None, f"Произошла ошибка: {str(e)}"

async def get_pagespeed_insights(url):
    """
    Asynchronously fetch PageSpeed Insights data with caching.
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        dict: PageSpeed analysis results
    """
    # Check cache first
    if url in cache:
        logger.info(f"Cache hit for PageSpeed data: {url}")
        return cache[url]

    try:
        api_key = current_app.config['PAGESPEED_API_KEY']
        if not api_key:
            logger.warning("PAGESPEED_API_KEY is not set")
            return {"error": "API ключ Google PageSpeed Insights не настроен"}
            
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
        fcp = audits.get('first-contentful-paint', {}).get('displayValue', 'Н/Д')
        lcp = audits.get('largest-contentful-paint', {}).get('displayValue', 'Н/Д')
        tti = audits.get('interactive', {}).get('displayValue', 'Н/Д')
        cls = audits.get('cumulative-layout-shift', {}).get('displayValue', 'Н/Д')

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
        
        # Store in cache
        cache[url] = result
        return result
        
    except aiohttp.ClientResponseError as e:
        error_msg = f"PageSpeed API error: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    except asyncio.TimeoutError:
        error_msg = "Время ожидания PageSpeed API истекло"
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Ошибка при получении данных PageSpeed: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}