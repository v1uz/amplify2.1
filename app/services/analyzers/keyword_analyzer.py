"""
Keyword Analyzer Module
Analyzes keyword optimization and usage across a webpage.
"""

import re
import logging
from collections import Counter
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class KeywordOptimizationAnalyzer:
    """Analyzes keyword optimization and usage across a webpage"""
    
    def __init__(self):
        self.name = "keyword_analysis"
    
    async def analyze(self, url, raw_data, api_data=None):
        """
        Analyze keyword optimization
        
        Args:
            url (str): The URL being analyzed
            raw_data (dict): Raw data including the parsed BeautifulSoup object
            api_data (dict, optional): Data from external APIs
            
        Returns:
            dict: Keyword optimization analysis results
        """
        try:
            soup = raw_data.get('soup', BeautifulSoup("", 'html.parser'))
            
            # Extract metadata
            meta_keywords = self._extract_meta_keywords(soup)
            
            # Extract all page text
            page_text = self._extract_text_content(soup)
            
            # Auto-detect important keywords from content
            detected_keywords = self._detect_keywords(page_text)
            
            # Analyze keyword placement in important elements
            placement = self._analyze_keyword_placement(soup, detected_keywords)
            
            # Analyze keyword density
            density = self._analyze_keyword_density(page_text, detected_keywords)
            
            # Analyze semantic relevance
            semantic = self._analyze_semantic_relevance(soup, detected_keywords)
            
            # Check for keyword targeting issues
            issues = self._check_keyword_issues(
                meta_keywords, detected_keywords, placement, density)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                meta_keywords, detected_keywords, placement, density, issues)
            
            # Calculate overall keyword score
            keyword_score = self._calculate_keyword_score(
                meta_keywords, placement, density, issues)
            
            return {
                "meta_keywords": meta_keywords,
                "detected_keywords": detected_keywords,
                "placement": placement,
                "density": density,
                "semantic_relevance": semantic,
                "issues": issues,
                "recommendations": recommendations,
                "keyword_score": keyword_score
            }
            
        except Exception as e:
            logger.error(f"Error in keyword analysis: {str(e)}")
            return {"error": f"Не удалось выполнить анализ ключевых слов: {str(e)}"}
    
    def _extract_meta_keywords(self, soup):
        """Extract keywords from meta tags"""
        # Meta keywords tag
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords_content = meta_keywords['content'] if meta_keywords and meta_keywords.has_attr('content') else ""
        
        # Meta description for supplementary keywords
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description_content = meta_description['content'] if meta_description and meta_description.has_attr('content') else ""
        
        # Process keywords from meta keywords
        keywords = []
        if keywords_content:
            keywords = [k.strip().lower() for k in keywords_content.split(',') if k.strip()]
            
        # Extract potential keywords from description
        if description_content:
            words = re.findall(r'\b\w+\b', description_content.lower())
            stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'о', 'от', 'для', 'из', 'за', 'то', 
                         'что', 'как', 'это', 'этот', 'или', 'но', 'а', 'же'}
            desc_keywords = [w for w in words if len(w) > 3 and w not in stop_words]
            
            # Add description keywords that aren't already in the list
            for keyword in desc_keywords:
                if keyword not in keywords and not any(keyword in k for k in keywords):
                    keywords.append(keyword)
        
        return {
            "has_meta_keywords": bool(meta_keywords),
            "keywords": keywords,
            "count": len(keywords)
        }
    
    def _extract_text_content(self, soup):
        """Extract all visible text content"""
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav"]):
            script.extract()
            
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _detect_keywords(self, text):
        """Auto-detect important keywords from content"""
        # Tokenize text
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove common stop words
        stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'о', 'от', 'для', 'из', 'за', 'то', 
                     'что', 'как', 'это', 'этот', 'или', 'но', 'а', 'же', 'если', 'так', 'вот', 
                     'только', 'еще', 'уже', 'даже', 'ну', 'вдруг', 'ли', 'ведь', 'тоже', 'при'}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Count word frequency
        word_counts = Counter(filtered_words)
        
        # Get most common words
        common_words = word_counts.most_common(10)
        
        # Process into keyword objects
        keywords = []
        for word, count in common_words:
            keywords.append({
                "keyword": word,
                "count": count,
                "density": round((count / max(1, len(filtered_words))) * 100, 1)
            })
            
        return {
            "keywords": keywords,
            "total_words": len(filtered_words)
        }
    
    def _analyze_keyword_placement(self, soup, detected_keywords):
        """Analyze keyword placement in important elements"""
        # Get primary keywords (top 5)
        primary_keywords = [k["keyword"] for k in detected_keywords.get("keywords", [])[:5]]
        
        # Check title
        title = soup.title.string if soup.title else ""
        title_lower = title.lower() if title else ""
        
        keywords_in_title = [k for k in primary_keywords if k in title_lower]
        
        # Check headings
        h1 = soup.find('h1')
        h1_text = h1.get_text(strip=True).lower() if h1 else ""
        
        h2s = soup.find_all('h2')
        h2_texts = [h.get_text(strip=True).lower() for h in h2s]
        
        keywords_in_h1 = [k for k in primary_keywords if k in h1_text]
        keywords_in_h2 = [k for k in primary_keywords if any(k in h2 for h2 in h2_texts)]
        
        # Check URL
        url_parts = soup.find('meta', attrs={'property': 'og:url'})
        url = url_parts['content'].lower() if url_parts and url_parts.has_attr('content') else ""
        
        keywords_in_url = [k for k in primary_keywords if k in url]
        
        # Check first paragraph
        first_p = soup.find('p')
        first_p_text = first_p.get_text(strip=True).lower() if first_p else ""
        
        keywords_in_first_p = [k for k in primary_keywords if k in first_p_text]
        
        # Check alt text
        alt_texts = [img.get('alt', '').lower() for img in soup.find_all('img') if img.has_attr('alt')]
        
        keywords_in_alt = [k for k in primary_keywords if any(k in alt for alt in alt_texts)]
        
        # Calculate placement score (0-100)
        placement_score = 0
        if primary_keywords:  # Avoid division by zero
            # Calculate percentages of placement
            title_percentage = len(keywords_in_title) / len(primary_keywords) * 100
            h1_percentage = len(keywords_in_h1) / len(primary_keywords) * 100
            h2_percentage = len(keywords_in_h2) / len(primary_keywords) * 100
            url_percentage = len(keywords_in_url) / len(primary_keywords) * 100
            p1_percentage = len(keywords_in_first_p) / len(primary_keywords) * 100
            alt_percentage = len(keywords_in_alt) / len(primary_keywords) * 100
            
            # Weight the percentages
            placement_score = (
                (title_percentage * 0.3) +  # 30% weight
                (h1_percentage * 0.2) +     # 20% weight
                (h2_percentage * 0.15) +    # 15% weight
                (url_percentage * 0.15) +   # 15% weight
                (p1_percentage * 0.1) +     # 10% weight
                (alt_percentage * 0.1)      # 10% weight
            )
        
        return {
            "title": {
                "keywords": keywords_in_title,
                "count": len(keywords_in_title)
            },
            "h1": {
                "keywords": keywords_in_h1,
                "count": len(keywords_in_h1)
            },
            "h2": {
                "keywords": keywords_in_h2,
                "count": len(keywords_in_h2)
            },
            "url": {
                "keywords": keywords_in_url,
                "count": len(keywords_in_url)
            },
            "first_paragraph": {
                "keywords": keywords_in_first_p,
                "count": len(keywords_in_first_p)
            },
            "alt_text": {
                "keywords": keywords_in_alt,
                "count": len(keywords_in_alt)
            },
            "placement_score": round(placement_score)
        }
    
    def _analyze_keyword_density(self, text, detected_keywords):
        """Analyze keyword density and distribution"""
        # Get all keywords
        keywords = [k["keyword"] for k in detected_keywords.get("keywords", [])]
        
        # Get total content length
        total_words = len(re.findall(r'\b\w+\b', text))
        
        # Analyze density per section (simplified by splitting text)
        sections = text.split('. ')  # Split by periods
        
        # Ensure at least 3 sections for analysis
        if len(sections) < 3:
            chunks = []
            chunk_size = max(1, len(text) // 3)
            for i in range(0, len(text), chunk_size):
                chunks.append(text[i:i+chunk_size])
            sections = chunks
            
        # Check distribution across sections
        distribution = {}
        for keyword in keywords:
            section_counts = []
            for section in sections:
                # Count occurrences in section (case insensitive)
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', section.lower()))
                section_counts.append(count)
                
            # Calculate distribution metrics
            distribution[keyword] = {
                "counts": section_counts,
                "total": sum(section_counts),
                "is_well_distributed": max(section_counts) <= 2 and sum(section_counts) >= 2
            }
            
        # Check for keyword stuffing (high density)
        stuffing_threshold = 5.0  # 5% is often considered too high
        potential_stuffing = []
        
        for k in detected_keywords.get("keywords", []):
            if k["density"] > stuffing_threshold:
                potential_stuffing.append(k["keyword"])
        
        return {
            "total_keywords": len(distribution),
            "distribution": distribution,
            "potential_stuffing": potential_stuffing,
            "has_keyword_stuffing": bool(potential_stuffing)
        }
    
    def _analyze_semantic_relevance(self, soup, detected_keywords):
        """Analyze semantic relevance and related terms"""
        # This is a simplified implementation as a full semantic analysis
        # would typically require external APIs or more complex NLP
        
        # Get primary keywords
        primary_keywords = [k["keyword"] for k in detected_keywords.get("keywords", [])[:3]]
        
        # Look for related terms based on context
        related_terms = {}
        
        for keyword in primary_keywords:
            # Find paragraphs containing the keyword
            paragraphs = []
            for p in soup.find_all('p'):
                p_text = p.get_text(strip=True).lower()
                if keyword in p_text:
                    paragraphs.append(p_text)
                    
            # Extract potential related terms
            context_words = set()
            for p in paragraphs:
                words = re.findall(r'\b\w+\b', p)
                # Get words near the keyword
                for i, word in enumerate(words):
                    if word.lower() == keyword:
                        # Get context window (3 words before and after)
                        start = max(0, i-3)
                        end = min(len(words), i+4)
                        context = words[start:end]
                        # Add words to context set
                        for w in context:
                            if len(w) > 3 and w.lower() != keyword:
                                context_words.add(w.lower())
                                
            related_terms[keyword] = list(context_words)[:5]  # Top 5 related terms
            
        return {
            "related_terms": related_terms
        }
    
    def _check_keyword_issues(self, meta_keywords, detected_keywords, placement, density):
        """Check for keyword targeting and optimization issues"""
        issues = []
        
        # Check if meta keywords match detected keywords
        meta_kw_set = set(meta_keywords.get("keywords", []))
        detected_kw_set = set(k["keyword"] for k in detected_keywords.get("keywords", [])[:5])
        
        meta_kw_match = len(meta_kw_set.intersection(detected_kw_set))
        
        if meta_keywords.get("has_meta_keywords", False) and meta_kw_match == 0:
            issues.append("Мета-ключевые слова не соответствуют контенту страницы.")
            
        # Check for critical placement issues
        if not placement.get("title", {}).get("count", 0):
            issues.append("Ключевые слова отсутствуют в заголовке страницы (title).")
            
        if not placement.get("h1", {}).get("count", 0):
            issues.append("Ключевые слова отсутствуют в основном заголовке (H1).")
            
        # Check for keyword stuffing
        if density.get("has_keyword_stuffing", False):
            issues.append(f"Обнаружено переоптимизированное использование ключевых слов: {', '.join(density.get('potential_stuffing', []))}.")
            
        # Check for keyword cannibalization (multiple main keywords)
        top_keywords = detected_keywords.get("keywords", [])[:2]
        if len(top_keywords) >= 2:
            # Check if top keywords are too similar or if one is contained in another
            if (top_keywords[0]["density"] > 0.5 and top_keywords[1]["density"] > 0.5 and
                (top_keywords[0]["keyword"] in top_keywords[1]["keyword"] or
                 top_keywords[1]["keyword"] in top_keywords[0]["keyword"])):
                issues.append("Возможная каннибализация ключевых слов: присутствуют похожие основные ключевые слова.")
        
        return issues
    
    def _generate_recommendations(self, meta_keywords, detected_keywords, placement, density, issues):
        """Generate keyword optimization recommendations"""
        recommendations = []
        
        # Add recommendations based on identified issues
        for issue in issues:
            if "мета-ключевые слова не соответствуют" in issue.lower():
                recommendations.append("Обновите мета-ключевые слова, чтобы они соответствовали фактическому содержимому страницы.")
                
            elif "отсутствуют в заголовке" in issue.lower():
                recommendations.append("Добавьте основные ключевые слова в заголовок страницы (title).")
                
            elif "отсутствуют в основном заголовке" in issue.lower():
                recommendations.append("Включите основные ключевые слова в тег H1.")
                
            elif "переоптимизированное использование" in issue.lower():
                recommendations.append("Уменьшите плотность ключевых слов, сделайте текст более естественным.")
                
            elif "каннибализация ключевых слов" in issue.lower():
                recommendations.append("Выберите одно основное ключевое слово для страницы и оптимизируйте для него.")
        
        # Add general recommendations based on analysis
        if placement.get("placement_score", 0) < 50:
            recommendations.append("Улучшите размещение ключевых слов в важных элементах страницы (заголовок, H1, H2, первый абзац).")
            
        if detected_keywords.get("total_words", 0) < 300:
            recommendations.append("Добавьте больше содержимого с соответствующими ключевыми словами для улучшения релевантности.")
            
        if not meta_keywords.get("has_meta_keywords", False):
            recommendations.append("Добавьте мета-тег keywords с релевантными ключевыми словами.")
            
        if not placement.get("alt_text", {}).get("count", 0):
            recommendations.append("Включите ключевые слова в атрибуты alt изображений, где это уместно.")
            
        return recommendations
    
    def _calculate_keyword_score(self, meta_keywords, placement, density, issues):
        """Calculate overall keyword optimization score"""
        # Base score
        score = 100
        
        # Deduct for missing meta keywords
        if not meta_keywords.get("has_meta_keywords", False):
            score -= 5
            
        # Deduct for placement issues
        if placement.get("placement_score", 0) < 50:
            score -= 20
        elif placement.get("placement_score", 0) < 70:
            score -= 10
            
        # Deduct for keyword stuffing
        if density.get("has_keyword_stuffing", False):
            score -= 15
            
        # Deduct for each identified issue
        score -= len(issues) * 5
        
        # Ensure score is within range
        return max(0, min(100, score))