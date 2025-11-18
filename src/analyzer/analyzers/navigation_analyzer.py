from typing import Dict, Any
from playwright.async_api import Page
from ...utils.logger import setup_logger
from ..models.analysis_models import NavigationAnalysis

class NavigationAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def analyze_navigation_flow(self, page: Page) -> NavigationAnalysis:
        """Analyze navigation flow and keyboard accessibility"""
        self.logger.debug("Analyzing navigation flow")
        
        # Analyze skip links
        skip_links = await page.query_selector_all('a[href^="#"]')
        skip_links_present = len(skip_links) > 0
        
        # Analyze landmark regions
        landmarks = await self._analyze_landmark_regions(page)
        
        # Analyze focus management
        focus_management = await self._analyze_focus_management(page)
        
        return NavigationAnalysis(
            skip_links_present=skip_links_present,
            landmark_regions=landmarks,
            focus_management=focus_management
        )
    
    async def _analyze_landmark_regions(self, page: Page) -> Dict[str, int]:
        """Analyze landmark regions on the page"""
        return await page.evaluate('''() => {
            const landmarks = {};
            ['main', 'nav', 'header', 'footer', 'aside', 'section', 'article'].forEach(tag => {
                landmarks[tag] = document.getElementsByTagName(tag).length;
            });
            return landmarks;
        }''')
    
    async def _analyze_focus_management(self, page: Page) -> Dict[str, Any]:
        """Analyze focus indicators and management"""
        return await page.evaluate('''() => {
            const elements = document.querySelectorAll('*');
            let focusable = 0;
            let hasFocusIndicator = 0;
            
            elements.forEach(el => {
                if (el.tabIndex >= 0 || el.tagName === 'A' || el.tagName === 'BUTTON' || 
                    el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') {
                    focusable++;
                    const style = window.getComputedStyle(el);
                    if (style.outline !== 'none' || style.outlineStyle !== 'none' || 
                        style.boxShadow !== 'none' || el.getAttribute('data-custom-focus')) {
                        hasFocusIndicator++;
                    }
                }
            });
            
            return {
                focusable_elements: focusable,
                elements_with_focus_indicator: hasFocusIndicator,
                focus_indicator_coverage: focusable > 0 ? (hasFocusIndicator / focusable) * 100 : 0
            };
        }''')