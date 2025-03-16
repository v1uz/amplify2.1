"""
Amplify 2.1 - Main application initialization
This module initializes the Flask application and sets up all necessary configurations and extensions.
"""

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
    
    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.analysis_routes import analysis_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    
    # Register description blueprint if you've added it
    try:
        from app.routes.description_routes import description_bp
        app.register_blueprint(description_bp)
    except ImportError:
        # If description_routes.py doesn't exist yet, skip this
        pass
    
    return app