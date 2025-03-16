"""
Main routes for Amplify application.
These routes handle the main landing page, amplify interface, and preloader.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from flask import current_app
from flask import send_from_directory
import os
import mimetypes

# Create blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main landing page."""
    return render_template('main.html')

@main_bp.route('/amplify')
def amplify():
    """Render the Amplify analysis interface."""
    return render_template('amplify.html')

@main_bp.route('/preloader')
def preloader():
    """
    Render the preloader page with the URL to analyze.
    This route expects a 'url' query parameter.
    """
    url = request.args.get('url')
    if not url:
        return redirect(url_for('main.amplify'))
    return render_template('preloader.html', url=url)

@main_bp.route('/result')
def result():
    """
    Render the analysis results page.
    Results are stored in the session and retrieved for display.
    """
    seo_results = session.get('seo_results')
    if not seo_results:
        return redirect(url_for('main.amplify'))
    print("SEO RESULTS:", seo_results)
    return render_template('result.html', results=seo_results)

import os

@main_bp.route('/test-static')
def test_static():
    """Test page for static files."""
    static_folder = current_app.static_folder
    css_exists = os.path.exists(os.path.join(static_folder, 'css', 'main.css'))
    js_exists = os.path.exists(os.path.join(static_folder, 'js', 'main.js'))
    
    return render_template('test_static.html', 
                          static_folder=static_folder,
                          css_exists=css_exists,
                          js_exists=js_exists)
    
@main_bp.route('/direct')
def direct_test():
    """Serve the direct test page with inline styles and scripts."""
    return send_from_directory(os.path.dirname(current_app.root_path), 'direct.html')

@main_bp.route('/debug-static/<path:filename>')
def debug_static(filename):
    """Debug static file serving with MIME type reporting."""
    filepath = os.path.join(current_app.static_folder, filename)
    
    if not os.path.exists(filepath):
        return f"File not found: {filepath}", 404
    
    # Read the file content
    with open(filepath, 'rb') as f:
        content = f.read()
    
    # Guess the MIME type
    mime_type = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
    
    # Return file with explicit MIME type and debugging information
    response = current_app.response_class(
        response=content,
        status=200,
        mimetype=mime_type
    )
    
    response.headers['X-Debug-Info'] = f"File: {filename}, MIME: {mime_type}"
    return response

@main_bp.route('/result-gauge')
def results_gauge():
    """Render the analysis results page with gauge visualization."""
    seo_results = session.get('seo_results')
    if not seo_results:
        return redirect(url_for('main.amplify'))
    return render_template('result_gauge.html', results=seo_results)