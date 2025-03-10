"""
Analysis routes for Amplify application.
These routes handle SEO analysis functionality.
"""

from flask import Blueprint, request, jsonify, session, url_for
import logging

# Import services
from app.services.analyzer import analyze_seo
from app.utils.url_validator import validate_url
from app.services.pagespeed import fetch_website_data

# Create blueprint for analysis routes
analysis_bp = Blueprint('analysis', __name__)

# Set up logging
logger = logging.getLogger(__name__)

@analysis_bp.route('/analyze', methods=['POST'])
async def analyze():
    """
    Analyze a website URL for SEO metrics.
    
    Expects a JSON payload with a 'url' field.
    Returns a JSON response with a redirect to the results page or an error message.
    """
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "URL не предоставлен"}), 400

        url = data['url']
        logger.info(f"Received URL for analysis: {url}")
        
        # Validate and normalize the URL
        is_valid, formatted_url = validate_url(url)
        if not is_valid:
            return jsonify({"error": "Неверный формат URL"}), 400
            
        # Fetch website content
        html_content, error = await fetch_website_data(formatted_url)
        if error:
            logger.error(f"Error fetching {formatted_url}: {error}")
            return jsonify({"error": error}), 400

        # Analyze SEO metrics
        seo_results = await analyze_seo(html_content, formatted_url)
        
        # Store results in session for display on results page
        session['seo_results'] = seo_results
        
        return jsonify({"redirect": url_for('main.result')}), 200
        
    except Exception as e:
        logger.error(f"Error in /analyze: {str(e)}")
        return jsonify({"error": "Произошла внутренняя ошибка сервера: " + str(e)}), 500