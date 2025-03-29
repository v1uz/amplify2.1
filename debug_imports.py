"""
Debug script to help identify import issues.

Run this script to see detailed information about import errors.
"""
import os
import sys
import traceback

def debug_imports():
    """
    Attempt to import key modules and print debug information.
    """
    print("\n=== Python Environment Information ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    
    # Check if app directory exists and is accessible
    app_dir = os.path.join(os.getcwd(), 'app')
    print(f"\nApp directory path: {app_dir}")
    if os.path.exists(app_dir):
        print("  ✓ App directory exists")
        # List files in app directory
        files = os.listdir(app_dir)
        print(f"  Files in app directory: {files}")
    else:
        print("  ✗ App directory does not exist!")
    
    # Check services directory
    services_dir = os.path.join(app_dir, 'services')
    print(f"\nServices directory path: {services_dir}")
    if os.path.exists(services_dir):
        print("  ✓ Services directory exists")
        # List files in services directory
        files = os.listdir(services_dir)
        print(f"  Files in services directory: {files}")
        
        # Check analyzer.py specifically
        analyzer_path = os.path.join(services_dir, 'analyzer.py')
        if os.path.exists(analyzer_path):
            print("  ✓ analyzer.py exists")
        else:
            print("  ✗ analyzer.py does not exist!")
    else:
        print("  ✗ Services directory does not exist!")
    
    # Test imports
    print("\n=== Import Tests ===")
    try:
        print("Trying import: from app import app")
        from app import app
        print("  ✓ Successfully imported app")
    except ImportError as e:
        print(f"  ✗ Failed to import app: {e}")
        print(f"    {traceback.format_exc()}")
    
    try:
        print("\nTrying import: from app.services import analyzer")
        from app.services import analyzer
        print("  ✓ Successfully imported analyzer module")
        
        print("\nTrying import: from app.services.analyzer import analyze_website")
        from app.services.analyzer import analyze_website
        print("  ✓ Successfully imported analyze_website function")
    except ImportError as e:
        print(f"  ✗ Failed to import: {e}")
        print(f"    {traceback.format_exc()}")
    
    try:
        print("\nTrying import: from app.services.bert_service import BERTDescriptionGenerator")
        from app.services.bert_service import BERTDescriptionGenerator
        print("  ✓ Successfully imported BERTDescriptionGenerator")
    except ImportError as e:
        print(f"  ✗ Failed to import: {e}")
        print(f"    {traceback.format_exc()}")
    
    print("\n=== End of Debug Info ===")

if __name__ == "__main__":
    # Insert the current directory into the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    debug_imports()