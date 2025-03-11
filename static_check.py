import os
import mimetypes

def check_static_files():
    """Check for static files and their MIME types."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    static_folder = os.path.join(project_root, 'static')
    
    if not os.path.exists(static_folder):
        print(f"ERROR: Static folder not found at: {static_folder}")
        return
    
    print(f"Static folder exists at: {static_folder}")
    
    # Check CSS files
    css_folder = os.path.join(static_folder, 'css')
    if os.path.exists(css_folder):
        print(f"CSS folder exists at: {css_folder}")
        css_files = os.listdir(css_folder)
        print(f"CSS files: {css_files}")
        
        for css_file in css_files:
            file_path = os.path.join(css_folder, css_file)
            mime_type = mimetypes.guess_type(file_path)[0]
            print(f"  {css_file}: {mime_type}")
    else:
        print(f"ERROR: CSS folder not found at: {css_folder}")
    
    # Check JS files
    js_folder = os.path.join(static_folder, 'js')
    if os.path.exists(js_folder):
        print(f"JS folder exists at: {js_folder}")
        js_files = os.listdir(js_folder)
        print(f"JS files: {js_files}")
        
        for js_file in js_files:
            file_path = os.path.join(js_folder, js_file)
            mime_type = mimetypes.guess_type(file_path)[0]
            print(f"  {js_file}: {mime_type}")
    else:
        print(f"ERROR: JS folder not found at: {js_folder}")

if __name__ == "__main__":
    check_static_files()