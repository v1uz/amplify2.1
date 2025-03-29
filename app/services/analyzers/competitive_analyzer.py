"""
Competitive Analysis Module
Analyzes a webpage in comparison to top competitors.
(Note: Full implementation requires external API access)
"""

import logging
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class CompetitiveAnalyzer:
    """Analyzes a webpage in comparison to top competitors"""
    
    def __init__(self):
        self.name = "competitive_analysis"
    
    async def analyze(self, url, raw_data, api_data=None):
        """
        Analyze a webpage in comparison to competitors
        
        Args:
            url (str): The URL being analyzed
            raw_data (dict): Raw data including the parsed BeautifulSoup object
            api_data (dict, optional): Data from external APIs (SemRush, etc.)
            
        Returns:
            dict: Competitive analysis results
        """
        try:
            # This is a simplified implementation that would normally use
            # external APIs (SemRush, Ahrefs, etc.) for complete analysis
            
            soup = raw_data.get('soup', BeautifulSoup("", 'html.parser'))
            domain = urlparse(url).netloc
            
            # Extract content metrics
            content_metrics = self._analyze_content_metrics(soup)
            
            # Check for competitive keywords (simplified without API)
            keywords = self._extract_potential_keywords(soup)
            
            # Handle SemRush API data if available
            semrush_data = api_data.get('semrush', {}) if api_data else {}
            
            # Generate recommendations
            recommendations = self._generate_recommendations(content_metrics, semrush_data)
            
            # For a fully implemented version, we would include:
            # - Competitor ranking analysis
            # - Backlink comparison
            # - Shared/unique keywords
            # - Content gap analysis
            
            return {
                "domain": domain,
                "content_metrics": content_metrics,
                "potential_keywords": keywords,
                "semrush_data": semrush_data,
                "is_limited": True,  # Indicates this is a limited implementation
                "recommendations": recommendations,
                "requires_api": True  # Indicates full analysis requires API access
            }
            
        except Exception as e:
            logger.error(f"Error in competitive analysis: {str(e)}")
            return {
                "error": f"Не удалось выполнить конкурентный анализ: {str(e)}",
                "is_limited": True,
                "requires_api": True
            }
    
    def _analyze_content_metrics(self, soup):
        """Analyze content metrics for competitive comparison"""
        # Word count
        text_content = soup.get_text(strip=True)
        words = re.findall(r'\b\w+\b', text_content)
        word_count = len(words)
        
        # Headings count
        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        
        # List items
        list_items = len(soup.find_all('li'))
        
        # Images
        images = len(soup.find_all('img'))
        
        # Tables
        tables = len(soup.find_all('table'))
        
        # Videos (simplified check)
        videos = len(soup.find_all(['video', 'iframe']))
        
        # Outbound links
        links = soup.find_all('a', href=True)
        outbound_links = 0
        for link in links:
            href = link['href']
            if href.startswith(('http://', 'https://')) and urlparse(url).netloc not in href:
                outbound_links += 1
                
        return {
            "word_count": word_count,
            "headings": {
                "h1": h1_count,
                "h2": h2_count,
                "h3": h3_count,
                "total": h1_count + h2_count + h3_count
            },
            "list_items": list_items,
            "images": images,
            "tables": tables,
            "videos": videos,
            "outbound_links": outbound_links,
            "content_score": min(100, word_count / 50)  # Simplified score
        }
    
    def _extract_potential_keywords(self, soup):
        """Extract potential competitive keywords from content"""
        # This is a simplified implementation without external API data
        
        # Get title and headings
        title = soup.title.string if soup.title else ""
        headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])]
        
        # Combine and extract potential keywords
        all_text = title + " " + " ".join(headings)
        words = re.findall(r'\b\w+\b', all_text.lower())
        
        # Remove stop words (simplified list)
        stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'о', 'от', 'для', 'из'}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Get potential keyword phrases (2-3 words)
        phrases = []
        for i in range(len(words) - 1):
            if words[i] not in stop_words and len(words[i]) > 3:
                # Two-word phrases
                phrases.append(words[i] + " " + words[i+1])
                
                # Three-word phrases
                if i < len(words) - 2:
                    phrases.append(words[i] + " " + words[i+1] + " " + words[i+2])
        
        return {
            "single_words": filtered_words[:10],  # Top 10 potential single keywords
            "phrases": phrases[:5]  # Top 5 potential keyword phrases
        }
    
    def _generate_recommendations(self, content_metrics, semrush_data):
        """Generate competitive recommendations"""
        recommendations = []
        
        # Content-based recommendations
        if content_metrics.get("word_count", 0) < 500:
            recommendations.append("Расширьте содержание страницы. Конкурирующие страницы обычно имеют более развернутый контент.")
            
        if content_metrics.get("headings", {}).get("total", 0) < 3:
            recommendations.append("Добавьте больше заголовков для улучшения структуры и улучшения SEO.")
            
        if content_metrics.get("images", 0) < 2:
            recommendations.append("Добавьте больше изображений для повышения привлекательности контента.")
            
        # Generic recommendation about API integration
        recommendations.append("Для полного конкурентного анализа рекомендуется интеграция с API SemRush, Ahrefs или аналогичными сервисами.")
        
        return recommendations