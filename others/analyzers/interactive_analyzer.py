from typing import Dict, Any
from playwright.async_api import Page
from ...utils.logger import setup_logger
from ..models.analysis_models import InteractiveAnalysis

class InteractiveAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def analyze_interactive_elements(self, page: Page) -> InteractiveAnalysis:
        """Analyze interactive elements for productivity"""
        self.logger.debug("Analyzing interactive elements")
        
        forms_analysis = await self._analyze_forms(page)
        buttons_analysis = await self._analyze_buttons(page)
        
        return InteractiveAnalysis(
            forms=forms_analysis,
            buttons=buttons_analysis
        )
    
    async def _analyze_forms(self, page: Page) -> Dict[str, Any]:
        """Analyze form accessibility and labeling"""
        return await page.evaluate('''() => {
            const forms = document.querySelectorAll('form');
            let form_data = {
                total_forms: forms.length,
                forms_with_labels: 0,
                forms_with_aria: 0,
                average_fields_per_form: 0
            };
            
            let total_fields = 0;
            let forms_with_proper_labels = 0;
            let forms_with_aria = 0;
            
            forms.forEach(form => {
                const fields = form.querySelectorAll('input, select, textarea');
                total_fields += fields.length;
                
                let hasAllLabels = true;
                let hasAria = false;
                
                fields.forEach(field => {
                    // Check for associated label
                    const id = field.id;
                    const label = id ? document.querySelector(`label[for="${id}"]`) : null;
                    const parentLabel = field.closest('label');
                    
                    if (!label && !parentLabel && !field.getAttribute('aria-label') && 
                        !field.getAttribute('aria-labelledby')) {
                        hasAllLabels = false;
                    }
                    
                    if (field.getAttribute('aria-required') || field.getAttribute('aria-invalid') ||
                        field.getAttribute('aria-describedby')) {
                        hasAria = true;
                    }
                });
                
                if (hasAllLabels) forms_with_proper_labels++;
                if (hasAria) forms_with_aria++;
            });
            
            form_data.forms_with_labels = forms_with_proper_labels;
            form_data.forms_with_aria = forms_with_aria;
            form_data.average_fields_per_form = forms.length > 0 ? total_fields / forms.length : 0;
            
            return form_data;
        }''')
    
    async def _analyze_buttons(self, page: Page) -> Dict[str, Any]:
        """Analyze button accessibility"""
        return await page.evaluate('''() => {
            const buttons = document.querySelectorAll('button, [role="button"]');
            let accessible_buttons = 0;
            let keyboard_accessible = 0;
            
            buttons.forEach(button => {
                // Check if button has accessible name
                const name = button.textContent?.trim() || 
                            button.getAttribute('aria-label') ||
                            button.getAttribute('title');
                
                if (name && name.length > 0) {
                    accessible_buttons++;
                }
                
                // Check keyboard accessibility
                if (button.tabIndex >= 0 && !button.disabled) {
                    keyboard_accessible++;
                }
            });
            
            return {
                total_buttons: buttons.length,
                accessible_buttons: accessible_buttons,
                keyboard_accessible: keyboard_accessible,
                accessibility_score: buttons.length > 0 ? (accessible_buttons / buttons.length) * 100 : 0
            };
        }''')