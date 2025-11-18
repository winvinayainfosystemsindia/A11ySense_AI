from typing import Dict, Any
from playwright.async_api import Page
from ...utils.logger import setup_logger
from ..models.analysis_models import CognitiveAnalysis

class CognitiveAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def analyze_cognitive_load(self, page: Page) -> CognitiveAnalysis:
        """Analyze cognitive load for users with cognitive disabilities"""
        self.logger.debug("Analyzing cognitive load")
        
        language_complexity = await self._analyze_language_complexity(page)
        visual_complexity = await self._analyze_visual_complexity(page)
        
        return CognitiveAnalysis(
            language_complexity=language_complexity,
            visual_complexity=visual_complexity
        )
    
    async def _analyze_language_complexity(self, page: Page) -> Dict[str, Any]:
        """Analyze language complexity and readability"""
        return await page.evaluate('''() => {
            const bodyText = document.body.innerText || '';
            const sentences = bodyText.split(/[.!?]+/).filter(s => s.trim().length > 0);
            const words = bodyText.trim().split(/\\s+/).filter(word => word.length > 0);
            
            let complexWords = 0;
            words.forEach(word => {
                // Simple heuristic for complex words (3+ syllables or 8+ characters)
                if (word.length >= 8 || (word.match(/[aeiou]{2,}/gi) || []).length >= 2) {
                    complexWords++;
                }
            });
            
            return {
                total_sentences: sentences.length,
                total_words: words.length,
                complex_words: complexWords,
                average_sentence_length: sentences.length > 0 ? words.length / sentences.length : 0,
                complexity_score: words.length > 0 ? (complexWords / words.length) * 100 : 0
            };
        }''')
    
    async def _analyze_visual_complexity(self, page: Page) -> Dict[str, Any]:
        """Analyze visual complexity of the page"""
        return await page.evaluate('''() => {
            const sections = document.querySelectorAll('section, article, [role="main"]').length;
            const containers = document.querySelectorAll('.container, .wrapper, .main, .content').length;
            const modals = document.querySelectorAll('[role="dialog"], .modal, .popup').length;
            
            return {
                content_sections: sections,
                layout_containers: containers,
                modal_windows: modals,
                total_structural_elements: sections + containers + modals
            };
        }''')