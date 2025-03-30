"""
Amplify SEO Flask Application.

This module initializes the Flask application and registers all blueprints.
"""
from flask import Flask
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure the app directory is in the Python path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
parent_dir = os.path.abspath(os.path.dirname(app_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration name to use
        
    Returns:
        Configured Flask application
    """
    # Create Flask app - explicitly set static and template folders
    app = Flask(__name__, 
                static_folder='static', 
                template_folder='templates')
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app.config['ENVIRONMENT'] = config_name  # Store environment name for our own use
    
    if config_name == 'production':
        app.config.from_object('app.config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')
    
    # Load environment variables from .env file
    if os.path.exists('.env'):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            logger.warning("python-dotenv not installed. Environment variables from .env will not be loaded.")
    
    # Configure app-specific settings
    configure_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def configure_app(app):
    """
    Configure app-specific settings.
    
    Args:
        app: Flask application instance
    """
    # Set secret key
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Configure session
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # Force debug mode for development
    if app.config['ENVIRONMENT'] == 'development':
        app.debug = True
    
    # Enable CSRF protection if needed
    # from flask_wtf.csrf import CSRFProtect
    # csrf = CSRFProtect(app)
    
    # Configure cache directory
    cache_dir = os.path.join(app.root_path, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    app.config['CACHE_DIR'] = cache_dir
    
    # Set PageSpeed API key if available
    app.config['PAGESPEED_API_KEY'] = os.getenv('PAGESPEED_API_KEY', '')
    
    # Use our custom ENVIRONMENT key instead of ENV (which might not be set in newer Flask versions)
    env_name = app.config.get('ENVIRONMENT', 'development')
    logger.info(f"App configured for {env_name} environment")

def register_blueprints(app):
    """
    Register all blueprints with the application.
    
    Args:
        app: Flask application instance
    """
    try:
        # Import blueprints
        from app.routes.main_routes import main_bp
        from app.routes.analysis_routes import analysis_bp
        
        # Register blueprints
        app.register_blueprint(main_bp)
        app.register_blueprint(analysis_bp, url_prefix='/analysis')
        
        # Register description blueprint if it exists
        try:
            from app.routes.description_routes import description_bp
            app.register_blueprint(description_bp)
            logger.info("Description blueprint registered")
        except ImportError:
            # If description_routes.py doesn't exist yet, skip this
            logger.info("Description blueprint not found, skipping")
            pass
        
        logger.info("Blueprints registered successfully")
    except Exception as e:
        logger.error(f"Error registering blueprints: {str(e)}")
        logger.exception("Full traceback:")
        # Keep going even if blueprint registration fails
        # This allows the app to start and show an error message

def register_error_handlers(app):
    """
    Register custom error handlers.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def page_not_found(e):
        # Try to render the custom 404 template
        try:
            from flask import render_template
            return render_template('errors/404.html'), 404
        except:
            # Fallback to basic HTML response
            return "<h1>404 - Page Not Found</h1><p>The requested URL was not found on the server.</p>", 404
            
    @app.errorhandler(500)
    def internal_server_error(e):
        # Try to render the custom 500 template
        try:
            from flask import render_template
            return render_template('errors/500.html'), 500
        except:
            # Fallback to basic HTML response
            return "<h1>500 - Internal Server Error</h1><p>An unexpected error occurred.</p>", 500

# Create the application instance
app = create_app()

# This makes the app package importable
if __name__ == '__main__':
    app.run(debug=True)