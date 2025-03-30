"""
Configuration settings for the Amplify SEO application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration."""
    
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # PageSpeed API settings
    PAGESPEED_API_KEY = os.environ.get('PAGESPEED_API_KEY', '')
    
    # BERT model settings
    BERT_MODEL_NAME = os.environ.get('BERT_MODEL_NAME', 't5-base')
    BERT_DEVICE = os.environ.get('BERT_DEVICE', 'cpu')
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    
    # Cache settings
    CACHE_DIR = 'cache'
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    BERT_MODEL_NAME = os.environ.get('BERT_MODEL_NAME') or 't5-base'  # Matching your existing implementation
    GPT_API_KEY = os.environ.get('OPENAI_API_KEY')
    MAX_TOKEN_LENGTH = int(os.environ.get('MAX_TOKEN_LENGTH') or 500)
    GPT_RATE_LIMIT = int(os.environ.get('GPT_RATE_LIMIT') or 20)  # Seconds to wait between rate-limited requests


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    
    # Use a stronger secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Cache settings
    CACHE_DEFAULT_TIMEOUT = 86400  # 24 hours
    
    # Logging
    LOG_LEVEL = 'ERROR'


# Dictionary mapping environment names to config classes
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}