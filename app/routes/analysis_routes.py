"""
Analysis routes for the Amplify SEO application.

This module handles all routes related to SEO analysis, results display,
and BERT description generation.
"""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
import logging
from urllib.parse import urlparse
import time
import json
import traceback
from app.utils.url_validator import is_valid_url, normalize_url
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)
validate_url = is_valid_url

try:
    from celery import Celery
    celery = Celery('amplify', broker='redis://localhost:6379/0')
    celery_available = True
except ImportError:
    celery_available = False
    # Create dummy implementation
    class DummyCelery:
        def task(self, f):
            return f
    celery = DummyCelery()

try:
    from app.services.analyzer import analyze_website
except ImportError as e:
    logging.error(f"Error importing analyzer: {e}")
    def analyze_website(url, **kwargs):
        return {"error": "Analyzer module could not be loaded", "url": url}

try:
    from app.services.bert_service import BERTDescriptionGenerator
except ImportError as e:
    logging.error(f"Error importing BERTDescriptionGenerator: {e}")
    # Define a fallback class in case the import fails
    class BERTDescriptionGenerator:
        def __init__(self, *args, **kwargs):
            self.model_loaded = False
        
        def process_webpage_content(self, *args, **kwargs):
            return {"description": "", "confidence": 0.0, "error": "BERT service not available"}
        
        def detect_language(self, text):
            return "en"

try:
    from app.utils.pagespeed_utils import get_pagespeed_data
except ImportError as e:
    logging.error(f"Error importing get_pagespeed_data: {e}")
    # Define a fallback function in case the import fails
    def get_pagespeed_data(url, strategy='mobile'):
        return {"performance_score": 0, "error": "PageSpeed service not available"}

# Import utilities
from app.utils import debug_bert_service, extract_keywords, clean_text, format_duration
from app.utils.url_validator import normalize_url, extract_domain, is_valid_url
from app.utils.cache_manager import cache

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
analysis_bp = Blueprint('analysis', __name__)

# Initialize BERT service (global instance)
bert_service = BERTDescriptionGenerator(model_name='t5-base', device='cpu')

@celery.task
def process_website_task(url):
    result = analyze_website(url, generate_description=True, enhance_with_gpt=True)
    return result

@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    """Analyze a website and show results."""
    start_time = time.time()
    
    # Handle both form submissions and JSON requests
    if request.is_json:
        data = request.get_json()
        url = data.get('url', '').strip()
    else:
        url = request.form.get('url', '').strip()
    
    if not url:
        if request.is_json:
            return jsonify({"error": "URL is required"}), 400
        else:
            return render_template('error.html', error="URL is required"), 400
    
    # Validate URL
    if not is_valid_url(url):
        if request.is_json:
            return jsonify({"error": "Invalid URL format. Please enter a valid website URL."}), 400
        else:
            return render_template('error.html', error="Invalid URL format. Please enter a valid website URL."), 400
    
    # Normalize URL
    url = normalize_url(url)
    
    try:
        logger.info(f"Starting analysis for URL: {url}")
        
        # Check cache for existing analysis
        cache_key = f"analysis:{url}"
        cached_results = cache.get(cache_key)
        
        if cached_results:
            logger.info(f"Returning cached analysis for {url}")
            cached_results['from_cache'] = True
            cached_results['analysis_time'] = "< 1 second (cached)"
            
            if request.is_json:
                return jsonify({
                    "status": "complete",
                    "redirect": url_for('analysis.show_result', url=url)
                })
            else:
                return render_template('results.html', results=analysis_results)

        # Perform website analysis
        analysis_results = analyze_website(url)
        
        # Process descriptions
        if 'descriptions' in analysis_results:
            analysis_results['bert_description'] = analysis_results['descriptions'].get('bert_description', '')
            analysis_results['bert_confidence'] = analysis_results['descriptions'].get('bert_confidence', 0.0)
            analysis_results['enhanced_description'] = analysis_results['descriptions'].get('enhanced_description', '')
            analysis_results['generation_method'] = analysis_results['descriptions'].get('generation_method', '')
            analysis_results['icl_analysis'] = analysis_results['descriptions'].get('icl_analysis', '')
            
            logger.info(f"BERT description: {analysis_results['bert_description'][:30]}...")
            logger.info(f"Enhanced description: {analysis_results['enhanced_description'][:30]}...")
            if analysis_results['icl_analysis']:
                logger.info(f"ICL analysis: {analysis_results['icl_analysis'][:30]}...")
        
        if 'customer_profile' in analysis_results:
            analysis_results['ideal_customer_profile'] = analysis_results['customer_profile']
        
        # Add analysis timestamp
        analysis_results['analysis_timestamp'] = time.time()
        
        # Generate keywords
        if 'content' in analysis_results and analysis_results['content']:
            keywords = extract_keywords(analysis_results['content'], max_keywords=15)
            analysis_results['keywords'] = ', '.join(keywords)
        else:
            analysis_results['keywords'] = "Keywords not found"
        
        # Get PageSpeed data if not already included
        if 'pagespeed' not in analysis_results.get('metrics', {}):
            try:
                pagespeed_data = get_pagespeed_data(url)
                if pagespeed_data:
                    if 'metrics' not in analysis_results:
                        analysis_results['metrics'] = {}
                    analysis_results['metrics']['pagespeed'] = pagespeed_data
            except Exception as e:
                logger.error(f"Error fetching PageSpeed data: {e}")
                analysis_results['pagespeed_error'] = str(e)
        
        # Remove BERT analysis if needed
        if 'bert_analysis' in analysis_results:
            del analysis_results['bert_analysis']
            
        # Calculate recommendations
        recommendations = generate_recommendations(analysis_results)
        analysis_results['recommendations'] = recommendations
        
        # Calculate analysis time
        elapsed_time = time.time() - start_time
        analysis_results['analysis_time'] = format_duration(elapsed_time)
        analysis_results['from_cache'] = False
        
        # Cache the results (1 hour TTL)
        cache.set(cache_key, analysis_results, ttl=3600)
        
        logger.info(f"Analysis completed in {elapsed_time:.2f}s for {url}")
        
        # Return results based on request type
        if request.is_json:
            return jsonify({
                "status": "complete",
                "redirect": url_for('analysis.show_result', url=url)
            })
        else:
            return render_template('results.html', results=analysis_results)
        
    except Exception as e:
        logger.error(f"Error in analyze route: {e}")
        logger.error(traceback.format_exc())
        
        if request.is_json:
            return jsonify({"status": "failed", "error": f"Analysis failed: {str(e)}"}), 500
        else:
            return render_template('error.html', error=f"Analysis failed: {str(e)}"), 500

