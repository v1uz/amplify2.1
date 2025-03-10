"""
SEO analysis service module.
This module handles the extraction and analysis of SEO metrics from website content.
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging

# Import page speed service
from app.services.pagespeed import get_pagespeed_insights

# Set up logging
logger = logging.getLogger(__name__)

async def analyze_seo(html_content, url):
    """
    Analyze HTML content for SEO metrics and combine with PageSpeed Insights data.
    
    Args:
        html_content (str): HTML content of the website
        url (str): URL of the website
        
    Returns:
        dict: A dictionary containing SEO analysis results
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract basic metadata
    title = soup.title.string if soup.title else "Заголовок не найден"
    
    # Extract meta description or use first paragraphs as fallback
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_description_content = meta_description['content'] if meta_description and meta_description.has_attr('content') else " ".join([p.get_text(strip=True) for p in soup.find_all('p')[:2]])
    
    # Extract keywords
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    keywords = keywords_meta['content'] if keywords_meta and keywords_meta.has_attr('content') else "Ключевые слова не найдены"

    # Extract structural elements
    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
    h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
    
    # Check for images without alt text
    img_without_alt = len([img for img in soup.find_all('img') if not img.get('alt')])
    
    # Count internal and external links
    internal_links = len([a for a in soup.find_all('a', href=True) if a['href'].startswith('/')])
    external_links = len([a for a in soup.find_all('a', href=True) if not a['href'].startswith('/') and urlparse(a['href']).netloc])

    # Generate SEO recommendations
    recommendations = []
    if len(title) > 60:
        recommendations.append("Заголовок слишком длинный (более 60 символов). Сократите его для лучшего SEO.")
    if meta_description_content == "Заголовок не найден" or len(meta_description_content) < 10:
        recommendations.append("Отсутствует мета-описание. Добавьте краткое описание (150-160 символов).")
    if keywords == "Ключевые слова не найдены":
        recommendations.append("Отсутствуют мета-ключевые слова. Добавьте релевантные ключевые слова.")
    if not h1_tags:
        recommendations.append("Отсутствует тег H1. Добавьте один тег H1 с основной темой.")
    if img_without_alt > 0:
        recommendations.append(f"{img_without_alt} изображений без атрибута alt. Добавьте описательные атрибуты alt.")

    # Get PageSpeed Insights data
    try:
        pagespeed_data = await get_pagespeed_insights(url)
        if 'error' in pagespeed_data:
            pagespeed_recommendations = [pagespeed_data['error']]
            logger.warning(f"Error getting PageSpeed data: {pagespeed_data['error']}")
        else:
            pagespeed_recommendations = pagespeed_data.get('recommendations', [])
    except Exception as e:
        logger.error(f"Exception in PageSpeed analysis: {str(e)}")
        pagespeed_data = {"error": f"Не удалось получить данные PageSpeed Insights: {str(e)}"}
        pagespeed_recommendations = [pagespeed_data["error"]]

    # Create a prompt summarizing the analysis
    prompt = (
        f"Анализ SEO для сайта с заголовком: '{title}'. "
        f"Описание: {meta_description_content}. "
        f"Ключевые слова: {keywords}. "
        f"Теги H1: {h1_tags}. "
        f"Теги H2: {h2_tags}. "
        f"Внутренние ссылки: {internal_links}, Внешние ссылки: {external_links}. "
        f"Рекомендации SEO: {', '.join(recommendations)}. "
        f"Оценка PageSpeed: {pagespeed_data.get('performance_score', 'Н/Д')}. "
        f"Рекомендации PageSpeed: {', '.join(pagespeed_recommendations if isinstance(pagespeed_recommendations, list) else [pagespeed_recommendations])}."
    )

    # Return comprehensive analysis
    return {
        'description': meta_description_content,
        'keywords': keywords,
        'prompt': prompt,
        'recommendations': recommendations + (pagespeed_recommendations if isinstance(pagespeed_recommendations, list) else [pagespeed_recommendations]),
        'metrics': {
            'title': title,
            'h1_tags': h1_tags,
            'h2_tags': h2_tags,
            'img_without_alt': img_without_alt,
            'internal_links': internal_links,
            'external_links': external_links,
            'pagespeed': pagespeed_data
        }
    }