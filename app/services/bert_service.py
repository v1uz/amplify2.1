import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import os
import re
from langdetect import detect, LangDetectException
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from bs4 import BeautifulSoup, Comment
import html

os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger(__name__)

class BERTDescriptionGenerator:
    def __init__(self, model_name='microsoft/deberta-v3-large', device=None):
        self.model_loaded = False
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model_loaded = True
            logger.info(f"Model {model_name} loaded successfully on {self.device}")
            
            # Initialize additional layers for text generation
            self.generation_head = torch.nn.Linear(
                self.model.config.hidden_size, 
                self.tokenizer.vocab_size
            ).to(self.device)
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    def clean_html(self, html_content: str) -> str:
        """Securely clean HTML content and extract readable text."""
        if not html_content:
            return ""
            
        try:
            # Parse HTML with stricter parser
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove potentially dangerous elements
            for element in soup(['script', 'style', 'iframe', 'noscript', 'head', 
                               'meta', 'link', 'object', 'embed']):
                element.decompose()
                
            # Remove HTML comments
            for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()
                
            # Get text content with spacing
            text = soup.get_text(separator=' ')
            
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[\n\r\t\xa0\u200b\u2800]+', ' ', text)
            
            # Extra security: escape any remaining HTML-like content
            text = html.escape(text)
            
            return text.strip()
        except Exception as e:
            logger.error(f"HTML cleaning error: {e}")
            # Even stricter fallback
            return re.sub(r'<[^>]*>', ' ', html.escape(html_content)).strip()
    
    def detect_language(self, text: str) -> str:
        """Detect text language with fallback."""
        if not text or len(text) < 20:
            return 'en'
            
        try:
            return detect(text[:1000])  # Use first 1000 chars for efficiency
        except:
            return 'en'
    
    def is_valid_content(self, text: str) -> bool:
        """Validate content for processing."""
        if not text or len(text.strip()) < 50:
            return False
            
        # Check for sufficient word content
        words = re.findall(r'\b\w+\b', text)
        if len(words) < 10:
            return False
            
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'(eval|setTimeout|setInterval)\s*\(',
            r'document\.write\(',
            r'<iframe.*?>.*?</iframe>',
            r'style\s*=\s*"[^"]*expression\s*\('
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Suspicious pattern detected: {pattern}")
                return False
                
        return True
    
    # 1. Improved extract_key_content method to filter UI elements
    def extract_key_content(self, text: str) -> str:
        """Extract relevant company information while filtering UI elements."""
        cleaned_text = self.clean_html(text)
        
        if not self.is_valid_content(cleaned_text):
            return ""
        
        # Filter out UI-related content
        ui_patterns = [
            r'carousel', r'button', r'click', r'navigate', r'scroll',
            r'menu', r'tab', r'slider', r'swipe', r'next', r'previous'
        ]
        
        # Filter paragraphs with UI elements
        paragraphs = [p.strip() for p in cleaned_text.split('\n') if len(p.strip()) > 50]
        filtered_paragraphs = []
        for p in paragraphs:
            if not any(re.search(pattern, p.lower()) for pattern in ui_patterns):
                filtered_paragraphs.append(p)
        
        # Extend keywords for better content detection
        lang = self.detect_language(cleaned_text)
        keywords = {
            'en': ["about", "company", "mission", "vision", "founded", "business", 
                "service", "product", "industry", "market", "team", "furniture",
                "store", "collection", "design", "quality", "customer"]
        }
        
        active_keywords = keywords.get(lang, keywords['en'])
        
        # Extract relevant paragraphs with priority
        relevant_paragraphs = [p for p in filtered_paragraphs 
                            if any(k in p.lower() for k in active_keywords)]
        
        # Look for product descriptions or "about us" sections
        if not relevant_paragraphs and filtered_paragraphs:
            # Try to find product descriptions or about sections
            for p in filtered_paragraphs:
                if len(p.split()) > 10 and re.search(r'[.!?]', p):  # Complete sentences
                    relevant_paragraphs.append(p)
                if len(relevant_paragraphs) >= 3:
                    break
        
        # Limit total content length
        combined = " ".join(relevant_paragraphs)
        return combined[:1500] if len(combined) > 1500 else combined

    
    def generate_description(self, content: str, max_length: int = 150, target_language: str = 'en', timeout: int = 15) -> Dict[str, Any]:
        if not content or not self.model_loaded:
            return {"description": "", "confidence": 0.0}
        
        # Your existing content cleaning and validation code remains unchanged
        
        # Modified prompt for BERT models
        prompt = (
            f"TASK: Create a professional company description.\n\n"
            f"REQUIREMENTS:\n"
            f"1. Write 4-5 complete sentences about the business itself\n"
            f"2. Must describe the company's main products, services, or purpose\n"
            f"3. Must be properly formatted with correct grammar\n"
            f"4. Must NOT include descriptions of website UI elements (carousels, buttons, navigation)\n"
            f"5. Must focus on WHAT the business does, not how their website works\n"
            f"6. Must be coherent, professional business description only\n\n"
            f"TEXT: {content}\n\n"
            f"COMPANY DESCRIPTION:"
        )
        
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._generate_with_model, prompt, max_length)
                result = future.result(timeout=timeout)
            return result
        except TimeoutError:
            logger.error(f"Model generation timed out after {timeout} seconds")
            return {"description": "", "confidence": 0.0, "error": f"Generation timed out after {timeout} seconds"}
        except Exception as e:
            logger.error(f"Error in model generation: {str(e)}")
            return {"description": "", "confidence": 0.0, "error": str(e)}
    
    def _generate_with_model(self, prompt: str, max_length: int) -> Dict[str, Any]:
        """Modified to use BERT/DeBERTa for text generation."""
        try:
            # Tokenize with prompt
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # BERT-specific generation approach using auto-regressive generation
            generated_tokens = []
            input_ids = inputs["input_ids"]
            attention_mask = inputs["attention_mask"]
            
            confidence_scores = []
            
            # Auto-regressive generation loop
            for _ in range(max_length):
                with torch.no_grad():
                    # Get model outputs
                    outputs = self.model(
                        input_ids=input_ids,
                        attention_mask=attention_mask
                    )
                    
                    # Get the last hidden state for prediction
                    last_hidden_state = outputs.last_hidden_state[:, -1, :]
                    
                    # Get next token logits
                    logits = self.generation_head(last_hidden_state)
                    
                    # Apply sampling for text generation
                    next_token_logits = logits / 0.7  # Temperature
                    
                    # Filter out special tokens if needed
                    for special_token_id in self.tokenizer.all_special_ids:
                        next_token_logits[0, special_token_id] = -float('inf')
                    
                    # Apply softmax to get probabilities
                    probs = torch.nn.functional.softmax(next_token_logits, dim=-1)
                    
                    # Sample from the distribution
                    next_token = torch.multinomial(probs, num_samples=1)
                    
                    # Calculate confidence
                    token_confidence = probs[0, next_token.item()].item()
                    confidence_scores.append(token_confidence)
                    
                    # Check for EOS token
                    if next_token.item() == self.tokenizer.eos_token_id:
                        break
                    
                    # Append to generated tokens
                    generated_tokens.append(next_token.item())
                    
                    # Update input_ids and attention_mask for next iteration
                    input_ids = torch.cat([input_ids, next_token], dim=-1)
                    attention_mask = torch.cat([
                        attention_mask, 
                        torch.ones((1, 1), dtype=torch.long, device=self.device)
                    ], dim=-1)
            
            # Decode the generated tokens
            description = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            description = description.strip()
            
            # Additional safety check - ensure no HTML
            if "<" in description or "javascript" in description.lower():
                description = html.escape(description)
            
            # Calculate overall confidence
            if confidence_scores:
                confidence = float(np.mean(confidence_scores))
                confidence = max(min(confidence, 1.0), 0.0)
            else:
                confidence = 0.0
            
            return {
                "description": description,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Model generation error: {e}")
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