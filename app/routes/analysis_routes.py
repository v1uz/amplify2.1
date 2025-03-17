# app/routes/analysis_routes.py

# Add these imports
from app.utils.site_crawler import crawl_website
from app.services.bert_service import BERTDescriptionGenerator
from flask import Blueprint, request, jsonify, session, url_for
import logging
from app.utils.url_validator import validate_url
from app.services.pagespeed import fetch_website_data

logger = logging.getLogger(__name__)
analysis_bp = Blueprint('analysis', __name__)
from app.services.analyzers import legacy_analyze_seo
# Initialize BERT service (do this outside the route handler for performance)
bert_generator = BERTDescriptionGenerator()

@analysis_bp.route('/analyze', methods=['POST'])
async def analyze_website():
    """Handle website analysis request."""
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data.get('url')
    
    # Validate URL
    is_valid, normalized_url = validate_url(url)
    if not is_valid:
        return jsonify({'error': 'Invalid URL format'}), 400
    
    try:
        # 1. Crawl the website to get content from multiple pages
        site_content = await crawl_website(normalized_url, max_pages=5, max_depth=1)
        
        # 2. Get the HTML content for the main SEO analysis
        html_content, error = await fetch_website_data(normalized_url)
        if error:
            return jsonify({'error': f'Failed to fetch website: {error}'}), 400
            
        # 3. Run the SEO analysis on the main page
        seo_results = await legacy_analyze_seo(html_content, normalized_url)
        
        # 4. Generate BERT description using text from all crawled pages
        all_text = "\n\n".join(site_content["texts"])
        bert_result = bert_generator.process_webpage_content(all_text)
        
        # 5. Add the BERT description to the results
        seo_results['bert_description'] = bert_result.get('description', '')
        seo_results['bert_confidence'] = bert_result.get('confidence', 0.0)
        
        # 6. Store results in session and redirect
        session['seo_results'] = seo_results
        return jsonify({'redirect': url_for('main.result')})
        
    except Exception as e:
        logger.error(f"Error analyzing {url}: {str(e)}")
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500