"""
Main routes for Amplify application.
These routes handle the main landing page, amplify interface, and preloader.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session

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
    return render_template('result.html', results=seo_results)