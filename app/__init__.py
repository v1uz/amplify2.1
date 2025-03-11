"""
Amplify 2.1 - Main application initialization
This module initializes the Flask application and sets up all necessary configurations and extensions.
"""

from flask import Flask, send_from_directory, request
from flask_cors import CORS
import os
import logging
import mimetypes
from cachetools import TTLCache

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
    # Configure proper MIME types
    mimetypes.add_type('text/css', '.css')
    mimetypes.add_type('application/javascript', '.js')
    
    # Set up static folder path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_folder = os.path.join(project_root, 'static')
    
    # Create Flask application instance
    app = Flask(__name__, 
                static_folder=static_folder,
                template_folder='templates')
    
    # Load configuration based on environment
    app.config.from_object(config_by_name[config_name])
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting application in {config_name} mode")
    logger.info(f"Static folder path: {static_folder}")
    
    # Initialize CORS
    CORS(app, resources={r"/analyze": {"origins": app.config['CORS_ORIGINS']}})
    
    # Set secret key
    app.secret_key = app.config['SECRET_KEY']
    
    # Custom static route to ensure proper MIME types
    @app.route('/static/<path:filename>')
    def custom_static(filename):
        cache_timeout = app.get_send_file_max_age(filename)
        response = send_from_directory(app.static_folder, filename, 
                                      max_age=cache_timeout)
        
        # Set correct MIME types
        if filename.endswith('.css'):
            response.headers['Content-Type'] = 'text/css'
        elif filename.endswith('.js'):
            response.headers['Content-Type'] = 'application/javascript'
        
        return response
    
    # Debug route to check static files
    @app.route('/debug-static')
    def debug_static():
        import os
        css_path = os.path.join(static_folder, 'css', 'main.css')
        js_path = os.path.join(static_folder, 'js', 'main.js')
        
        result = {
            'static_folder': static_folder,
            'css_exists': os.path.exists(css_path),
            'js_exists': os.path.exists(js_path),
            'css_path': css_path,
            'js_path': js_path,
            'static_files': os.listdir(static_folder) if os.path.exists(static_folder) else []
        }
        
        return f"""
        <h1>Static Files Debug</h1>
        <pre>{str(result)}</pre>
        """
    
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