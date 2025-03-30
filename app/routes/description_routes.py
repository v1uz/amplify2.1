from flask import Blueprint, request, jsonify, render_template
from app.services.bert_service import BERTDescriptionGenerator
from app.utils.content_extractor import ContentExtractor
from app.utils.url_validator import validate_url
import logging

logger = logging.getLogger(__name__)

# Initialize the blueprint
description_bp = Blueprint('description', __name__, url_prefix='/description')

# Initialize services
bert_generator = BERTDescriptionGenerator()
content_extractor = ContentExtractor()

@description_bp.route('/analyze', methods=['POST'])
def analyze_description():
    """
    API endpoint to analyze a URL and generate a company description.
    
    Expected JSON payload:
    {
        "url": "https://example.com"
    }
    
    Returns:
        JSON response with the generated description
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400
    
    url = data['url']
    
    # Validate URL
    if not validate_url(url):
        return jsonify({"error": "Invalid URL format"}), 400
    
    try:
        # Extract content from URL
        extraction_result = content_extractor.extract_from_url(url)
        
        if extraction_result["status"] == "error":
            return jsonify({
                "status": "error",
                "error": extraction_result["error"]
            }), 400
        
        # Generate description from extracted content
        description_result = bert_generator.process_webpage_content(extraction_result["content"])
        
        # Combine results
        result = {
            "status": "success",
            "url": url,
            "title": extraction_result["title"],
            "meta_description": extraction_result["meta_description"],
            "generated_description": description_result["description"],
            "confidence": description_result["confidence"]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@description_bp.route('/view', methods=['GET'])
def view_description_page():
    """
    Render the company description page.
    
    Returns:
        Rendered HTML template
    """
    return render_template('description.html')