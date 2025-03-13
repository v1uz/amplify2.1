"""
Mobile Optimization Analyzer Module
Analyzes mobile-friendliness and responsiveness of webpages.
"""

import re
import logging
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class MobileAnalyzer:
    """Analyzes mobile-friendliness of a webpage"""
    
    def __init__(self):
        self.name = "mobile_analysis"
    
    async def analyze(self, url, raw_data, api_data=None):
        """
        Analyze mobile-friendliness metrics
        
        Args:
            url (str): The URL being analyzed
            raw_data (dict): Raw data including the parsed BeautifulSoup object
            api_data (dict, optional): Data from external APIs
            
        Returns:
            dict: Mobile optimization analysis results
        """
        try:
            soup = raw_data.get('soup', BeautifulSoup("", 'html.parser'))
            
            # Check viewport meta tag
            viewport = self._check_viewport(soup)
            
            # Check touch targets
            touch_targets = self._analyze_touch_targets(soup)
            
            # Check font sizes
            font_sizes = self._analyze_font_sizes(soup)
            
            # Check for mobile-specific elements
            mobile_elements = self._check_mobile_elements(soup)
            
            # Check for responsive images
            responsive_images = self._check_responsive_images(soup)
            
            # Check for media queries in style tags
            responsive_css = self._check_responsive_css(soup)
            
            # Generate recommendations
            recommendations = []
            
            if not viewport['has_viewport']:
                recommendations.append("Добавьте мета-тег viewport для правильного отображения на мобильных устройствах.")
                
            if not viewport.get('is_responsive', False):
                recommendations.append("Настройте viewport для адаптивного дизайна: width=device-width, initial-scale=1.")
                
            if not touch_targets['adequate_sizing']:
                recommendations.append("Увеличьте размер элементов интерфейса для удобного нажатия на мобильных устройствах.")
                
            if font_sizes['potential_issues']:
                recommendations.append("Проверьте размеры шрифтов для лучшей читаемости на мобильных устройствах.")
                
            if not responsive_images['has_responsive_images'] and responsive_images['total_images'] > 0:
                recommendations.append("Используйте адаптивные изображения с атрибутами srcset или picture для мобильных устройств.")
                
            if not responsive_css['has_media_queries']:
                recommendations.append("Добавьте медиа-запросы (media queries) для адаптации дизайна под разные размеры экранов.")
            
            # Calculate overall mobile-friendliness score
            score_components = [
                viewport.get('is_responsive', False) * 30,  # 30% weight
                touch_targets.get('adequate_sizing', False) * 20,  # 20% weight
                (not font_sizes.get('potential_issues', True)) * 15,  # 15% weight
                responsive_images.get('has_responsive_images', False) * 15,  # 15% weight
                responsive_css.get('has_media_queries', False) * 20  # 20% weight
            ]
            mobile_score = sum(score_components)
            
            return {
                "viewport": viewport,
                "touch_targets": touch_targets,
                "font_sizes": font_sizes,
                "mobile_elements": mobile_elements,
                "responsive_images": responsive_images,
                "responsive_css": responsive_css,
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
                "content": None,
                "is_responsive": False
            }
            
        viewport_content = viewport_tag.get('content', '')
        
        # Check for responsive settings
        has_width = 'width=device-width' in viewport_content
        has_initial_scale = 'initial-scale=1' in viewport_content
        has_user_scalable_no = 'user-scalable=no' in viewport_content or 'maximum-scale=1' in viewport_content
        
        return {
            "has_viewport": True,
            "content": viewport_content,
            "has_width": has_width,
            "has_initial_scale": has_initial_scale,
            "prevents_zooming": has_user_scalable_no,
            "is_responsive": has_width and has_initial_scale,
            "issues": [] if (has_width and has_initial_scale) else ["Неоптимальные настройки viewport"]
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
                'width:' in style and re.search(r'width:\s*(\d+)px', style) and int(re.search(r'width:\s*(\d+)px', style).group(1)) < 40 or
                'height:' in style and re.search(r'height:\s*(\d+)px', style) and int(re.search(r'height:\s*(\d+)px', style).group(1)) < 40
            ):
                small_elements += 1
        
        total_targets = len(links) + len(buttons) + len(inputs)
        
        return {
            "total_touch_targets": total_targets,
            "potential_small_targets": small_elements,
            "adequate_sizing": small_elements == 0 or (small_elements / max(1, total_targets) < 0.1)
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
        elements_with_small_class = sum(1 for cls in small_text_classes 
                                      for element in soup.find_all(class_=re.compile(cls)))
        
        return {
            "small_inline_fonts": small_fonts,
            "small_class_elements": elements_with_small_class,
            "potential_issues": small_fonts > 0 or elements_with_small_class > 0
        }
    
    def _check_mobile_elements(self, soup):
        """Check for mobile-specific elements and features"""
        # Check for meta theme-color
        theme_color = soup.find('meta', attrs={'name': 'theme-color'})
        
        # Check for apple touch icons
        apple_icon = soup.find('link', rel='apple-touch-icon')
        
        # Check for app manifest
        manifest = soup.find('link', rel='manifest')
        
        # Check for accelerated mobile pages (AMP) link
        amp_html = soup.find('link', rel='amphtml')
        
        return {
            "has_theme_color": bool(theme_color),
            "has_apple_icon": bool(apple_icon),
            "has_web_manifest": bool(manifest),
            "has_amp_version": bool(amp_html),
            "mobile_optimization_score": sum([
                bool(theme_color), 
                bool(apple_icon), 
                bool(manifest), 
                bool(amp_html)
            ]) * 25  # Score from 0-100
        }
        
    def _check_responsive_images(self, soup):
        """Check for responsive image techniques"""
        # Find all images
        images = soup.find_all('img')
        
        # Count images with responsive features
        responsive_count = 0
        for img in images:
            if (
                img.has_attr('srcset') or  # Responsive image srcset
                img.has_attr('sizes') or   # Sizes attribute
                img.parent.name == 'picture'  # Picture element
            ):
                responsive_count += 1
                
        # Check if any CSS background images use media queries (simplified check)
        style_tags = soup.find_all('style')
        has_responsive_bg = any('@media' in style.string and 'background' in style.string 
                              for style in style_tags if style.string)
                
        return {
            "total_images": len(images),
            "responsive_images": responsive_count,
            "has_responsive_images": responsive_count > 0 or has_responsive_bg,
            "responsive_percentage": round((responsive_count / max(1, len(images))) * 100, 1)
        }
        
    def _check_responsive_css(self, soup):
        """Check for responsive CSS media queries"""
        # Find all style tags and check for media queries
        style_tags = soup.find_all('style')
        
        media_queries = []
        for style in style_tags:
            if style.string:
                # Extract media queries
                queries = re.findall(r'@media\s+([^{]+)', style.string)
                media_queries.extend(queries)
                
        # Check for responsive frameworks
        responsive_frameworks = {
            'bootstrap': soup.find_all(class_=re.compile(r'col-\w+-\d+')),
            'foundation': soup.find_all(class_=re.compile(r'small-\d+|medium-\d+|large-\d+')),
            'tailwind': soup.find_all(class_=re.compile(r'sm:|md:|lg:|xl:|2xl:'))
        }
        
        has_framework = any(len(elements) > 0 for elements in responsive_frameworks.values())
        
        return {
            "has_media_queries": len(media_queries) > 0 or has_framework,
            "media_queries_count": len(media_queries),
            "has_responsive_framework": has_framework,
            "detected_frameworks": [name for name, elements in responsive_frameworks.items() 
                                   if len(elements) > 0]
        }