@analysis_bp.route('/status', methods=['GET'])
def check_status():
    """Check analysis status for a URL."""
    url = request.args.get('url', '')
    if not url:
        return jsonify({"error": "URL parameter required"}), 400
        
    url = normalize_url(url)
    cache_key = f"analysis:{url}"
    cached_results = cache.get(cache_key)
    
    if cached_results:
        return jsonify({
            "status": "complete",
            "redirect": url_for('analysis.show_result', url=url)
        })
    else:
        # Analysis is either in progress or not started
        return jsonify({
            "status": "in_progress"
        })
    
@analysis_bp.route('/api/task/<task_id>')
def check_task(task_id):
    task = process_website_task.AsyncResult(task_id)
    if task.ready():
        return jsonify({"status": "complete", "result": task.result})
    return jsonify({"status": "processing"})
        
@analysis_bp.route('/api/analyze', methods=['POST'])
def analyze_api():
    url = request.json.get('url')
    if not url or not is_valid_url(url):
        return jsonify({"error": "Invalid URL"}), 400
    
    if celery_available:
        # Async processing with Celery
        task = process_website_task.delay(url)
        return jsonify({"task_id": task.id})
    else:
        # Synchronous processing
        result = process_website_task(url)
        return jsonify({"result": result})
        
@analysis_bp.route('/result', methods=['GET'])
def show_result():
    """Show results for a previously analyzed URL."""
    url = request.args.get('url', '')
    
    if not url:
        return redirect(url_for('main.index'))
    
    # Normalize URL
    url = normalize_url(url)
    
    # Check cache for existing analysis
    cache_key = f"analysis:{url}"
    cached_results = cache.get(cache_key)
    
    if cached_results:
        # Ensure results structure is complete before rendering
        cached_results = ensure_result_structure(cached_results)
        cached_results['from_cache'] = True
        return render_template('results.html', results=cached_results)
    else:
        # If no cached result, redirect to analyzer
        return redirect(url_for('main.index', url=url))
    
    url_for('analysis.show_result', url=url)


@analysis_bp.route('/debug/bert', methods=['GET'])
def debug_bert():
    """Debug endpoint for BERT service."""
    # Get sample text from request or use default
    sample_text = request.args.get('text', '')
    
    # Run diagnostics
    debug_results = debug_bert_service(bert_service, content=sample_text)
    
    # Return as JSON or render a debug template
    if request.args.get('format') == 'json':
        return jsonify(debug_results)
    else:
        return render_template('debug_bert.html', results=debug_results)

