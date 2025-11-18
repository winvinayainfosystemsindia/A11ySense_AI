# src/analyzer/extended_audits/base_audit.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from ...utils.logger import setup_logger

class BaseAudit(ABC):
    def __init__(self, driver: WebDriver, config: Dict[str, Any]):
        self.driver = driver
        self.config = config
        self.logger = setup_logger(self.__class__.__name__)
    
    @abstractmethod
    async def run_audit(self) -> List[Any]:
        """Run the specific audit and return defects"""
        pass
    
    def _safe_execute(self, func: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
        """Safely execute a function with retry logic for stale elements"""
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except StaleElementReferenceException as e:
                last_exception = e
                if attempt == max_retries:
                    break
                self.logger.debug(f"Stale element encountered, retrying... (attempt {attempt + 1})")
                continue
            except Exception as e:
                last_exception = e
                break
        
        if last_exception:
            self.logger.debug(f"Failed after {max_retries} retries: {last_exception}")
        return None
    
    def _get_element_description(self, element: WebElement) -> str:
        """Get descriptive text for an element with stale element protection"""
        try:
            description = self._safe_execute(self._get_element_description_unsafe, element)
            return description or "Unknown element"
        except Exception as e:
            self.logger.debug(f"Failed to get element description: {e}")
            return "Unknown element"
    
    def _get_element_description_unsafe(self, element: WebElement) -> str:
        """Unsafe version of get_element_description (called by safe_execute)"""
        # Try to get text content
        text = element.text.strip()
        if text:
            return text[:100]  # Limit length
        
        # Try to get aria-label
        aria_label = element.get_attribute('aria-label')
        if aria_label:
            return aria_label[:100]
        
        # Try to get alt text
        alt_text = element.get_attribute('alt')
        if alt_text:
            return alt_text[:100]
        
        # Try to get placeholder for inputs
        placeholder = element.get_attribute('placeholder')
        if placeholder:
            return f"{element.tag_name}[placeholder='{placeholder[:50]}']"
        
        # Fallback to tag name and basic attributes
        tag_name = element.tag_name
        element_id = element.get_attribute('id')
        element_class = element.get_attribute('class')
        
        description = tag_name
        if element_id:
            description += f"#{element_id}"
        if element_class:
            description += f".{element_class.split()[0]}"
        
        return description
    
    def _get_element_selector(self, element: WebElement) -> str:
        """Generate a CSS selector for the element with stale element protection"""
        try:
            selector = self._safe_execute(self._get_element_selector_unsafe, element)
            return selector or "unknown"
        except Exception as e:
            self.logger.debug(f"Failed to get element selector: {e}")
            return "unknown"
    
    def _get_element_selector_unsafe(self, element: WebElement) -> str:
        """Unsafe version of get_element_selector (called by safe_execute)"""
        tag_name = element.tag_name
        
        # Try ID first
        element_id = element.get_attribute('id')
        if element_id:
            return f"{tag_name}#{element_id}"
        
        # Try classes
        element_class = element.get_attribute('class')
        if element_class:
            classes = ' '.join(element_class.split())
            return f"{tag_name}.{classes.replace(' ', '.')}"
        
        # Try name attribute for form elements
        element_name = element.get_attribute('name')
        if element_name:
            return f"{tag_name}[name='{element_name}']"
        
        # Try type attribute
        element_type = element.get_attribute('type')
        if element_type:
            return f"{tag_name}[type='{element_type}']"
        
        # Fallback to basic selector
        return tag_name
    
    def _find_elements_safe(self, selector: str) -> List[WebElement]:
        """Safely find elements with error handling"""
        try:
            return self.driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception as e:
            self.logger.warning(f"Failed to find elements with selector {selector}: {e}")
            return []
    
    def _refresh_element(self, element: WebElement) -> Optional[WebElement]:
        """Refresh an element reference using its selector"""
        try:
            selector = self._get_element_selector(element)
            refreshed_elements = self._find_elements_safe(selector)
            return refreshed_elements[0] if refreshed_elements else None
        except Exception as e:
            self.logger.debug(f"Failed to refresh element: {e}")
            return None
    
    def _execute_js_on_element(self, element: WebElement, script: str) -> Any:
        """Execute JavaScript on element with stale element protection"""
        try:
            selector = self._get_element_selector(element)
            full_script = f"""
            var element = document.querySelector('{selector}');
            if (element) {{
                {script}
            }}
            """
            return self.driver.execute_script(full_script)
        except Exception as e:
            self.logger.debug(f"Failed to execute JS on element: {e}")
            return None
    
    def _get_unique_elements(self, elements: List[WebElement]) -> List[WebElement]:
        """Get unique elements using selector-based deduplication"""
        unique_elements = []
        seen_selectors = set()
        
        for element in elements:
            try:
                selector = self._get_element_selector(element)
                if selector and selector not in seen_selectors:
                    seen_selectors.add(selector)
                    unique_elements.append(element)
            except StaleElementReferenceException:
                continue  # Skip stale elements during deduplication
            except Exception as e:
                self.logger.debug(f"Error getting selector for element: {e}")
                continue
        
        return unique_elements