"""
Main routes for the Amplify SEO application.

This module handles the main pages, landing page, and non-analysis routes.
"""
from flask import Blueprint, render_template, request, redirect, url_for
import logging
from app.utils.url_validator import normalize_url, is_valid_url

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Render the main landing page.
    """
    return render_template('index.html')

@main_bp.route('/amplify')
def amplify():
    """
    Render the Amplify tool page.
    """
    # Get URL from query parameter (if redirected from landing page)
    url = request.args.get('url', '')
    
    return render_template('amplify.html', url=url)

@main_bp.route('/about')
def about():
    """
    Render the about page.
    """
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """
    Render the contact page.
    """
    return render_template('contact.html')

@main_bp.route('/features')
def features():
    """
    Render the features page.
    """
    return render_template('features.html')

@main_bp.route('/pricing')
def pricing():
    """
    Render the pricing page.
    """
    return render_template('pricing.html')

@main_bp.route('/blog')
def blog():
    """
    Render the blog index page.
    """
    return render_template('blog/index.html')

@main_bp.route('/terms')
def terms():
    """
    Render the terms of service page.
    """
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """
    Render the privacy policy page.
    """
    return render_template('privacy.html')

@main_bp.route('/error')
def error():
    """
    Render a generic error page.
    """
    error_message = request.args.get('message', 'An error occurred')
    return render_template('error.html', error=error_message)

@main_bp.route('/preloader')
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

@main_bp.errorhandler(404)
def page_not_found(e):
    """
    Handle 404 errors.
    """
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def server_error(e):
    """
    Handle 500 errors.
    """
    logger.error(f"Server error: {str(e)}")
    return render_template('errors/500.html'), 500