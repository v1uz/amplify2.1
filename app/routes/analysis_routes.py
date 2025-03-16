from flask import Blueprint, request, jsonify, render_template
from app.services.analyzer import get_meta_description
from app.utils.url_validator import validate_url
import requests
from bs4 import BeautifulSoup
import re
import random  # For demo purposes only

# Create blueprint
analysis_bp = Blueprint('analysis', __name__)

# Description generator page
@analysis_bp.route('/description')
def description_page():
    return render_template('description.html')

# API endpoint for description generation
@analysis_bp.route('/api/description', methods=['POST'])
def generate_description():
    data = request.json
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data.get('url')
    regenerate = data.get('regenerate', False)
    
    # Validate URL
    if not validate_url(url):
        return jsonify({'error': 'Invalid URL format'}), 400
    
    try:
        # Fetch webpage content
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else 'Unknown Company'
        
        # Extract meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag.get('content', '') if meta_desc_tag else ''
        
        # Clean up meta description
        meta_description = meta_description.strip() or 'No meta description found'
        
        # In a real app, you'd use BERT or another model here
        # For demo, generate a simple description based on page content
        paragraphs = soup.find_all('p')
        text_content = ' '.join([p.get_text() for p in paragraphs[:5]])
        
        # Simple text processing
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Create a generated description (simplified for demo)
        words = text_content.split()[:50]  # Take first 50 words
        generated_description = ' '.join(words) + '...'
        
        # If no content was found or regenerate was requested,
        # create a fallback or alternative
        if not generated_description or regenerate:
            company_types = ['technology', 'e-commerce', 'service', 'consulting', 'manufacturing']
            adjectives = ['innovative', 'leading', 'trusted', 'experienced', 'customer-focused']
            
            type_idx = hash(url + str(regenerate)) % len(company_types)
            adj_idx = (hash(url + str(regenerate)) + 1) % len(adjectives)
            
            generated_description = (f"A {adjectives[adj_idx]} {company_types[type_idx]} company "
                                    f"dedicated to providing high-quality solutions for clients worldwide. "
                                    f"With years of experience in the industry, {title} offers exceptional "
                                    f"products and services designed to meet modern market demands.")
        
        # Calculate fake confidence score
        confidence = random.randint(70, 95) if regenerate else random.randint(80, 98)
        
        # Return results
        return jsonify({
            'title': title,
            'meta_description': meta_description,
            'generated_description': generated_description,
            'confidence': confidence
        })
    
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch website: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500