# app/utils/site_crawler.py
import asyncio
import logging
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from app.services.pagespeed import fetch_website_data

logger = logging.getLogger(__name__)

async def crawl_website(start_url, max_pages=10, max_depth=2):
    """
    Crawl a website to collect text content from multiple pages.
    
    Args:
        start_url: Starting URL to crawl
        max_pages: Maximum number of pages to crawl
        max_depth: Maximum link depth to follow
        
    Returns:
        dict: Combined content from all pages
    """
    visited = set()
    to_visit = [(start_url, 0)]  # (url, depth)
    all_content = {
        "texts": [],
        "urls": [],
        "title": ""  # Main page title
    }
    
    # Parse base domain to stay within the site
    parsed_url = urlparse(start_url)
    base_domain = parsed_url.netloc
    
    while to_visit and len(visited) < max_pages:
        url, depth = to_visit.pop(0)
        
        if url in visited or depth > max_depth:
            continue
            
        logger.info(f"Crawling page {len(visited)+1}/{max_pages}: {url}")
        
        # Fetch the page
        content, error = await fetch_website_data(url)
        if error or not content:
            logger.warning(f"Error fetching {url}: {error}")
            visited.add(url)
            continue
            
        # Parse the content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Get the page text (clean it up)
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        
        page_text = soup.get_text(separator="\n", strip=True)
        all_content["texts"].append(page_text)
        all_content["urls"].append(url)
        
        # Save the main page title if this is the first page
        if len(visited) == 0 and soup.title:
            all_content["title"] = soup.title.string
            
        # Extract links for next pages to visit
        if depth < max_depth:
            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"]
                
                # Handle relative URLs
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(url, href)
                    
                # Skip external links, anchors, etc.
                parsed_href = urlparse(href)
                if parsed_href.netloc != base_domain or not parsed_href.path:
                    continue
                    
                if href not in visited and (href, depth+1) not in to_visit:
                    to_visit.append((href, depth+1))
        
        visited.add(url)
    
    logger.info(f"Crawled {len(visited)} pages from {start_url}")
    return all_content