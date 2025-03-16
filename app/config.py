"""
Configuration settings for the Amplify application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    DEBUG = False
    TESTING = False
    # Add other common configuration settings here


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Development-specific settings


class ProductionConfig(Config):
    """Production configuration."""
    # Production-specific settings
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Make sure this is set in production


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    # Testing-specific settings


# Dictionary mapping environment names to config classes
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}