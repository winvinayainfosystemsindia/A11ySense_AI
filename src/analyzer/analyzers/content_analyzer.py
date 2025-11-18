from typing import Dict, Any
from playwright.async_api import Page
from ...utils.logger import setup_logger
from ..models.analysis_models import ContentAnalysis

class ContentAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def analyze_content_structure(self, page: Page) -> ContentAnalysis:
        """Analyze content structure for readability and navigation"""
        self.logger.debug("Analyzing content structure")
        
        heading_structure = await self._analyze_heading_hierarchy(page)
        content_density = await self._analyze_content_density(page)
        
        return ContentAnalysis(
            heading_structure=heading_structure,
            content_density=content_density
        )
    
    async def _analyze_heading_hierarchy(self, page: Page) -> Dict[str, Any]:
        """Analyze heading hierarchy and structure"""
        return await page.evaluate('''() => {
            const headings = {};
            for (let i = 1; i <= 6; i++) {
                headings[`h${i}`] = document.querySelectorAll(`h${i}`).length;
            }
            
            // Check for heading hierarchy issues
            let hierarchy_issues = 0;
            const allHeadings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            
            let previousLevel = 0;
            allHeadings.forEach(heading => {
                const currentLevel = parseInt(heading.tagName.substring(1));
                if (currentLevel > previousLevel + 1 && previousLevel > 0) {
                    hierarchy_issues++;
                }
                previousLevel = currentLevel;
            });
            
            return {
                heading_counts: headings,
                hierarchy_issues: hierarchy_issues,
                has_h1: headings.h1 > 0
            };
        }''')
    
    async def _analyze_content_density(self, page: Page) -> Dict[str, Any]:
        """Analyze content density and readability"""
        return await page.evaluate('''() => {
            const bodyText = document.body.innerText || '';
            const words = bodyText.trim().split(/\\s+/).filter(word => word.length > 0);
            const paragraphs = document.querySelectorAll('p').length;
            const lists = document.querySelectorAll('ul, ol').length;
            
            return {
                word_count: words.length,
                paragraph_count: paragraphs,
                list_count: lists,
                average_words_per_paragraph: paragraphs > 0 ? words.length / paragraphs : 0,
                content_density_score: Math.min(100, (words.length / 1000) * 100) // Score out of 100
            };
        }''')