"""
Amplify 2.1 - Main application initialization
This module initializes the Flask application and sets up all necessary configurations and extensions.
"""

from flask import Flask
from flask_cors import CORS
import os
import logging
from cachetools import TTLCache
from flask import request

# Import configuration
from app.config import config_by_name

# Initialize cache
cache = TTLCache(maxsize=100, ttl=3600)

def create_app(config_name='default'):
    """
    Factory function that creates and configures the Flask application.
    
    Args:
        config_name (str): The configuration to use (default, development, testing, production)
        
    Returns:
        Flask: The configured Flask application
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    static_folder = os.path.join(project_root, 'static')

# Then in your Flask initialization
    app = Flask(__name__, 
            static_folder=static_folder,
            template_folder='templates')
    
    # Load configuration based on environment
    app.config.from_object(config_by_name[config_name])
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting application in {config_name} mode")
    
    # Initialize CORS
    CORS(app, resources={r"/analyze": {"origins": app.config['CORS_ORIGINS']}})
    
    # Set secret key
    app.secret_key = app.config['SECRET_KEY']
    
    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.analysis_routes import analysis_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return {'error': 'Internal server error'}, 500
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    # Add cache headers for static resources
    @app.after_request
    def add_cache_headers(response):
        if request.path.startswith('/static'):
            response.cache_control.max_age = 86400  # 24 hours
        return response
    
    return app