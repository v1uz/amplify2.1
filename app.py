from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from bs4 import BeautifulSoup
from flask_cors import CORS
from urllib.parse import urlparse, urljoin
import os
from dotenv import load_dotenv # type: ignore
import aiohttp
from cachetools import TTLCache
import asyncio
import certifi
import ssl

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "http://localhost:5002"}})
app.secret_key = os.urandom(24)  # Required for session management

# Access API key from environment variables
API_KEY = os.getenv('PAGESPEED_API_KEY')
if not API_KEY:
    print("Warning: PAGESPEED_API_KEY is not set. Check your .env file.")
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Cache setup with TTL of 1 hour
cache = TTLCache(maxsize=100, ttl=3600)

def validate_url(url):
    """Normalize URL to use https:// and validate format with detailed debugging."""
    print(f"Validating URL: {url}")
    parsed = urlparse(url.strip())
    
    # If no scheme is provided, or if the scheme is http, normalize to https://
    if not parsed.scheme or parsed.scheme == 'http':
        print(f"No scheme or http detected, normalizing to 'https://' for {url}")
        # Remove any existing http:// or https:// to avoid duplication
        url_without_scheme = url.replace('http://', '').replace('https://', '').strip('/')
        url = f'https://{url_without_scheme}'
        parsed = urlparse(url)
    # If scheme is https, proceed as is
    elif parsed.scheme == 'https':
        print(f"Scheme is already https, proceeding with {url}")
    else:
        print(f"Unsupported scheme {parsed.scheme}, normalizing to https://")
        url_without_scheme = url.replace(f'{parsed.scheme}://', '').strip('/')
        url = f'https://{url_without_scheme}'
        parsed = urlparse(url)

    # Validate that scheme and netloc are present after normalization
    has_scheme = bool(parsed.scheme)
    has_netloc = bool(parsed.netloc)
    is_valid = has_scheme and has_netloc
    print(f"Parsed: Scheme={parsed.scheme}, Netloc={parsed.netloc}, Path={parsed.path}, "
          f"has_scheme={has_scheme}, has_netloc={has_netloc}, Valid={is_valid}, Full Parsed={parsed}")
    return is_valid, url

async def fetch_website_data(url):
    """Asynchronously fetch website content with improved error handling."""
    try:
        is_valid, formatted_url = validate_url(url)
        if not is_valid:
            return None, "Неверный формат URL"

        print(f"Fetching data from: {formatted_url}")
        # Create an SSL context with the certifi CA bundle
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        async with aiohttp.ClientSession() as session:
            async with session.get(formatted_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }, timeout=aiohttp.ClientTimeout(total=10), ssl=ssl_context) as response:
                response.raise_for_status()
                text = await response.text()
                return text, None
    except aiohttp.ClientError as e:
        return None, f"Ошибка при получении URL: {str(e)}"

