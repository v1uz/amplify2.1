import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-amplify'
    
    # Cache settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT') or 300)  # 5 minutes
    
    # API Keys
    PAGESPEED_API_KEY = os.environ.get('PAGESPEED_API_KEY') or ''
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS') or '*'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # More secure secret key required in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Set to True only if using HTTPS
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}