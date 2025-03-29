"""
Script to debug static file issues in Flask.

Run this script to check if your static files are properly configured
and accessible.
"""
import os
import sys
import requests
from pathlib import Path

def debug_static_files():
    """Debug static file issues in your Flask application."""
    print("\n=== STATIC FILES DEBUGGER ===")
    
    # 1. Check if Flask is running
    try:
        response = requests.get("http://127.0.0.1:5000/")
        print("✓ Flask server is running")
    except requests.exceptions.ConnectionError:
        print("✗ Flask server is not running or not accessible on http://127.0.0.1:5000/")
        print("  Please start your Flask server first.")
        return
    
    # 2. Check project structure
    print("\n=== Checking Project Structure ===")
    
    # Detect project root (where this script is run from)
    project_root = os.getcwd()
    print(f"Current directory: {project_root}")
    
    # Look for app directory
    app_dir = os.path.join(project_root, 'app')
    if os.path.exists(app_dir) and os.path.isdir(app_dir):
        print(f"✓ Found app directory: {app_dir}")
    else:
        print(f"✗ App directory not found at: {app_dir}")
    
    # Look for static directory
    static_dir = os.path.join(app_dir, 'static')
    if os.path.exists(static_dir) and os.path.isdir(static_dir):
        print(f"✓ Found static directory: {static_dir}")
    else:
        print(f"✗ Static directory not found at: {static_dir}")
        print("  Creating static directory...")
        try:
            os.makedirs(static_dir, exist_ok=True)
            print(f"✓ Created static directory at: {static_dir}")
        except Exception as e:
            print(f"✗ Error creating static directory: {e}")
    
    # Look for CSS directory
    css_dir = os.path.join(static_dir, 'css')
    if os.path.exists(css_dir) and os.path.isdir(css_dir):
        print(f"✓ Found CSS directory: {css_dir}")
    else:
        print(f"✗ CSS directory not found at: {css_dir}")
        print("  Creating CSS directory...")
        try:
            os.makedirs(css_dir, exist_ok=True)
            print(f"✓ Created CSS directory at: {css_dir}")
        except Exception as e:
            print(f"✗ Error creating CSS directory: {e}")
    
    # Check for amplify.css
    amplify_css_path = os.path.join(css_dir, 'amplify.css')
    if os.path.exists(amplify_css_path):
        print(f"✓ Found amplify.css at: {amplify_css_path}")
        # Check permissions
        try:
            with open(amplify_css_path, 'r') as f:
                first_line = f.readline()
                print(f"✓ Successfully read from amplify.css: '{first_line[:30]}...'")
        except Exception as e:
            print(f"✗ Error reading amplify.css: {e}")
    else:
        print(f"✗ amplify.css not found at: {amplify_css_path}")
    
    # 3. Check static file access via HTTP
    print("\n=== Testing Static File Access ===")
    css_url = "http://127.0.0.1:5000/static/css/amplify.css"
    try:
        response = requests.get(css_url)
        if response.status_code == 200:
            print(f"✓ Successfully accessed {css_url}")
            content_type = response.headers.get('Content-Type', '')
            if 'text/css' in content_type:
                print(f"✓ Correct Content-Type: {content_type}")
            else:
                print(f"✗ Unexpected Content-Type: {content_type}")
            print(f"✓ File size: {len(response.text)} bytes")
        else:
            print(f"✗ Failed to access {css_url} - Status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error accessing {css_url}: {e}")
    
    # 4. Check template references
    print("\n=== Checking Template References ===")
    templates_dir = os.path.join(app_dir, 'templates')
    has_correct_references = True
    
    if os.path.exists(templates_dir):
        print(f"✓ Found templates directory: {templates_dir}")
        html_files = list(Path(templates_dir).glob('**/*.html'))
        print(f"  Found {len(html_files)} HTML templates")
        
        for html_file in html_files:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'static/css/amplify.css' in content:
                    print(f"✗ Direct path reference in {html_file.name} - should use url_for()")
                    has_correct_references = False
                elif "{{ url_for('static', filename='css/amplify.css') }}" in content:
                    print(f"✓ Correct reference in {html_file.name}")
                elif 'amplify.css' in content:
                    print(f"? Possible incorrect reference to amplify.css in {html_file.name}")
                    has_correct_references = False
    else:
        print(f"✗ Templates directory not found at: {templates_dir}")
    
    if not has_correct_references:
        print("\nSome templates may have incorrect static file references.")
        print("Make sure to use: {{ url_for('static', filename='css/amplify.css') }}")
    
    # 5. Check Flask static folder configuration
    print("\n=== Checking Flask Configuration ===")
    init_path = os.path.join(app_dir, '__init__.py')
    if os.path.exists(init_path):
        with open(init_path, 'r') as f:
            init_content = f.read()
            if "static_folder" in init_content:
                print("✓ Found static_folder specification in __init__.py")
            else:
                print("? No explicit static_folder setting found in __init__.py")
                print("  Default is 'static' relative to app directory")
    
    # 6. Suggestions
    print("\n=== Suggestions ===")
    print("1. Make sure your Flask app is initialized with the correct static folder:")
    print("   app = Flask(__name__, static_folder='static')")
    print("2. Check if the static directory is readable by the web server")
    print("3. Use url_for() in templates: {{ url_for('static', filename='css/amplify.css') }}")
    print("4. If using blueprint static files, check blueprint static_folder settings")
    print("5. Try restarting your Flask server after making changes")

if __name__ == "__main__":
    debug_static_files()