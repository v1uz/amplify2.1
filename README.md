# amplify2.1
# Amplify 2.1

Amplify is an AI-powered SEO analysis tool that helps users optimize their websites for search engines and improve performance.

## Features

- Website SEO analysis with actionable recommendations
- Page speed metrics using Google PageSpeed Insights API
- Extraction of key SEO elements (title, meta tags, headings, etc.)
- Responsive and user-friendly interface
- Asynchronous processing for faster results

## Project Structure

```
amplify/
│
├── app/                          # Main application package
│   ├── __init__.py               # Initialize Flask app
│   ├── config.py                 # Configuration settings
│   ├── routes/                   # Route handlers
│   │   ├── __init__.py
│   │   ├── main_routes.py        # Main page routes
│   │   └── analysis_routes.py    # Analysis API routes
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── analyzer.py           # SEO analysis logic
│   │   └── pagespeed.py          # PageSpeed API integration
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── url_validator.py      # URL validation logic
│   │   └── cache_manager.py      # Cache management
│   └── templates/                # HTML templates 
│
├── static/                       # Static assets
│   ├── css/                      # Stylesheet files
│   ├── js/                       # JavaScript files
│   └── img/                      # Image assets
│
├── tests/                        # Unit and integration tests
│
├── .env.example                  # Example environment variables
├── .gitignore                    # Git ignore file
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
└── run.py                        # Application entry point
```

## Prerequisites

- Python 3.8 or higher
- Google PageSpeed Insights API key (optional, but recommended)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/amplify2.1.git
   cd amplify2.1
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file and add your Google PageSpeed API key

## Running the Application

Start the application:
```
python run.py
```

Then open your browser and navigate to http://localhost:5002

## Testing

Run the tests with pytest:
```
pytest
```
