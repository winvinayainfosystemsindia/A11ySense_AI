from typing import Dict, Any
from playwright.async_api import Page
from ...utils.logger import setup_logger
from ..models.analysis_models import PerformanceAnalysis

class PerformanceAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def analyze_performance_impact(self, page: Page) -> PerformanceAnalysis:
        """Analyze performance impact of accessibility features"""
        self.logger.debug("Analyzing performance impact")
        
        resource_impact = await self._analyze_resource_impact(page)
        dom_complexity = await self._analyze_dom_complexity(page)
        
        return PerformanceAnalysis(
            resource_impact=resource_impact,
            dom_complexity=dom_complexity
        )
    
    async def _analyze_resource_impact(self, page: Page) -> Dict[str, Any]:
        """Analyze resource loading impact of accessibility features"""
        return await page.evaluate('''() => {
            const resources = performance.getEntriesByType('resource');
            const accessibilityResources = resources.filter(resource => 
                resource.name.includes('aria') || 
                resource.name.includes('accessibility') ||
                resource.name.includes('a11y')
            );
            
            return {
                total_resources: resources.length,
                accessibility_resources: accessibilityResources.length,
                total_resource_size: resources.reduce((acc, resource) => acc + (resource.transferSize || 0), 0),
                accessibility_resource_size: accessibilityResources.reduce((acc, resource) => acc + (resource.transferSize || 0), 0)
            };
        }''')
    
    async def _analyze_dom_complexity(self, page: Page) -> Dict[str, Any]:
        """Analyze DOM complexity and its impact on performance"""
        return await page.evaluate('''() => {
            const allElements = document.querySelectorAll('*').length;
            const interactiveElements = document.querySelectorAll(
                'a, button, input, select, textarea, [role="button"], [role="link"]'
            ).length;
            
            return {
                total_elements: allElements,
                interactive_elements: interactiveElements,
                complexity_ratio: allElements > 0 ? (interactiveElements / allElements) * 100 : 0
            };
        }''')