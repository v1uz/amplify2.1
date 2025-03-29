from venv import logger
from flask import Config, Flask, send_from_directory, request
from flask_cors import CORS
import os
import logging
import mimetypes
from cachetools import TTLCache
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig

# Initialize cache
cache = TTLCache(maxsize=100, ttl=3600)

def create_app(config_class=None):
    """
    Application factory function.
    
    Args:
        config_class: Configuration class or string naming environment
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Handle configuration
    if config_class is None:
        from app.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    elif isinstance(config_class, str):
        # If config_class is a string (e.g., 'development'), map it to the right config class
        if config_class.lower() == 'development':
            from app.config import DevelopmentConfig
            app.config.from_object(DevelopmentConfig)
        elif config_class.lower() == 'production':
            from app.config import ProductionConfig
            app.config.from_object(ProductionConfig)
        elif config_class.lower() == 'testing':
            from app.config import TestingConfig
            app.config.from_object(TestingConfig)
        else:
            raise ValueError(f"Unknown configuration: {config_class}")
    else:
        # Assume config_class is an actual configuration class
        app.config.from_object(config_class)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.analysis_routes import analysis_bp
    
    # Important: Register blueprints without any prefix to ensure routes work as expected
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    
    # Register description blueprint if you've added it
    try:
        from app.routes.description_routes import description_bp
        app.register_blueprint(description_bp)
    except ImportError:
        # If description_routes.py doesn't exist yet, skip this
        pass
        
    # Debug route registrations
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule.endpoint} -> {rule.rule}")
    
    return app