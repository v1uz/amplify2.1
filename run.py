"""
Amplify 2.1 application entry point.
This script serves as the entry point for running the Amplify SEO analysis application.
"""

import os
import asyncio
import logging
from hypercorn.config import Config
from hypercorn.asyncio import serve
from dotenv import load_dotenv
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Starting application initialization...")

# Before each important import
logger.debug("About to import create_app...")
from app import create_app
logger.debug("Successfully imported create_app")

# Load environment variables from .env file
load_dotenv()

# Import the application factory
from app import create_app

# Create application instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Configure Hypercorn
        config = Config()
        config.bind = [os.getenv('BIND', '0.0.0.0:5002')]
        config.use_reloader = os.getenv('USE_RELOADER', 'True').lower() == 'true'
        
        # Get environment for display
        environment = os.getenv('FLASK_ENV', 'development')
        port = config.bind[0].split(':')[1]
        
        # Log startup information
        logger.info(f"Starting Amplify 2.1 in {environment} mode")
        logger.info(f"Server running at http://localhost:{port}")
        logger.info(f"Press Ctrl+C to quit")
        
        # Start the server
        asyncio.run(serve(app, config))
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()