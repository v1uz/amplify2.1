import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class BERTDescriptionGenerator:
    """Service for generating company descriptions using BERT."""
    
    def __init__(self, model_name='t5-base', device='cpu'):
        """Initialize with error handling"""
        self.model_loaded = False
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.model.to(device)
            self.device = device
            self.model_loaded = True
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            
    def extract_key_content(self, text: str) -> str:
        """
        Extract key content that's relevant for company descriptions.
        This could be enhanced with keyword extraction or other techniques.
        
        Args:
            text: Raw extracted text from a webpage
            
        Returns:
            Filtered text containing relevant company information
        """
        # Simple implementation - could be enhanced with more sophisticated NLP
        paragraphs = text.split('\n')
        # Keep paragraphs that might contain company information
        relevant_paragraphs = []
        
        keywords = ["about", "company", "mission", "vision", "founded", "business", 
                   "service", "product", "industry", "market"]
        
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50:  # Skip very short paragraphs
                if any(keyword in para.lower() for keyword in keywords):
                    relevant_paragraphs.append(para)
        
        # If we couldn't find relevant paragraphs, take the first few substantive ones
        if not relevant_paragraphs and paragraphs:
            relevant_paragraphs = [p for p in paragraphs if len(p.strip()) > 100][:3]
            
        return " ".join(relevant_paragraphs)
    
    def generate_description(self, content: str, max_length: int = 150) -> Dict[str, Any]:
        """
        Generate a concise company description based on extracted content.
        
        Args:
            content: The extracted and filtered website content
            max_length: Maximum token length for the generated description
            
        Returns:
            Dictionary containing the generated description and confidence score
        """
        if not content:
            return {"description": "", "confidence": 0.0}
        
        # Prepare prompt for the model
        prompt = f"Summarize this text into a professional company description: {content}"
        
        try:
            # Tokenize and generate
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate description
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=4,
                    temperature=0.7,
                    top_p=0.9,
                    no_repeat_ngram_size=2,
                    return_dict_in_generate=True,
                    output_scores=True
                )
            
            # Decode generated text
            description = self.tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
            
            # Calculate confidence score (simplified)
            confidence = float(torch.mean(torch.stack(outputs.scores)).cpu().numpy())
            
            return {
                "description": description,
                "confidence": min(confidence * 10, 1.0)  # Scale to 0-1 range
            }
            
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return {"description": "", "confidence": 0.0, "error": str(e)}
    
    def process_webpage_content(self, content: str) -> Dict[str, Any]:
        """
        Process webpage content to generate a company description.
        
        Args:
            content: The raw content extracted from the webpage
            
        Returns:
            Dictionary with generated description and metadata
        """
        # Extract relevant content
        relevant_content = self.extract_key_content(content)
        
        # Generate description
        result = self.generate_description(relevant_content)
        
        # Add metadata
        result["content_length"] = len(content)
        result["relevant_content_length"] = len(relevant_content)
        
        return result