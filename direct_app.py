import os
from flask import Flask, send_from_directory

app = Flask(__name__)

# Set the path to your static folder
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

@app.route('/static/<path:filename>')
def static_files(filename):
    # Explicitly set Content-Type based on file extension
    response = send_from_directory(static_folder, filename)
    
    if filename.endswith('.css'):
        response.headers['Content-Type'] = 'text/css'
    elif filename.endswith('.js'):
        response.headers['Content-Type'] = 'application/javascript'
    
    return response

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Static Test</title>
        <link rel="stylesheet" href="/static/css/main.css">
    </head>
    <body>
        <h1 class="hero-title">This should be styled</h1>
        <script src="/static/js/main.js"></script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True, port=5002)