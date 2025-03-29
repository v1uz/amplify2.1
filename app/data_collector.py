"""
Website Data Collector Module
Collects and processes comprehensive website data.
"""

import logging
import asyncio
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class WebsiteDataCollector:
    """Collects comprehensive website data for analysis"""
    
    async def collect_comprehensive_data(self, url, initial_html=None):
        """
        Collect all available data about a website
        
        Args:
            url (str): The URL to analyze
            initial_html (str, optional): HTML content if already fetched
            
        Returns:
            dict: Comprehensive website data
        """
        try:
            # Parse the initial HTML if provided
            if initial_html:
                soup = BeautifulSoup(initial_html, 'html.parser')
            else:
                # In a real implementation, you might need to fetch the HTML here
                # if it wasn't provided, but in your case it's always provided by
                # the existing analyze_seo function
                logger.warning("No initial HTML provided to data collector")
                soup = BeautifulSoup("", 'html.parser')
            
            # Parse the URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Create the base data object
            data = {
                'url': url,
                'domain': domain,
                'soup': soup,
                'head_data': self._extract_head_data(soup),
                'page_structure': self._analyze_page_structure(soup),
                'main_content': self._extract_main_content(soup),
                'links': self._extract_links(soup, url),
                'images': self._extract_images(soup),
                'mobile_snapshot': self._extract_mobile_data(soup)
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error collecting website data: {str(e)}")
            # Return minimal data with error
            return {
                'url': url,
                'soup': BeautifulSoup(initial_html, 'html.parser') if initial_html else BeautifulSoup("", 'html.parser'),
                'error': str(e)
            }
    
    def _extract_head_data(self, soup):
        """Extract data from the <head> section"""
        head = soup.head
        
        if not head:
            return {'error': 'No head section found'}
            
        # Basic metadata
        title = head.title.string if head.title else None
        
        # Meta tags
        meta_tags = {}
        for meta in head.find_all('meta'):
            if meta.get('name'):
                meta_tags[meta['name']] = meta.get('content')
            elif meta.get('property'):
                meta_tags[meta['property']] = meta.get('content')
        
        # Link tags
        link_tags = {}
        for link in head.find_all('link'):
            if link.get('rel'):
                rel = ' '.join(link['rel']) if isinstance(link['rel'], list) else link['rel']
                link_tags[rel] = link.get('href')
        
        # Scripts in head
        scripts = []
        for script in head.find_all('script', src=True):
            scripts.append(script['src'])
            
        return {
            'title': title,
            'meta_tags': meta_tags,
            'link_tags': link_tags,
            'scripts': scripts
        }
    
    def _analyze_page_structure(self, soup):
        """Analyze the structure of the page"""
        # Count various elements
        elements = {}
        for tag_name in ['div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'form', 'input', 'button', 'img', 'a']:
            elements[tag_name] = len(soup.find_all(tag_name))
            
        # Identify main containers
        main_containers = []
        for container in soup.find_all(['main', 'div', 'section'], class_=True):
            if container.get('id') in ['main', 'content', 'main-content'] or any(x in container.get('class', []) for x in ['main', 'content', 'container']):
                main_containers.append({
                    'tag': container.name,
                    'id': container.get('id'),
                    'class': container.get('class')
                })
                
        return {
            'element_counts': elements,
            'main_containers': main_containers,
            'has_header': bool(soup.find('header')),
            'has_footer': bool(soup.find('footer')),
            'has_nav': bool(soup.find('nav')),
            'has_sidebar': bool(soup.find(['aside', 'div'], class_=lambda c: c and 'sidebar' in c)),
            'has_article': bool(soup.find('article'))
        }
    
    def _extract_main_content(self, soup):
        """Extract the main content area of the page"""
        # Try to find main content by common tags
        content_candidates = [
            soup.find('main'),
            soup.find('article'),
            soup.find(id='content'),
            soup.find(id='main-content'),
            soup.find(class_='content'),
            soup.find(class_='main-content')
        ]
        
        # Use the first valid candidate
        main_content = None
        for candidate in content_candidates:
            if candidate:
                main_content = candidate
                break
                
        # Fallback to body if no content containers found
        if not main_content:
            main_content = soup.body
            
        # Analyze if main content exists
        if main_content:
            # Extract headings
            headings = []
            for h_level in range(1, 7):
                for heading in main_content.find_all(f'h{h_level}'):
                    headings.append({
                        'level': h_level,
                        'text': heading.get_text(strip=True)
                    })
                    
            # Extract paragraphs
            paragraphs = [p.get_text(strip=True) for p in main_content.find_all('p')]
            
            # Extract lists
            lists = []
            for list_tag in main_content.find_all(['ul', 'ol']):
                items = [li.get_text(strip=True) for li in list_tag.find_all('li')]
                lists.append({
                    'type': list_tag.name,
                    'items': items
                })
                
            return {
                'text': main_content.get_text(strip=True),
                'word_count': len(main_content.get_text(strip=True).split()),
                'headings': headings,
                'paragraphs': paragraphs,
                'lists': lists
            }
        else:
            return {
                'error': 'No main content area identified'
            }
    
    def _extract_links(self, soup, base_url):
        """Extract and categorize all links on the page"""
        links = soup.find_all('a', href=True)
        
        # Parse the base URL
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc
        
        # Categorize links
        internal_links = []
        external_links = []
        social_links = []
        resource_links = []
        
        for link in links:
            href = link['href']
            
            # Skip fragment and javascript links
            if href.startswith('#') or href.startswith('javascript:'):
                continue
                
            # Normalize the URL
            if href.startswith('/'):
                full_url = f"{parsed_base.scheme}://{base_domain}{href}"
            elif not href.startswith(('http://', 'https://')):
                full_url = urljoin(base_url, href)
            else:
                full_url = href
                
            # Parse the URL
            parsed_url = urlparse(full_url)
            
            # Create link data
            link_data = {
                'url': full_url,
                'text': link.get_text(strip=True),
                'domain': parsed_url.netloc
            }
            
            # Categorize the link
            if parsed_url.netloc == base_domain:
                internal_links.append(link_data)
            elif any(social in parsed_url.netloc for social in ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'pinterest.com']):
                social_links.append(link_data)
            elif parsed_url.path.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar')):
                resource_links.append(link_data)
            else:
                external_links.append(link_data)
                
        return {
            'internal': internal_links,
            'external': external_links,
            'social': social_links,
            'resources': resource_links,
            'total_count': len(internal_links) + len(external_links) + len(social_links) + len(resource_links)
        }
    
    def _extract_images(self, soup):
        """Extract and analyze images on the page"""
        images = soup.find_all('img')
        
        image_data = []
        for img in images:
            image_data.append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', ''),
                'has_alt': bool(img.get('alt')),
                'has_dimensions': bool(img.get('width') and img.get('height')),
                'is_svg': img.get('src', '').endswith('.svg') or img.name == 'svg',
                'is_responsive': bool(img.get('srcset') or img.parent.name == 'picture')
            })
            
        return {
            'count': len(images),
            'with_alt': sum(1 for img in image_data if img['has_alt']),
            'without_alt': sum(1 for img in image_data if not img['has_alt']),
            'responsive': sum(1 for img in image_data if img['is_responsive']),
            'svg': sum}