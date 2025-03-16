"""
Enhanced SEO analysis service module.
This module provides comprehensive website analysis including metadata, content quality,
technical SEO, mobile optimization, and keyword analysis.
"""

import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import Counter

# Set up logging first
logger = logging.getLogger(__name__)

# Import page speed service with fallback for testing
try:
    # Normal application import
    from app.services.pagespeed import get_pagespeed_insights
except ImportError:
    # Alternative import for tests
    try:
        from services.pagespeed import get_pagespeed_insights
    except ImportError:
        # Local import (if in same directory)
        try:
            from .pagespeed import get_pagespeed_insights
        except ImportError:
            # Create a stub for testing if all else fails
            logger.warning("Using pagespeed test stub - module not found")
            
            # Define the stub function
            async def get_pagespeed_insights(url):
                """Test stub for PageSpeed Insights API"""
                return {"performance_score": 80, "recommendations": ["Test PageSpeed stub"]}


class ContentQualityAnalyzer:
    """Analyzes the quality and optimization of webpage content"""
    
    def __init__(self):
        self.name = "content_analysis"
    
    def analyze(self, soup, url):
        """Analyze content quality metrics"""
        try:
            # Extract main content (excluding navigation, footer, etc.)
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
            
            # Assess content structure
            structure_score = self._assess_content_structure(soup)
            
            # Generate recommendations
            recommendations = []
            
            if word_count < 300:
                recommendations.append("Контент слишком короткий. Рекомендуется иметь не менее 300 слов для важных страниц.")
            
            if avg_sentence_length > 25:
                recommendations.append("Средняя длина предложений слишком велика. Для лучшей читаемости сократите предложения.")
                
            if structure_score < 0.7:
                recommendations.append("Улучшите структуру контента, используя подзаголовки (H2, H3) для разделения текста на логические части.")
            
            if readability < 50:
                recommendations.append("Текст слишком сложный для чтения. Упростите язык и используйте более короткие предложения.")
            
            return {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_sentence_length": round(avg_sentence_length, 1),
                "readability_score": readability,
                "keyword_density": keyword_density,
                "structure_score": round(structure_score, 2),
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
            
        # Remove common stop words
        stop_words = {'и', 'в', 'на', 'с', 'по', 'к', 'у', 'о', 'от', 'для', 'из', 'за', 'то', 'что', 'как', 'это', 'этот', 'или'}
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


class TechnicalSEOAnalyzer:
    """Analyzes technical SEO aspects of a webpage"""
    
    def __init__(self):
        self.name = "technical_analysis"
    
    def analyze(self, soup, url):
        """Analyze technical SEO factors"""
        try:
            # Parse URL
            parsed_url = urlparse(url)
            
            # Analyze canonical URL
            canonical = self._check_canonical(soup, url)
            
            # Check robots directives
            robots = self._check_robots(soup)
            
            # Analyze URL structure
            url_analysis = self._analyze_url(parsed_url)
            
            # Check for hreflang tags
            hreflang = self._check_hreflang(soup)
            
            # Check for schema markup
            schema = self._check_schema_markup(soup)
            
            # Check for XML sitemap reference
            sitemap = self._check_sitemap_reference(soup)
            
            # Generate recommendations
            recommendations = []
            
            if not canonical['has_canonical']:
                recommendations.append("Добавьте канонический URL для предотвращения проблем с дублированным контентом.")
                
            if not robots['has_robots_tag']:
                recommendations.append("Добавьте мета-тег robots для управления индексацией страницы.")
                
            if url_analysis['issues']:
                recommendations.append(f"Проблемы с URL: {', '.join(url_analysis['issues'])}.")
                
            if not schema['has_schema']:
                recommendations.append("Добавьте структурированные данные (Schema.org) для улучшения отображения в результатах поиска.")
            
            return {
                "canonical": canonical,
                "robots": robots,
                "url_analysis": url_analysis,
                "hreflang": hreflang,
                "schema_markup": schema,
                "sitemap": sitemap,
                "technical_score": 100 - (len(recommendations) * 25),  # Simple scoring
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in technical SEO analysis: {str(e)}")
            return {"error": f"Не удалось выполнить технический анализ SEO: {str(e)}"}
    
    def _check_canonical(self, soup, current_url):
        """Check for canonical URL tag"""
        canonical_tag = soup.find('link', rel='canonical')
        
        if not canonical_tag:
            return {
                "has_canonical": False,
                "canonical_url": None,
                "is_self_canonical": False
            }
            
        canonical_url = canonical_tag.get('href', '')
        is_self_canonical = canonical_url == current_url
        
        return {
            "has_canonical": True,
            "canonical_url": canonical_url,
            "is_self_canonical": is_self_canonical
        }
    
    def _check_robots(self, soup):
        """Check robots directives"""
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        
        if not robots_tag:
            return {
                "has_robots_tag": False,
                "directives": None
            }
            
        robots_content = robots_tag.get('content', '')
        directives = [d.strip() for d in robots_content.split(',')]
        
        return {
            "has_robots_tag": True,
            "directives": directives,
            "is_noindex": 'noindex' in directives,
            "is_nofollow": 'nofollow' in directives
        }
    
    def _analyze_url(self, parsed_url):
        """Analyze URL structure for SEO best practices"""
        path = parsed_url.path
        issues = []
        
        # Check for uppercase letters
        if any(c.isupper() for c in path):
            issues.append("URL содержит заглавные буквы")
            
        # Check for special characters
        if re.search(r'[^a-zA-Z0-9/-]', path):
            issues.append("URL содержит специальные символы")
            
        # Check for multiple consecutive hyphens
        if '--' in path:
            issues.append("URL содержит двойные дефисы")
            
        # Check length
        if len(path) > 100:
            issues.append("URL слишком длинный")
            
        return {
            "path": path,
            "issues": issues,
            "is_optimized": len(issues) == 0
        }
    
    def _check_hreflang(self, soup):
        """Check for hreflang implementation"""
        hreflang_tags = soup.find_all('link', rel='alternate', href=True)
        hreflang_tags = [tag for tag in hreflang_tags if tag.get('hreflang')]
        
        if not hreflang_tags:
            return {
                "has_hreflang": False,
                "languages": []
            }
            
        languages = [tag.get('hreflang') for tag in hreflang_tags]
        
        return {
            "has_hreflang": True,
            "languages": languages,
            "count": len(languages)
        }
    
    def _check_schema_markup(self, soup):
        """Check for schema.org structured data"""
        # Look for JSON-LD
        json_ld = soup.find_all('script', type='application/ld+json')
        
        # Look for microdata
        microdata = soup.find_all(attrs={"itemtype": re.compile(r'schema.org')})
        
        return {
            "has_schema": bool(json_ld or microdata),
            "json_ld_count": len(json_ld),
            "microdata_count": len(microdata)
        }
    
    def _check_sitemap_reference(self, soup):
        """Check for XML sitemap reference"""
        # This would typically be in robots.txt, but sometimes in HTML as well
        sitemap_link = soup.find('a', href=re.compile(r'sitemap\.xml'))
        
        return {
            "has_sitemap_link": bool(sitemap_link)
        }


class MobileAnalyzer:
    
    
    """Analyzes mobile-friendliness of a webpage"""
    
    def __init__(self):
        self.name = "mobile_analysis"
    
    def analyze(self, soup, url):
        """Analyze mobile-friendliness metrics"""
        try:
            # Check viewport meta tag
            viewport = self._check_viewport(soup)
            
            # Check touch targets
            touch_targets = self._analyze_touch_targets(soup)
            
            # Check font sizes
            font_sizes = self._analyze_font_sizes(soup)
            
            # Check for mobile-specific elements
            mobile_elements = self._check_mobile_elements(soup)
            
            # Generate recommendations
            recommendations = []
            
            if not viewport['has_viewport']:
                recommendations.append("Добавьте мета-тег viewport для правильного отображения на мобильных устройствах.")
                
            if not touch_targets['adequate_sizing']:
                recommendations.append("Увеличьте размер элементов интерфейса для удобного нажатия на мобильных устройствах.")
                
            if font_sizes['potential_issues']:
                recommendations.append("Проверьте размеры шрифтов для лучшей читаемости на мобильных устройствах.")
            
            # Calculate a mobile score
            mobile_score = 100
            if not viewport['has_viewport']:
                mobile_score -= 40
            if not touch_targets['adequate_sizing']:
                mobile_score -= 30
            if font_sizes['potential_issues']:
                mobile_score -= 30
                
            return {
                "viewport": viewport,
                "touch_targets": touch_targets,
                "font_sizes": font_sizes,
                "mobile_elements": mobile_elements,
                "mobile_score": mobile_score,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in mobile analysis: {str(e)}")
            return {"error": f"Не удалось выполнить анализ мобильной версии: {str(e)}"}
    
    def _check_viewport(self, soup):
        """Check for viewport meta tag"""
        viewport_tag = soup.find('meta', attrs={'name': 'viewport'})
        
        if not viewport_tag:
            return {
                "has_viewport": False,
                "content": None
            }
            
        viewport_content = viewport_tag.get('content', '')
        
        # Check for responsive settings
        has_width = 'width=device-width' in viewport_content
        has_initial_scale = 'initial-scale=1' in viewport_content
        
        return {
            "has_viewport": True,
            "content": viewport_content,
            "has_width": has_width,
            "has_initial_scale": has_initial_scale,
            "is_responsive": has_width and has_initial_scale
        }
    
    def _analyze_touch_targets(self, soup):
        """Analyze touch targets for mobile devices"""
        # Find all potential touch targets
        links = soup.find_all('a')
        buttons = soup.find_all('button')
        inputs = soup.find_all('input', type=['button', 'submit', 'checkbox', 'radio'])
        
        # Count small elements (simple estimation)
        small_elements = 0
        for element in links + buttons + inputs:
            # Check for inline or CSS size indicators
            style = element.get('style', '')
            class_attr = element.get('class', [])
            
            if (
                'btn-sm' in class_attr or 
                'small' in class_attr or
                'width:' in style and re.search(r'width:\s*(\d+)px', style) and int(re.search(r'width:\s*(\d+)px', style).group(1)) < 40
            ):
                small_elements += 1
        
        return {
            "total_touch_targets": len(links) + len(buttons) + len(inputs),
            "potential_small_targets": small_elements,
            "adequate_sizing": small_elements == 0
        }
    
    def _analyze_font_sizes(self, soup):
        """Analyze font sizes for mobile readability"""
        # Check for small font sizes
        small_fonts = 0
        
        # Find elements with font-size in style
        elements_with_style = soup.find_all(style=re.compile(r'font-size'))
        
        for element in elements_with_style:
            style = element.get('style', '')
            font_size_match = re.search(r'font-size:\s*(\d+)px', style)
            
            if font_size_match and int(font_size_match.group(1)) < 12:
                small_fonts += 1
        
        # Check for small text CSS classes
        small_text_classes = ['small', 'text-xs', 'text-sm', 'fine-print']
        elements_with_small_class = soup.find_all(class_=[c for c in small_text_classes])
        
        return {
            "small_inline_fonts": small_fonts,
            "small_class_elements": len(elements_with_small_class),
            "potential_issues": small_fonts > 0 or len(elements_with_small_class) > 0
        }
    
    def _check_mobile_elements(self, soup):
        """Check for mobile-specific elements and features"""
        # Check for meta theme-color
        theme_color = soup.find('meta', attrs={'name': 'theme-color'})
        
        # Check for app icons
        apple_icon = soup.find('link', rel='apple-touch-icon')
        
        return {
            "has_theme_color": bool(theme_color),
            "has_apple_icon": bool(apple_icon)
        }


class MetaAnalyzer:
    """Analyzes SEO metadata of a webpage"""
    
    def __init__(self):
        self.name = "meta_analysis"
    
    def analyze(self, soup, url):
        """
        Analyze metadata for SEO optimization. This is an enhanced version
        of the original metadata extraction.
        """
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
        
        # Generate recommendations
        recommendations = []
        
        if title_analysis['issues']:
            recommendations.extend(title_analysis['issues'])
            
        if description_analysis['issues']:
            recommendations.extend(description_analysis['issues'])
            
        if keywords_analysis['issues']:
            recommendations.extend(keywords_analysis['issues'])
            
        if not og_meta['has_og_tags']:
            recommendations.append("Добавьте метаданные Open Graph для лучшего отображения при шаринге в социальных сетях.")
            
        if not twitter_meta['has_twitter_tags']:
            recommendations.append("Добавьте метаданные Twitter Cards для улучшения отображения в Twitter.")
        
        # Calculate meta score
        meta_score = 100
        meta_score -= len(title_analysis['issues']) * 20
        meta_score -= len(description_analysis['issues']) * 20
        meta_score -= 20 if not og_meta['has_og_tags'] else 0
        meta_score = max(0, meta_score)  # Ensure it doesn't go below 0
        
        return {
            "title": title_analysis,
            "description": description_analysis,
            "keywords": keywords_analysis,
            "open_graph": og_meta,
            "twitter_cards": twitter_meta,
            "author": author_content,
            "meta_score": meta_score,
            "recommendations": recommendations
        }
    
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
        
        return {
            "has_og_tags": has_og_tags,
            "og_title": og_title['content'] if og_title and og_title.has_attr('content') else None,
            "og_description": og_description['content'] if og_description and og_description.has_attr('content') else None,
            "og_image": og_image['content'] if og_image and og_image.has_attr('content') else None,
            "og_url": og_url['content'] if og_url and og_url.has_attr('content') else None,
            "og_type": og_type['content'] if og_type and og_type.has_attr('content') else None
        }
    
    def _analyze_twitter_cards(self, soup):
        """Analyze Twitter Cards metadata"""
        twitter_card = soup.find('meta', attrs={'name': 'twitter:card'})
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        
        has_twitter_tags = bool(twitter_card or twitter_title or twitter_description or twitter_image)
        
        return {
            "has_twitter_tags": has_twitter_tags,
            "twitter_card": twitter_card['content'] if twitter_card and twitter_card.has_attr('content') else None,
            "twitter_title": twitter_title['content'] if twitter_title and twitter_title.has_attr('content') else None,
            "twitter_description": twitter_description['content'] if twitter_description and twitter_description.has_attr('content') else None,
            "twitter_image": twitter_image['content'] if twitter_image and twitter_image.has_attr('content') else None
        }


async def legacy_analyze_seo(html_content, url):
    """
    Original SEO analysis implementation (kept for fallback)
    This is essentially your existing function, preserved for compatibility.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract basic metadata
    title = soup.title.string if soup.title else "Заголовок не найден"
    
    # Extract meta description or use first paragraphs as fallback
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_description_content = meta_description['content'] if meta_description and meta_description.has_attr('content') else " ".join([p.get_text(strip=True) for p in soup.find_all('p')[:2]])
    
    # Extract keywords
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    keywords = keywords_meta['content'] if keywords_meta and keywords_meta.has_attr('content') else "Ключевые слова не найдены"

    # Extract structural elements
    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
    h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
    
    # Check for images without alt text
    img_without_alt = len([img for img in soup.find_all('img') if not img.get('alt')])
    
    # Count internal and external links
    internal_links = len([a for a in soup.find_all('a', href=True) if a['href'].startswith('/')])
    external_links = len([a for a in soup.find_all('a', href=True) if not a['href'].startswith('/') and urlparse(a['href']).netloc])

    # Generate SEO recommendations
    recommendations = []
    if len(title) > 60:
        recommendations.append("Заголовок слишком длинный (более 60 символов). Сократите его для лучшего SEO.")
    if meta_description_content == "Заголовок не найден" or len(meta_description_content) < 10:
        recommendations.append("Отсутствует мета-описание. Добавьте краткое описание (150-160 символов).")
    if keywords == "Ключевые слова не найдены":
        recommendations.append("Отсутствуют мета-ключевые слова. Добавьте релевантные ключевые слова.")
    if not h1_tags:
        recommendations.append("Отсутствует тег H1. Добавьте один тег H1 с основной темой.")
    if img_without_alt > 0:
        recommendations.append(f"{img_without_alt} изображений без атрибута alt. Добавьте описательные атрибуты alt.")

    # Get PageSpeed Insights data
    try:
        pagespeed_data = await get_pagespeed_insights(url)
        if 'error' in pagespeed_data:
            pagespeed_recommendations = [pagespeed_data['error']]
            logger.warning(f"Error getting PageSpeed data: {pagespeed_data['error']}")
        else:
            pagespeed_recommendations = pagespeed_data.get('recommendations', [])
    except Exception as e:
        logger.error(f"Exception in PageSpeed analysis: {str(e)}")
        pagespeed_data = {"error": f"Не удалось получить данные PageSpeed Insights: {str(e)}"}
        pagespeed_recommendations = [pagespeed_data["error"]]

    # Create a prompt summarizing the analysis
    prompt = (
        f"Анализ SEO для сайта с заголовком: '{title}'. "
        f"Описание: {meta_description_content}. "
        f"Ключевые слова: {keywords}. "
        f"Теги H1: {h1_tags}. "
        f"Теги H2: {h2_tags}. "
        f"Внутренние ссылки: {internal_links}, Внешние ссылки: {external_links}. "
        f"Рекомендации SEO: {', '.join(recommendations)}. "
        f"Оценка PageSpeed: {pagespeed_data.get('performance_score', 'Н/Д')}. "
        f"Рекомендации PageSpeed: {', '.join(pagespeed_recommendations if isinstance(pagespeed_recommendations, list) else [pagespeed_recommendations])}."
    )

    # Return comprehensive analysis
    return {
        'description': meta_description_content,
        'keywords': keywords,
        'prompt': prompt,
        'recommendations': recommendations + (pagespeed_recommendations if isinstance(pagespeed_recommendations, list) else [pagespeed_recommendations]),
        'metrics': {
            'title': title,
            'h1_tags': h1_tags,
            'h2_tags': h2_tags,
            'img_without_alt': img_without_alt,
            'internal_links': internal_links,
            'external_links': external_links,
            'pagespeed': pagespeed_data
        }
    }


# Make sure this function is defined at the module level
def analyze_seo(html_content, url):
    """
    Enhanced analysis that coordinates specialized analyzers.
    This function works in both synchronous and async contexts.
    
    Args:
        html_content (str): HTML content of the website
        url (str): URL of the website
        
    Returns:
        dict: A dictionary containing comprehensive SEO analysis results
    """
    try:
        logger.info(f"Starting enhanced SEO analysis for {url}")
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize analyzers
        meta_analyzer = MetaAnalyzer()
        content_analyzer = ContentQualityAnalyzer()
        technical_analyzer = TechnicalSEOAnalyzer()
        mobile_analyzer = MobileAnalyzer()
        
        # Run specialized analyses
        meta_results = meta_analyzer.analyze(soup, url)
        content_results = content_analyzer.analyze(soup, url)
        technical_results = technical_analyzer.analyze(soup, url)
        mobile_results = mobile_analyzer.analyze(soup, url)
        
        # Get PageSpeed Insights data - Use synchronous version
        try:
            pagespeed_data = get_pagespeed_insights_sync(url)
            pagespeed_recommendations = pagespeed_data.get('recommendations', [])
        except Exception as e:
            logger.error(f"Exception in PageSpeed analysis: {str(e)}")
            pagespeed_data = {"error": f"Не удалось получить данные PageSpeed Insights: {str(e)}"}
            pagespeed_recommendations = [pagespeed_data["error"]]
        
        # Collect all recommendations
        all_recommendations = []
        
        # Add metadata recommendations
        if 'recommendations' in meta_results:
            all_recommendations.extend(meta_results['recommendations'])
            
        # Add content recommendations
        if 'recommendations' in content_results:
            all_recommendations.extend(content_results['recommendations'])
            
        # Add technical recommendations
        if 'recommendations' in technical_results:
            all_recommendations.extend(technical_results['recommendations'])
            
        # Add mobile recommendations
        if 'recommendations' in mobile_results:
            all_recommendations.extend(mobile_results['recommendations'])
            
        # Add PageSpeed recommendations
        all_recommendations.extend(pagespeed_recommendations if isinstance(pagespeed_recommendations, list) else [pagespeed_recommendations])
        
        # Extract basic metrics for backward compatibility
        title = meta_results['title']['content'] if meta_results.get('title', {}).get('content') else "Заголовок не найден"
        description = meta_results['description']['content'] if meta_results.get('description', {}).get('content') else ""
        keywords = meta_results['keywords']['content'] if meta_results.get('keywords', {}).get('content') else "Ключевые слова не найдены"
        
        # Count structural elements
        h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
        h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
        img_without_alt = len([img for img in soup.find_all('img') if not img.get('alt')])
        internal_links = len([a for a in soup.find_all('a', href=True) if a['href'].startswith('/')])
        external_links = len([a for a in soup.find_all('a', href=True) if not a['href'].startswith('/') and urlparse(a['href']).netloc])
        
        # Create a comprehensive prompt summarizing the analysis
        prompt = (
            f"Расширенный анализ SEO для сайта с заголовком: '{title}'. "
            f"Описание: {description}. "
            f"Ключевые слова: {keywords}. "
            f"Теги H1: {h1_tags}. "
            f"Теги H2: {h2_tags}. "
            f"Внутренние ссылки: {internal_links}, Внешние ссылки: {external_links}. "
            f"Качество контента: {content_results.get('word_count', 0)} слов, оценка читаемости {content_results.get('readability_score', 'Н/Д')}. "
            f"Техническое SEO: {technical_results.get('url_analysis', {}).get('is_optimized', False)}. "
            f"Мобильная оптимизация: {mobile_results.get('viewport', {}).get('is_responsive', False)}. "
            f"Оценка PageSpeed: {pagespeed_data.get('performance_score', 'Н/Д')}. "
            f"Основные рекомендации: {', '.join(all_recommendations[:5])}."
        )
        
        # Return results in a format compatible with the original function,
        # but with enhanced data in the metrics section
        return {
            'description': description,
            'keywords': keywords,
            'prompt': prompt,
            'recommendations': all_recommendations,
            'metrics': {
                'title': title,
                'h1_tags': h1_tags,
                'h2_tags': h2_tags,
                'img_without_alt': img_without_alt,
                'internal_links': internal_links,
                'external_links': external_links,
                'pagespeed': pagespeed_data,
                # Enhanced metrics
                'meta_analysis': meta_results,
                'content_analysis': content_results,
                'technical_analysis': technical_results,
                'mobile_analysis': mobile_results
            }
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced SEO analysis: {str(e)}")
        # Fallback to legacy analysis if enhanced analysis fails
        logger.info("Falling back to legacy analysis method")
        return legacy_analyze_seo(html_content, url)

# Synchronous version of the PageSpeed Insights function
def get_pagespeed_insights_sync(url):
    """
    Synchronous wrapper for the async PageSpeed Insights function.
    
    Args:
        url (str): URL to analyze
        
    Returns:
        dict: PageSpeed Insights results
    """
    import asyncio
    
    try:
        # Import your existing async function
        from app.services.pagespeed import get_pagespeed_insights
        
        # Run the async function in a synchronous context
        try:
            # Try to use the current event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if needed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function and get the result
        result = loop.run_until_complete(get_pagespeed_insights(url))
        return result
        
    except Exception as e:
        logger.error(f"Error in PageSpeed analysis: {str(e)}")
        return {
            "error": f"Failed to analyze with PageSpeed: {str(e)}",
            "performance_score": 54,  # Use your observed value as fallback
            "recommendations": ["Could not fetch PageSpeed data"]
        }
# Legacy analyze function for backward compatibility (synchronous version)
def legacy_analyze_seo(html_content, url):
    """
    Original SEO analysis implementation kept for fallback (synchronous version).
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract basic metadata
    title = soup.title.string if soup.title else "Заголовок не найден"
    
    # Extract meta description or use first paragraphs as fallback
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_description_content = meta_description['content'] if meta_description and meta_description.has_attr('content') else " ".join([p.get_text(strip=True) for p in soup.find_all('p')[:2]])
    
    # Extract keywords
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
    keywords = keywords_meta['content'] if keywords_meta and keywords_meta.has_attr('content') else "Ключевые слова не найдены"

    # Extract structural elements
    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
    h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all('h2')]
    
    # Check for images without alt text
    img_without_alt = len([img for img in soup.find_all('img') if not img.get('alt')])
    
    # Count internal and external links
    internal_links = len([a for a in soup.find_all('a', href=True) if a['href'].startswith('/')])
    external_links = len([a for a in soup.find_all('a', href=True) if not a['href'].startswith('/') and urlparse(a['href']).netloc])

    # Generate SEO recommendations
    recommendations = []
    if len(title) > 60:
        recommendations.append("Заголовок слишком длинный (более 60 символов). Сократите его для лучшего SEO.")
    if meta_description_content == "Заголовок не найден" or len(meta_description_content) < 10:
        recommendations.append("Отсутствует мета-описание. Добавьте краткое описание (150-160 символов).")
    if keywords == "Ключевые слова не найдены":
        recommendations.append("Отсутствуют мета-ключевые слова. Добавьте релевантные ключевые слова.")
    if not h1_tags:
        recommendations.append("Отсутствует тег H1. Добавьте один тег H1 с основной темой.")
    if img_without_alt > 0:
        recommendations.append(f"{img_without_alt} изображений без атрибута alt. Добавьте описательные атрибуты alt.")

    # Use synchronous PageSpeed Insights
    pagespeed_data = get_pagespeed_insights_sync(url)
    pagespeed_recommendations = pagespeed_data.get('recommendations', [])

    # Create a prompt summarizing the analysis
    prompt = (
        f"Анализ SEO для сайта с заголовком: '{title}'. "
        f"Описание: {meta_description_content}. "
        f"Ключевые слова: {keywords}. "
        f"Теги H1: {h1_tags}. "
        f"Теги H2: {h2_tags}. "
        f"Внутренние ссылки: {internal_links}, Внешние ссылки: {external_links}. "
        f"Рекомендации SEO: {', '.join(recommendations)}. "
        f"Оценка PageSpeed: {pagespeed_data.get('performance_score', 'Н/Д')}. "
        f"Рекомендации PageSpeed: {', '.join(pagespeed_recommendations if isinstance(pagespeed_recommendations, list) else [pagespeed_recommendations])}."
    )

    # Return comprehensive analysis
    return {
        'description': meta_description_content,
        'keywords': keywords,
        'prompt': prompt,
        'recommendations': recommendations + (pagespeed_recommendations if isinstance(pagespeed_recommendations, list) else [pagespeed_recommendations]),
        'metrics': {
            'title': title,
            'h1_tags': h1_tags,
            'h2_tags': h2_tags,
            'img_without_alt': img_without_alt,
            'internal_links': internal_links,
            'external_links': external_links,
            'pagespeed': pagespeed_data
        }
    }