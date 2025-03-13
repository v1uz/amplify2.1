"""
Content Quality Analyzer Module
Analyzes the quality and optimization of webpage content.
"""

import re
from collections import Counter
import logging
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class ContentQualityAnalyzer:
    """Analyzes the quality and optimization of webpage content"""
    
    def __init__(self):
        self.name = "content_analysis"
    
    async def analyze(self, url, raw_data, api_data=None):
        """
        Analyze content quality metrics
        
        Args:
            url (str): The URL being analyzed
            raw_data (dict): Raw data including the parsed BeautifulSoup object
            api_data (dict, optional): Data from external APIs
            
        Returns:
            dict: Content quality analysis results
        """
        try:
            soup = raw_data.get('soup', BeautifulSoup("", 'html.parser'))
            
            # Extract main content
            main_content = self._extract_main_content(soup)
            content_text = self._get_text_content(main_content)
            
            # Calculate content metrics
            word_count = len(content_text.split())
            sentence_count = len(re.split(r'[.!?]+', content_text))
            avg_sentence_length = word_count / max(1, sentence_count)
            
            # Analyze readability
            readability = self._calculate_readability_score(content_text)
            
            # Check keyword density
            keyword_density = self._analyze_keyword_density(content_text)
            
            # Analyze content structure
            structure_score = self._assess_content_structure(soup)
            
            # Check for thin content
            is_thin_content = word_count < 300
            
            # Check for duplicate paragraphs
            duplicate_content = self._check_duplicate_paragraphs(soup)
            
            # Generate recommendations
            recommendations = []
            
            if is_thin_content:
                recommendations.append("Контент слишком короткий. Рекомендуется иметь не менее 300 слов для важных страниц.")
            
            if avg_sentence_length > 25:
                recommendations.append("Средняя длина предложений слишком велика. Для лучшей читаемости сократите предложения.")
                
            if structure_score < 0.7:
                recommendations.append("Улучшите структуру контента, используя подзаголовки (H2, H3) для разделения текста на логические части.")
            
            if readability < 50:
                recommendations.append("Текст слишком сложный для чтения. Упростите язык и используйте более короткие предложения.")
                
            if duplicate_content['has_duplicates']:
                recommendations.append("Обнаружены повторяющиеся параграфы. Устраните дублирование контента.")
            
            return {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_sentence_length": round(avg_sentence_length, 1),
                "readability_score": readability,
                "keyword_density": keyword_density,
                "structure_score": round(structure_score, 2),
                "is_thin_content": is_thin_content,
                "duplicate_content": duplicate_content,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in content quality analysis: {str(e)}")
            return {"error": f"Не удалось проанализировать качество контента: {str(e)}"}
    
    def _extract_main_content(self, soup):
        """Extract the main content area of the page, excluding navigation, footer, etc."""
        # Try to find content by common container IDs/classes
        content_candidates = [
            soup.find('main'),
            soup.find(id='content'),
            soup.find(id='main-content'),
            soup.find(class_='content'),
            soup.find(class_='main-content'),
            soup.find('article')
        ]
        
        # Use the first valid candidate
        for candidate in content_candidates:
            if candidate:
                return candidate
                
        # Fallback to body if no content containers found
        return soup.body or soup
    
    def _get_text_content(self, element):
        """Extract clean text content from an element"""
        if not element:
            return ""
            
        # Extract text and clean it
        text = element.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _calculate_readability_score(self, text):
        """Calculate a simplified readability score (0-100)"""
        words = text.split()
        if not words:
            return 0
            
        # Count complex words (3+ syllables)
        complex_words = 0
        for word in words:
            syllables = self._count_syllables(word)
            if syllables >= 3:
                complex_words += 1
                
        # Calculate percentage of complex words and convert to a score
        complex_percentage = complex_words / max(1, len(words))
        # Invert so higher is better
        readability_score = 100 - (complex_percentage * 100)
        
        return round(readability_score)
    
    def _count_syllables(self, word):
        """Count syllables in a word using a simplified algorithm"""
        word = word.lower()
        # Remove endings
        word = re.sub(r'e$', '', word)
        word = re.sub(r'es$', '', word)
        word = re.sub(r'ed$', '', word)
        
        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_is_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel
            
        return max(1, count)  # Every word has at least one syllable
    
    def _analyze_keyword_density(self, text):
        """Analyze keyword density in the content"""
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return {}
            
        # Remove common stop words (for Russian language)
        stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'о', 'от', 'для', 'из', 'за', 'то', 
                      'что', 'как', 'это', 'этот', 'или', 'но', 'а', 'же', 'если', 'так', 'вот', 
                      'только', 'еще', 'уже', 'даже', 'ну', 'вдруг', 'ли', 'ведь', 'тоже', 'при'}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Count word frequency
        word_counts = Counter(filtered_words)
        total_words = len(filtered_words)
        
        # Calculate density percentages for top keywords
        density = {}
        for word, count in word_counts.most_common(10):
            density[word] = round((count / max(1, total_words)) * 100, 1)
            
        return density
    
    def _assess_content_structure(self, soup):
        """Assess the structure of the content (headings, paragraphs, lists)"""
        # Count structural elements
        paragraphs = len(soup.find_all('p'))
        headings = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        lists = len(soup.find_all(['ul', 'ol']))
        
        # Calculate structure score (0-1)
        text_blocks = paragraphs + 1  # Add 1 to avoid division by zero
        
        # Ideal ratio: At least 1 heading per 3-4 paragraphs, and some lists
        heading_ratio_score = min(1, headings / (text_blocks / 4))
        has_lists_score = 1 if lists > 0 else 0
        
        # Combined score
        structure_score = (heading_ratio_score * 0.7) + (has_lists_score * 0.3)
        
        return structure_score
        
    def _check_duplicate_paragraphs(self, soup):
        """Check for duplicate paragraphs in the content"""
        paragraphs = soup.find_all('p')
        paragraph_texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
        
        # Count occurrences
        text_counts = Counter(paragraph_texts)
        
        # Find duplicates
        duplicates = {text: count for text, count in text_counts.items() if count > 1}
        
        return {
            "has_duplicates": len(duplicates) > 0,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates
        }