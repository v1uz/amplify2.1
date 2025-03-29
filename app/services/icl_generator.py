# app/services/icl_generator.py

import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModel
import torch

class ICLGenerator:
    def __init__(self):
        # Load BERT model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        self.model = AutoModel.from_pretrained('bert-base-uncased')
        
    def extract_meta_data(self, url):
        """Extract meta description and keywords from a webpage"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract meta description
            meta_desc = ""
            meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_desc_tag and 'content' in meta_desc_tag.attrs:
                meta_desc = meta_desc_tag['content']
                
            # Extract meta keywords
            meta_keywords = ""
            meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords_tag and 'content' in meta_keywords_tag.attrs:
                meta_keywords = meta_keywords_tag['content']
                
            return {
                'description': meta_desc,
                'keywords': meta_keywords
            }
        except Exception as e:
            return {
                'description': "",
                'keywords': "",
                'error': str(e)
            }
    
    def generate_bert_embeddings(self, text):
        """Generate BERT embeddings for the given text"""
        if not text:
            return None
            
        # Tokenize and get BERT embeddings
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use the [CLS] token embedding as the sentence representation
        embeddings = outputs.last_hidden_state[:, 0, :].numpy()
        return embeddings
        
    def generate_icl_prompt(self, url):
        """Generate ICL prompt based on BERT and meta keywords"""
        # Extract meta data
        meta_data = self.extract_meta_data(url)
        
        # Combine description and keywords
        combined_text = f"{meta_data.get('description', '')} {meta_data.get('keywords', '')}"
        
        # Generate embeddings if text exists
        embeddings = self.generate_bert_embeddings(combined_text)
        
        # Generate prompt based on the embeddings and meta data
        prompt = self._format_icl_prompt(meta_data, embeddings)
        
        return prompt
        
    def _format_icl_prompt(self, meta_data, embeddings):
        """Format ICL prompt template using meta data and embeddings"""
        # Create a template for ICL
        prompt = f"""\
        Analyze the following website with these characteristics:
        
        Description: {meta_data.get('description', 'No description available')}
        Keywords: {meta_data.get('keywords', 'No keywords available')}
        
        Based on this information, provide a detailed SEO analysis covering:
        1. Keyword relevance and optimization
        2. Meta tag effectiveness
        3. Content quality assessment
        4. Suggested improvements
        
        Previous similar websites have shown these patterns:
        [Insert relevant patterns based on embeddings here]
        
        Please provide a comprehensive analysis:
        """
        
        return prompt