async def get_pagespeed_insights(url):
    """Asynchronously fetch PageSpeed Insights data with caching."""
    if url in cache:
        print(f"Cache hit for URL: {url}")
        return cache[url]

    try:
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={API_KEY}"
        print(f"Calling PageSpeed API for: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()

        lighthouse = data.get('lighthouseResult', {})
        performance_score = lighthouse.get('categories', {}).get('performance', {}).get('score', 0) * 100
        fcp = lighthouse.get('audits', {}).get('first-contentful-paint', {}).get('displayValue', 'Н/Д')
        lcp = lighthouse.get('audits', {}).get('largest-contentful-paint', {}).get('displayValue', 'Н/Д')
        tti = lighthouse.get('audits', {}).get('interactive', {}).get('displayValue', 'Н/Д')
        cls = lighthouse.get('audits', {}).get('cumulative-layout-shift', {}).get('displayValue', 'Н/Д')

        opportunities = lighthouse.get('audits', {}).get('opportunities', {})
        recommendations = [audit.get('title', 'Нет рекомендаций') for audit in opportunities.values() if audit.get('score') is not None]

        result = {
            'performance_score': performance_score,
            'first_contentful_paint': fcp,
            'largest_contentful_paint': lcp,
            'time_to_interactive': tti,
            'cumulative_layout_shift': cls,
            'recommendations': recommendations
        }
        cache[url] = result
        return result
    except aiohttp.ClientError as e:
        return {"error": f"Не удалось получить данные PageSpeed Insights: {str(e)}"}

async def analyze_seo(html_content, url):
    """Asynchronously analyze SEO metrics considering PageSpeed Insights."""
    soup = BeautifulSoup(html_content, 'html.parser')

    title = soup.title.string if soup.title else "Заголовок не найден"
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_description_content = meta_description['content'] if meta_description and meta_description.has_attr('content') else " ".join([p.get_text(strip=True) for p in soup.find_all('p')[:2]])
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    keywords = keywords_meta['content'] if keywords_meta and keywords_meta.has_attr('content') else "Ключевые слова не найдены"

    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
    h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
    img_without_alt = len([img for img in soup.find_all('img') if not img.get('alt')])
    internal_links = len([a for a in soup.find_all('a', href=True) if a['href'].startswith('/')])
    external_links = len([a for a in soup.find_all('a', href=True) if not a['href'].startswith('/') and urlparse(a['href']).netloc])

    recommendations = []
    if len(title) > 60:
        recommendations.append("Заголовок слишком длинный (более 60 символов). Сократите его для лучшего SEO.")
    if meta_description_content == "Заголовок не найден":
        recommendations.append("Отсутствует мета-описание. Добавьте краткое описание (150-160 символов).")
    if keywords == "Ключевые слова не найдены":
        recommendations.append("Отсутствуют мета-ключевые слова. Добавьте релевантные ключевые слова.")
    if not h1_tags:
        recommendations.append("Отсутствует тег H1. Добавьте один тег H1 с основной темой.")
    if img_without_alt > 0:
        recommendations.append(f"{img_without_alt} изображений без атрибута alt. Добавьте описательные атрибуты alt.")

    pagespeed_data = await get_pagespeed_insights(url)
    if 'error' in pagespeed_data:
        pagespeed_recommendations = [pagespeed_data['error']]
    else:
        pagespeed_recommendations = pagespeed_data['recommendations']

    prompt = (
        f"Анализ SEO для сайта с заголовком: '{title}'. "
        f"Описание: {meta_description_content}. "
        f"Ключевые слова: {keywords}. "
        f"Теги H1: {h1_tags}. "
        f"Теги H2: {h2_tags}. "
        f"Внутренние ссылки: {internal_links}, Внешние ссылки: {external_links}. "
        f"Рекомендации SEO: {', '.join(recommendations)}. "
        f"Оценка PageSpeed: {pagespeed_data.get('performance_score', 'Н/Д')}. "
        f"Рекомендации PageSpeed: {', '.join(pagespeed_recommendations)}."
    )

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

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/amplify')
def amplify():
    return render_template('amplify.html')

@app.route('/preloader')
def preloader():
    url = request.args.get('url')
    if not url:
        return redirect(url_for('amplify'))
    return render_template('preloader.html', url=url)

@app.route('/analyze', methods=['POST'])
async def analyze():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "URL не предоставлен"}), 400

        url = data['url']
        print(f"Received URL for analysis: {url}")
        html_content, error = await fetch_website_data(url)
        if error:
            return jsonify({"error": error}), 400

        seo_results = await analyze_seo(html_content, url)
        session['seo_results'] = seo_results
        return jsonify({"redirect": url_for('result')}), 200
    except Exception as e:
        print(f"Error in /analyze: {str(e)}")
        return jsonify({"error": "Произошла внутренняя ошибка сервера: " + str(e)}), 500

@app.route('/result')
def result():
    seo_results = session.get('seo_results')
    if not seo_results:
        return redirect(url_for('amplify'))
    return render_template('result.html', results=seo_results)

if __name__ == '__main__':
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    import logging

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        config = Config()
        config.bind = ["0.0.0.0:5002"]
        config.use_reloader = True
        logger.info("Starting server on http://localhost:5002")
        asyncio.run(serve(app, config))
    except Exception as e:
        logger.error(f"Failed to start server: {e}")