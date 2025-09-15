"""Document link extraction logic."""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

from browser_use import BrowserSession, BrowserProfile
from browser_use.browser.events import NavigateToUrlEvent

from config import (
    DOCUMENT_FILE_TYPES, 
    DOCUMENT_KEYWORDS, 
    DOCUMENT_CATEGORIES,
    logging
)

logger = logging.getLogger(__name__)


class DocumentLinkExtractor:
    """Handles document link extraction from websites."""
    
    def __init__(self):
        self.browser_session: Optional[BrowserSession] = None
        
    async def initialize_browser(self) -> None:
        """Initialize browser session if not already active."""
        if self.browser_session:
            return
            
        # Create browser profile optimized for link extraction
        profile = BrowserProfile(
            headless=True,  # Run headless for server environment
            wait_between_actions=0.3,  # Faster operation
            keep_alive=True,
            disable_security=True  # Needed for some sites
        )
        
        # Initialize browser session
        self.browser_session = BrowserSession(browser_profile=profile)
        await self.browser_session.start()
        
        logger.info("Browser session initialized for document link extraction")
    
    async def cleanup(self) -> None:
        """Clean up browser session."""
        if self.browser_session:
            await self.browser_session.stop()
            self.browser_session = None
            logger.info("Browser session cleaned up")
    
    def _determine_file_type(self, href: str) -> str:
        """Determine file type from URL."""
        href_lower = href.lower()
        for ext in DOCUMENT_FILE_TYPES:
            if ext in href_lower:
                return ext.replace('.', '').upper()
        return "unknown"
    
    def _determine_category(self, href: str, text: str) -> str:
        """Determine document category based on content."""
        href_lower = href.lower()
        text_lower = text.lower()
        
        for category, keywords in DOCUMENT_CATEGORIES.items():
            if any(word in href_lower or word in text_lower for word in keywords):
                return category
        return "general"
    
    def _is_document_link(self, href: str, text: str) -> tuple[bool, bool]:
        """Check if a link is a document or download link."""
        href_lower = href.lower()
        text_lower = text.lower()
        
        # Check if this is a download link
        is_download = any(ext in href_lower for ext in DOCUMENT_FILE_TYPES) or 'download' in href_lower
        is_document = any(keyword in href_lower or keyword in text_lower for keyword in DOCUMENT_KEYWORDS)
        
        return is_download, is_document
    
    async def extract_links(self, url: str) -> Dict[str, Any]:
        """Extract document download links from a website."""
        logger.info(f"Extracting document download links from: {url}")
        
        try:
            # Initialize browser if needed
            await self.initialize_browser()
            
            if not self.browser_session:
                return {"error": "Failed to initialize browser session"}
            
            # Navigate to the URL
            event = self.browser_session.event_bus.dispatch(NavigateToUrlEvent(url=url))
            await event
            
            # Wait for page to load
            await asyncio.sleep(1.5)
            
            # Get browser state to analyze the page
            browser_state = await self.browser_session.get_browser_state_summary()
            
            # Extract all links and filter for document content
            doc_links = []
            
            # Look for links in the DOM state
            for index, element in browser_state.dom_state.selector_map.items():
                if element.tag_name.lower() == 'a' and element.attributes.get('href'):
                    href = element.attributes['href']
                    text = element.get_all_children_text(max_depth=1) or ""
                    
                    # Check if this looks like a document download link
                    is_download, is_document = self._is_document_link(href, text)
                    
                    if is_download or is_document:
                        file_type = self._determine_file_type(href)
                        category = self._determine_category(href, text)
                        
                        doc_links.append({
                            'text': text.strip()[:100],  # Limit text length
                            'url': href,
                            'file_type': file_type,
                            'category': category,
                            'is_download': is_download,
                            'source': url.split('//')[1].split('/')[0] if '//' in url else 'unknown'
                        })
            
            # Prepare result
            if doc_links:
                result = {
                    'url': url,
                    'total_links_found': len(doc_links),
                    'document_links': doc_links,
                    'download_links': [link for link in doc_links if link['is_download']],
                    'message': f'Found {len(doc_links)} document download links'
                }
            else:
                # If no document links found, analyze all links for debugging
                all_links = []
                for index, element in browser_state.dom_state.selector_map.items():
                    if element.tag_name.lower() == 'a' and element.attributes.get('href'):
                        href = element.attributes['href']
                        text = element.get_all_children_text(max_depth=1) or "No text"
                        all_links.append({
                            'text': text.strip()[:50],
                            'url': href
                        })
                
                result = {
                    'url': url,
                    'total_links_found': 0,
                    'document_links': [],
                    'download_links': [],
                    'all_links_analyzed': len(all_links),
                    'message': 'No document download links found. The page may not contain downloadable documents.',
                    'sample_links_found': all_links[:5]  # Show first 5 links for debugging
                }
            
            logger.info(f"Link extraction complete. Found {len(doc_links)} total links")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting document links: {e}", exc_info=True)
            return {
                'error': str(e),
                'message': 'Failed to extract document download links. The website may be unavailable or require authentication.',
                'suggestion': 'Try accessing the page manually first to verify it contains downloadable documents.'
            }
