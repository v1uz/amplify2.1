"""
Entry point for the Amplify SEO application.

This file is used to run the Flask application.
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the Flask application
from app import app as application

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the application
    application.run(host="0.0.0.0", port=port, debug=True)