@analysis_bp.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear analysis cache."""
    try:
        # Clear only specific cache if URL provided
        url = request.form.get('url')
        if url:
            url = normalize_url(url)
            cache_key = f"analysis:{url}"
            cache.delete(cache_key)
            return jsonify({"success": True, "message": f"Cache cleared for {url}"})
        
        # Otherwise clear all cache
        cache.clear()
        return jsonify({"success": True, "message": "All cache cleared"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def generate_recommendations(analysis_results: dict) -> list:
    """
    Generate SEO recommendations based on analysis results.
    
    Args:
        analysis_results: Analysis results dictionary
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Meta recommendations
    meta = analysis_results.get('metrics', {}).get('meta_analysis', {})
    if meta:
        if meta.get('meta_score', 100) < 70:
            if not meta.get('title', {}).get('has_title', True):
                recommendations.append("Add a title tag to your page")
            elif meta.get('title', {}).get('length', 0) < 30:
                recommendations.append("Your title is too short. Make it more descriptive")
            elif meta.get('title', {}).get('length', 0) > 60:
                recommendations.append("Your title is too long. Keep it under 60 characters")
                
        if not meta.get('description', {}).get('has_description', True):
            recommendations.append("Add a meta description to your page")
        elif meta.get('description', {}).get('length', 0) < 70:
            recommendations.append("Your meta description is too short. Aim for 120-158 characters")
    
    # Content recommendations
    content = analysis_results.get('metrics', {}).get('content_analysis', {})
    if content:
        if content.get('word_count', 0) < 300:
            recommendations.append("Your content is too thin. Add more relevant, quality content")
        if content.get('has_headings', True) == False:
            recommendations.append("Add headings (H1, H2, H3) to structure your content")
    
    # Technical recommendations
    technical = analysis_results.get('metrics', {}).get('technical_analysis', {})
    if technical:
        if not technical.get('canonical', {}).get('has_canonical', True):
            recommendations.append("Add a canonical tag to prevent duplicate content issues")
        if not technical.get('schema_markup', {}).get('has_schema', True):
            recommendations.append("Add structured data (Schema.org) to enhance your search results")
    
    # Mobile recommendations
    mobile = analysis_results.get('metrics', {}).get('mobile_analysis', {})
    if mobile:
        if not mobile.get('viewport', {}).get('has_viewport', True):
            recommendations.append("Add a viewport meta tag for better mobile experience")
        if not mobile.get('responsive_css', {}).get('has_media_queries', True):
            recommendations.append("Make your site responsive with CSS media queries")
    
    # PageSpeed recommendations
    pagespeed = analysis_results.get('metrics', {}).get('pagespeed', {})
    if pagespeed:
        performance_score = pagespeed.get('performance_score', 100)
        if performance_score < 50:
            recommendations.append("Improve page load speed by optimizing images and resources")
        if performance_score < 70:
            recommendations.append("Consider implementing browser caching for better performance")
    
    # Add BERT-based recommendation if confidence is high
    if analysis_results.get('bert_description') and analysis_results.get('bert_confidence', 0) > 0.6:
        recommendations.append("Consider using our AI-generated description for your meta description")
    
    # Limit to 10 recommendations maximum
    if len(recommendations) > 10:
        recommendations = recommendations[:10]
    
    return recommendations

@analysis_bp.route('/preloader', methods=['GET'])
def preloader():
    """
    Handle URL preloading and redirect to the analysis process.
    This route accepts a URL parameter and renders the preloader page.
    """
    url = request.args.get('url', '')
    
    if not url:
        logger.error("Preloader called without URL parameter")
        return render_template('error.html', error="No URL provided. Please enter a website URL to analyze."), 400
    
    # Validate URL
    if not is_valid_url(url):
        logger.error(f"Invalid URL format: {url}")
        return render_template('error.html', error="Invalid URL format. Please enter a valid website URL."), 400
    
    # Normalize URL
    url = normalize_url(url)
    logger.info(f"Preloader processing URL: {url}")
    
    # Render the preloader template with the URL
    return render_template('preloader.html', url=url)

# In your analysis_routes.py, add this function:
def ensure_result_structure(results):
    """Ensure the results dictionary has all required keys to prevent template errors."""
    if 'bert_description' not in results:
        results['bert_description'] = ''
    if 'enhanced_description' not in results:
        results['enhanced_description'] = ''
    if 'bert_confidence' not in results:
        results['bert_confidence'] = 0.0
    if 'icl_analysis' not in results:
        results['icl_analysis'] = ''
    if 'icl_analysis' in results['descriptions']:
        results['icl_analysis'] = results['descriptions']['icl_analysis']
    
    if 'metrics' not in results:
        results['metrics'] = {}
        
    if 'meta_analysis' not in results['metrics']:
        results['metrics']['meta_analysis'] = {
            'title': {'content': ''},
            'description': {'content': ''},
            'keywords': {'content': []}
        }
        
    if 'content_analysis' not in results['metrics']:
        results['metrics']['content_analysis'] = {}
        
    if 'technical_analysis' not in results['metrics']:
        results['metrics']['technical_analysis'] = {}
    
    if 'ideal_customer_profile' not in results:
        results['ideal_customer_profile'] = {
            "demographics": "Not available (cached result)",
            "interests": "Not available (cached result)",
            "behavior": "Not available (cached result)",
            "needs": "Not available (cached result)",
            "pain_points": "Not available (cached result)"
        }
        
    return results
