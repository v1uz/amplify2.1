"""
Technical SEO Analyzer Module
Analyzes technical SEO aspects of a webpage.
"""

import re
import logging
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class TechnicalSEOAnalyzer:
    """Analyzes technical SEO aspects of a webpage"""
    
    def __init__(self):
        self.name = "technical_analysis"
    
    async def analyze(self, url, raw_data, api_data=None):
        """
        Analyze technical SEO factors
        
        Args:
            url (str): The URL being analyzed
            raw_data (dict): Raw data including the parsed BeautifulSoup object
            api_data (dict, optional): Data from external APIs
            
        Returns:
            dict: Technical SEO analysis results
        """
        try:
            soup = raw_data.get('soup', BeautifulSoup("", 'html.parser'))
            
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
            
            # Check page loading speed elements
            loading = self._check_loading_optimization(soup)
            
            # Check SSL/security indicators
            security = self._check_security(url)
            
            # Analyze internal linking structure
            internal_links = self._analyze_internal_links(soup, url)
            
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
                
            if not loading['has_resource_hints']:
                recommendations.append("Используйте подсказки ресурсов (preload, prefetch) для ускорения загрузки важных элементов.")
                
            if not security['is_https']:
                recommendations.append("Переведите сайт на HTTPS для повышения безопасности и улучшения SEO.")
                
            if internal_links['orphaned_headings']:
                recommendations.append("Некоторые заголовки не имеют якорных ссылок. Добавьте внутреннюю перелинковку.")
            
            # Calculate overall technical score
            score_components = [
                canonical.get('has_canonical', False) * 15,  # 15% weight
                robots.get('has_robots_tag', False) * 10,    # 10% weight
                (not url_analysis.get('issues', [])) * 15,   # 15% weight
                schema.get('has_schema', False) * 15,        # 15% weight
                loading.get('optimization_score', 0) / 100 * 20,  # 20% weight
                security.get('is_https', False) * 15,        # 15% weight
                internal_links.get('link_score', 0) / 100 * 10  # 10% weight
            ]
            technical_score = sum(score_components)
            
            return {
                "canonical": canonical,
                "robots": robots,
                "url_analysis": url_analysis,
                "hreflang": hreflang,
                "schema_markup": schema,
                "sitemap": sitemap,
                "loading_optimization": loading,
                "security": security,
                "internal_links": internal_links,
                "technical_score": round(technical_score),
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
            
        # Check for dynamic parameters
        if parsed_url.query:
            issues.append("URL содержит параметры запроса")
            
        # Check for trailing slash consistency
        if path != '/' and path.endswith('/'):
            # This is a style preference, not necessarily an issue
            pass
            
        return {
            "path": path,
            "query_parameters": parsed_url.query,
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
        
        # Check for common implementation issues
        issues = []
        
        # Check for self-referencing hreflang
        page_lang = soup.html.get('lang', '')
        if page_lang and not any(lang == page_lang for lang in languages):
            issues.append("Отсутствует самореферентная hreflang-ссылка")
            
        return {
            "has_hreflang": True,
            "languages": languages,
            "count": len(languages),
            "issues": issues
        }
    
    def _check_schema_markup(self, soup):
        """Check for schema.org structured data"""
        # Look for JSON-LD
        json_ld = soup.find_all('script', type='application/ld+json')
        
        # Look for microdata
        microdata = soup.find_all(attrs={"itemtype": re.compile(r'schema.org')})
        
        # Try to determine schema types (simplified)
        schema_types = []
        
        for script in json_ld:
            if script.string:
                # Extract schema type from JSON-LD
                type_match = re.search(r'"@type"\s*:\s*"([^"]+)"', script.string)
                if type_match:
                    schema_types.append(type_match.group(1))
        
        for element in microdata:
            itemtype = element.get('itemtype', '')
            if itemtype and 'schema.org/' in itemtype:
                schema_type = itemtype.split('schema.org/')[1].strip()
                if schema_type:
                    schema_types.append(schema_type)
        
        return {
            "has_schema": bool(json_ld or microdata),
            "json_ld_count": len(json_ld),
            "microdata_count": len(microdata),
            "detected_types": schema_types
        }
    
    def _check_sitemap_reference(self, soup):
        """Check for XML sitemap reference"""
        # This would typically be in robots.txt, but sometimes in HTML as well
        sitemap_link = soup.find('a', href=re.compile(r'sitemap\.xml'))
        
        return {
            "has_sitemap_link": bool(sitemap_link)
        }
        
    def _check_loading_optimization(self, soup):
        """Check for page loading optimization techniques"""
        # Check for resource hints
        preload = soup.find_all('link', rel='preload')
        prefetch = soup.find_all('link', rel='prefetch')
        dns_prefetch = soup.find_all('link', rel='dns-prefetch')
        
        # Check for async/defer on scripts
        scripts = soup.find_all('script', src=True)
        async_scripts = [s for s in scripts if s.has_attr('async')]
        defer_scripts = [s for s in scripts if s.has_attr('defer')]
        
        # Check for lazy loading
        lazy_loading = soup.find_all(attrs={'loading': 'lazy'})
        
        # Calculate optimization score
        has_resource_hints = bool(preload or prefetch or dns_prefetch)
        optimized_scripts = len(async_scripts) + len(defer_scripts)
        script_score = min(100, (optimized_scripts / max(1, len(scripts))) * 100)
        
        optimization_score = (
            (has_resource_hints * 40) +  # 40% weight
            (script_score * 0.4) +       # 40% weight
            (bool(lazy_loading) * 20)    # 20% weight
        )
        
        return {
            "has_resource_hints": has_resource_hints,
            "preload_count": len(preload),
            "prefetch_count": len(prefetch),
            "dns_prefetch_count": len(dns_prefetch),
            "script_optimization": {
                "total_scripts": len(scripts),
                "async_scripts": len(async_scripts),
                "defer_scripts": len(defer_scripts),
                "script_score": round(script_score)
            },
            "has_lazy_loading": bool(lazy_loading),
            "lazy_loading_count": len(lazy_loading),
            "optimization_score": round(optimization_score)
        }
        
    def _check_security(self, url):
        """Check for security indicators"""
        parsed_url = urlparse(url)
        
        # Check HTTPS
        is_https = parsed_url.scheme == 'https'
        
        return {
            "is_https": is_https,
            "protocol": parsed_url.scheme
        }
        
    def _analyze_internal_links(self, soup, url):
        """Analyze internal linking structure"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Get all links
        links = soup.find_all('a', href=True)
        
        # Separate internal and external links
        internal_links = []
        external_links = []
        
        for link in links:
            href = link['href']
            if href.startswith('#') or href.startswith('javascript:'):
                continue
                
            # Normalize URL
            if href.startswith('/'):
                full_url = f"{parsed_url.scheme}://{domain}{href}"
                internal_links.append(full_url)
            elif href.startswith(('http://', 'https://')):
                link_domain = urlparse(href).netloc
                if link_domain == domain:
                    internal_links.append(href)
                else:
                    external_links.append(href)
            else:
                # Relative URL
                internal_links.append(urljoin(url, href))
        
        # Check headings that aren't linked to
        headings = soup.find_all(['h2', 'h3'])
        linked_headings = []
        
        for link in links:
            for heading in headings:
                if heading.get_text(strip=True) in link.get_text(strip=True):
                    linked_headings.append(heading)
                    
        orphaned_headings = [h for h in headings if h not in linked_headings]
        
        # Calculate link score
        unique_internal = len(set(internal_links))
        has_sufficient_internal = unique_internal >= 3
        has_external = len(external_links) > 0
        
        link_score = (
            (has_sufficient_internal * 60) +  # 60% weight
            (has_external * 20) +             # 20% weight
            ((len(orphaned_headings) == 0) * 20)  # 20% weight
        )
        
        return {
            "internal_links": {
                "count": len(internal_links),
                "unique_count": unique_internal
            },
            "external_links": {
                "count": len(external_links)
            },
            "orphaned_headings": len(orphaned_headings),
            "has_sufficient_internal": has_sufficient_internal,
            "link_score": link_score
        }