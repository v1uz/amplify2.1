"""
Configuration settings for different environments.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with common settings across all environments."""
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    PAGESPEED_API_KEY = os.getenv('PAGESPEED_API_KEY', '')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5002')
    
    @staticmethod
    def init_app(app):
        """Initialize the application with this configuration."""
        pass

class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    FLASK_ENV = 'development'
    
class TestingConfig(Config):
    """Configuration for testing environment."""
    DEBUG = True
    TESTING = True
    
class ProductionConfig(Config):
    """Configuration for production environment."""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # In production, ensure a strong secret key is set
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Ensure API key is set in production
        if not cls.PAGESPEED_API_KEY:
            app.logger.error("PAGESPEED_API_KEY is not set in production!")

# Dictionary mapping environment names to configuration classes
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}