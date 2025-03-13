"""
Metadata Analyzer Module
Analyzes SEO metadata of a webpage.
"""

import re
import logging
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class MetaAnalyzer:
    """Analyzes SEO metadata of a webpage"""
    
    def __init__(self):
        self.name = "meta_analysis"
    
    async def analyze(self, url, raw_data, api_data=None):
        """
        Analyze metadata for SEO optimization
        
        Args:
            url (str): The URL being analyzed
            raw_data (dict): Raw data including the parsed BeautifulSoup object
            api_data (dict, optional): Data from external APIs
            
        Returns:
            dict: Metadata analysis results
        """
        try:
            soup = raw_data.get('soup', BeautifulSoup("", 'html.parser'))
            
            # Extract basic metadata with more detailed analysis
            title_analysis = self._analyze_title(soup)
            description_analysis = self._analyze_description(soup)
            keywords_analysis = self._analyze_keywords(soup)
            
            # Social media metadata
            og_meta = self._analyze_open_graph(soup)
            twitter_meta = self._analyze_twitter_cards(soup)
            
            # Additional metadata
            author = soup.find('meta', attrs={'name': 'author'})
            author_content = author['content'] if author and author.has_attr('content') else None
            
            # Language and encoding
            language = self._analyze_language(soup)
            charset = self._analyze_charset(soup)
            
            # Favicons and other icons
            icons = self._analyze_icons(soup)
            
            # Generate recommendations
            recommendations = []
            
            if title_analysis.get('issues', []):
                recommendations.extend(title_analysis['issues'])
                
            if description_analysis.get('issues', []):
                recommendations.extend(description_analysis['issues'])
                
            if keywords_analysis.get('issues', []):
                recommendations.extend(keywords_analysis['issues'])
                
            if not og_meta.get('has_og_tags', False):
                recommendations.append("Добавьте метаданные Open Graph для лучшего отображения при шаринге в социальных сетях.")
                
            if not twitter_meta.get('has_twitter_tags', False):
                recommendations.append("Добавьте метаданные Twitter Cards для улучшения отображения в Twitter.")
                
            if not icons.get('has_favicon', False):
                recommendations.append("Добавьте favicon для узнаваемости вашего сайта.")
                
            if not language.get('has_lang_attribute', False):
                recommendations.append("Укажите атрибут lang в теге html для правильного определения языка страницы.")
            
            # Calculate overall meta score
            score_components = [
                (not title_analysis.get('issues', [])) * 25,  # 25% weight
                (not description_analysis.get('issues', [])) * 25,  # 25% weight
                og_meta.get('has_og_tags', False) * 15,  # 15% weight
                twitter_meta.get('has_twitter_tags', False) * 10,  # 10% weight
                icons.get('has_favicon', False) * 10,  # 10% weight
                language.get('has_lang_attribute', False) * 15  # 15% weight
            ]
            meta_score = sum(score_components)
            
            return {
                "title": title_analysis,
                "description": description_analysis,
                "keywords": keywords_analysis,
                "open_graph": og_meta,
                "twitter_cards": twitter_meta,
                "author": author_content,
                "language": language,
                "charset": charset,
                "icons": icons,
                "meta_score": meta_score,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in metadata analysis: {str(e)}")
            return {"error": f"Не удалось проанализировать метаданные: {str(e)}"}
    
    def _analyze_title(self, soup):
        """Analyze title tag for SEO optimization"""
        title_tag = soup.title
        title = title_tag.string if title_tag else None
        
        if not title:
            return {
                "content": None,
                "length": 0,
                "is_optimized": False,
                "issues": ["Отсутствует title. Добавьте заголовок страницы."]
            }
            
        issues = []
        is_optimized = True
        
        # Check length
        if len(title) < 10:
            issues.append("Заголовок слишком короткий (менее 10 символов).")
            is_optimized = False
        elif len(title) > 60:
            issues.append("Заголовок слишком длинный (более 60 символов). Сократите его для лучшего SEO.")
            is_optimized = False
            
        # Check for keyword stuffing (simplified)
        words = title.lower().split()
        word_counts = {}
        
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_counts[word] = word_counts.get(word, 0) + 1
                
        for word, count in word_counts.items():
            if count > 2 and len(words) > 4:  # More than 2 occurrences and title has more than 4 words
                issues.append(f"Возможный спам ключевых слов в заголовке (повторение '{word}').")
                is_optimized = False
                break
            
        # Check for brand name
        brand_position = None
        common_separators = [' | ', ' - ', ' – ', ' — ', ' :: ', ' > ']
        
        for separator in common_separators:
            if separator in title:
                parts = title.split(separator)
                brand_position = 'prefix' if len(parts) > 1 and len(parts[0]) < 20 else 'suffix'
                break
        
        return {
            "content": title,
            "length": len(title),
            "is_optimized": is_optimized,
            "issues": issues,
            "has_brand": brand_position is not None,
            "brand_position": brand_position
        }
    
    def _analyze_description(self, soup):
        """Analyze meta description for SEO optimization"""
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description['content'] if meta_description and meta_description.has_attr('content') else None
        
        # Fallback to first paragraphs if no description
        if not description:
            paragraphs = soup.find_all('p')
            if paragraphs:
                description = " ".join([p.get_text(strip=True) for p in paragraphs[:2]])
                
        if not description:
            return {
                "content": None,
                "length": 0,
                "is_optimized": False,
                "issues": ["Отсутствует мета-описание. Добавьте краткое описание (150-160 символов)."]
            }
            
        issues = []
        is_optimized = True
        
        # Check length
        if len(description) < 50:
            issues.append("Мета-описание слишком короткое (менее 50 символов).")
            is_optimized = False
        elif len(description) > 160:
            issues.append("Мета-описание слишком длинное (более 160 символов). Сократите его для лучшего отображения в поиске.")
            is_optimized = False
            
        # Check for call to action
        has_cta = bool(re.search(r'узнайте|смотрите|читайте|закажите|купите|позвоните|свяжитесь|получите', description.lower()))
        
        # Check for potential keyword stuffing
        words = description.lower().split()
        word_counts = {}
        
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_counts[word] = word_counts.get(word, 0) + 1
                
        for word, count in word_counts.items():
            if count > 3 and len(words) > 10:  # More than 3 occurrences and description has more than 10 words
                issues.append(f"Возможный спам ключевых слов в описании (повторение '{word}').")
                is_optimized = False
                break
        
        return {
            "content": description,
            "length": len(description),
            "is_optimized": is_optimized,
            "issues": issues,
            "has_cta": has_cta
        }
    
    def _analyze_keywords(self, soup):
        """Analyze meta keywords for SEO optimization"""
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        keywords = keywords_meta['content'] if keywords_meta and keywords_meta.has_attr('content') else None
        
        if not keywords:
            return {
                "content": None,
                "count": 0,
                "is_optimized": False,
                "issues": ["Отсутствуют мета-ключевые слова. Хотя они имеют ограниченное значение для SEO, рекомендуется добавить релевантные ключевые слова."]
            }
            
        keyword_list = [k.strip() for k in keywords.split(',')]
        issues = []
        is_optimized = True
        
        # Check count
        if len(keyword_list) < 3:
            issues.append("Слишком мало ключевых слов. Добавьте больше релевантных ключевых слов.")
            is_optimized = False
        elif len(keyword_list) > 10:
            issues.append("Слишком много ключевых слов. Сократите список до наиболее релевантных.")
            is_optimized = False
            
        # Check for very long keywords
        long_keywords = [k for k in keyword_list if len(k) > 30]
        if long_keywords:
            issues.append("Некоторые ключевые слова слишком длинные. Используйте более короткие и точные термины.")
            is_optimized = False
            
        # Check for duplicates or very similar keywords
        similar_keywords = []
        for i, k1 in enumerate(keyword_list):
            for j, k2 in enumerate(keyword_list):
                if i != j and k1 in k2 and len(k1) > 5:
                    similar_keywords.append((k1, k2))
                    
        if similar_keywords:
            issues.append("Обнаружены похожие или перекрывающиеся ключевые слова.")
            is_optimized = False
            
        return {
            "content": keywords,
            "keywords": keyword_list,
            "count": len(keyword_list),
            "is_optimized": is_optimized,
            "issues": issues
        }
    
    def _analyze_open_graph(self, soup):
        """Analyze Open Graph metadata"""
        og_title = soup.find('meta', property='og:title')
        og_description = soup.find('meta', property='og:description')
        og_image = soup.find('meta', property='og:image')
        og_url = soup.find('meta', property='og:url')
        og_type = soup.find('meta', property='og:type')
        
        has_og_tags = bool(og_title or og_description or og_image or og_url or og_type)
        
        # Check completeness
        is_complete = all([og_title, og_description, og_image, og_url, og_type])
        
        # Check for issues
        issues = []
        if has_og_tags and not is_complete:
            missing = []
            if not og_title:
                missing.append("og:title")
            if not og_description:
                missing.append("og:description")
            if not og_image:
                missing.append("og:image")
            if not og_url:
                missing.append("og:url")
            if not og_type:
                missing.append("og:type")
                
            issues.append(f"Неполные метаданные Open Graph. Отсутствуют: {', '.join(missing)}.")
        
        return {
            "has_og_tags": has_og_tags,
            "is_complete": is_complete,
            "og_title": og_title['content'] if og_title and og_title.has_attr('content') else None,
            "og_description": og_description['content'] if og_description and og_description.has_attr('content') else None,
            "og_image": og_image['content'] if og_image and og_image.has_attr('content') else None,
            "og_url": og_url['content'] if og_url and og_url.has_attr('content') else None,
            "og_type": og_type['content'] if og_type and og_type.has_attr('content') else None,
            "issues": issues
        }
    
    def _analyze_twitter_cards(self, soup):
        """Analyze Twitter Cards metadata"""
        twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        
        has_twitter_tags = bool(twitter_card or twitter_title or twitter_description or twitter_image)
        
        # Check completeness
        is_complete = all([twitter_card, twitter_title, twitter_description, twitter_image])
        
        # Check for issues
        issues = []
        if has_twitter_tags and not is_complete:
            missing = []
            if not twitter_card:
                missing.append("twitter:card")
            if not twitter_title:
                missing.append("twitter:title")
            if not twitter_description:
                missing.append("twitter:description")
            if not twitter_image:
                missing.append("twitter:image")
                
            issues.append(f"Неполные метаданные Twitter Cards. Отсутствуют: {', '.join(missing)}.")
        
        return {
            "has_twitter_tags": has_twitter_tags,
            "is_complete": is_complete,
            "twitter_card": twitter_card['content'] if twitter_card and twitter_card.has_attr('content') else None,
            "twitter_title": twitter_title['content'] if twitter_title and twitter_title.has_attr('content') else None,
            "twitter_description": twitter_description['content'] if twitter_description and twitter_description.has_attr('content') else None,
            "twitter_image": twitter_image['content'] if twitter_image and twitter_image.has_attr('content') else None,
            "issues": issues
        }
        
    def _analyze_language(self, soup):
        """Analyze language settings"""
        html_tag = soup.html
        lang_attr = html_tag.get('lang') if html_tag else None
        
        # Check for content language meta
        content_language = soup.find('meta', attrs={'http-equiv': 'content-language'})
        content_language_value = content_language['content'] if content_language and content_language.has_attr('content') else None
        
        return {
            "has_lang_attribute": bool(lang_attr),
            "lang": lang_attr,
            "content_language": content_language_value,
            "is_consistent": lang_attr == content_language_value if lang_attr and content_language_value else True
        }
        
    def _analyze_charset(self, soup):
        """Analyze character encoding settings"""
        # Check meta charset
        meta_charset = soup.find('meta', charset=True)
        charset_value = meta_charset['charset'] if meta_charset else None
        
        # Check http-equiv
        http_equiv = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        http_equiv_value = http_equiv['content'] if http_equiv and http_equiv.has_attr('content') else None
        
        # Extract charset from http-equiv
        http_equiv_charset = None
        if http_equiv_value and 'charset=' in http_equiv_value:
            http_equiv_charset = http_equiv_value.split('charset=')[1].strip()
            
        return {
            "has_charset": bool(charset_value or http_equiv_charset),
            "charset": charset_value or http_equiv_charset,
            "is_utf8": (charset_value and 'utf-8' in charset_value.lower()) or 
                       (http_equiv_charset and 'utf-8' in http_equiv_charset.lower())
        }
        
    def _analyze_icons(self, soup):
        """Analyze favicon and other icon settings"""
        # Check for favicon links
        favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
        
        # Check for Apple touch icons
        apple_icon = soup.find('link', rel='apple-touch-icon')
        
        # Check for other icon sizes
        icon_sizes = soup.find_all('link', rel=re.compile(r'icon'))
        sizes = [link.get('sizes') for link in icon_sizes if link.has_attr('sizes')]
        
        return {
            "has_favicon": bool(favicon),
            "has_apple_icon": bool(apple_icon),
            "icon_sizes": sizes,
            "has_multiple_sizes": len(sizes) > 1
        }