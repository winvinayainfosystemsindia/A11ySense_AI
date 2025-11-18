# src/analyzer/extended_audits/screen_reader_audit.py
import asyncio
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from typing import List
from .base_audit import BaseAudit
from ..models.extended_audit_models import ScreenReaderDefect, SeverityLevel

class ScreenReaderAudit(BaseAudit):
    async def run_audit(self) -> List[ScreenReaderDefect]:
        """Test screen reader compatibility and return defects"""
        defects = []
        
        try:
            # Test interactive elements and important semantic elements
            selectors = [
                "button", "a[href]", "input", "select", "textarea",
                "img", "[role]", "[aria-label]", "[aria-labelledby]",
                "header", "nav", "main", "footer", "section", "article",
                "[aria-expanded]", "[aria-hidden]", "[aria-live]"
            ]
            
            total_elements = 0
            tested_elements = 0
            
            for selector in selectors:
                elements = self._find_elements_safe(selector)
                total_elements += len(elements)
                
                for element in elements:
                    try:
                        element_defects = await self._test_element_screen_reader_support(element)
                        defects.extend(element_defects)
                        tested_elements += 1
                    except StaleElementReferenceException:
                        self.logger.debug(f"Stale element with selector {selector}, skipping...")
                        continue
                    except Exception as e:
                        self.logger.warning(f"Failed to process element with selector {selector}: {e}")
                        continue
            
            self.logger.info(f"Screen reader audit: tested {tested_elements}/{total_elements} elements")
            
        except Exception as e:
            self.logger.error(f"Screen reader support test failed: {e}")
        
        return defects
    
    async def _test_element_screen_reader_support(self, element) -> List[ScreenReaderDefect]:
        """Test screen reader support for a single element and return defects"""
        defects = []
        
        try:
            # Refresh element reference
            selector = self._get_element_selector(element)
            if not selector or selector == "unknown":
                return defects
                
            refreshed_elements = self._find_elements_safe(selector)
            if not refreshed_elements:
                return defects
            
            element = refreshed_elements[0]
            
            tag_name = self._safe_execute(lambda el: el.tag_name.lower(), element)
            description = self._get_element_description(element)
            
            if not tag_name:
                return defects
            
            # Check ARIA attributes with safe execution
            has_aria_label = bool(self._safe_execute(lambda el: el.get_attribute('aria-label'), element))
            has_aria_labelledby = bool(self._safe_execute(lambda el: el.get_attribute('aria-labelledby'), element))
            has_aria_describedby = bool(self._safe_execute(lambda el: el.get_attribute('aria-describedby'), element))
            
            # Check alt text for images
            has_alt_text = False
            if tag_name == 'img':
                has_alt_text = bool(self._safe_execute(lambda el: el.get_attribute('alt'), element))
            
            # Check role
            role = self._safe_execute(lambda el: el.get_attribute('role'), element)
            role_present = bool(role)
            
            # Check state announcements
            state_announced = await self._has_state_announcements(element)
            
            # Check value announcements for form elements
            value_announced = await self._has_value_announcements(element)
            
            # Identify defects
            if tag_name == 'img' and not has_alt_text and not has_aria_label:
                defects.append(ScreenReaderDefect(
                    element_type=tag_name,
                    element_description=description,
                    issue="Image missing alt text or aria-label",
                    severity=SeverityLevel.CRITICAL,
                    recommendation="Add descriptive alt text or aria-label for screen readers",
                    selector=selector
                ))
            
            if tag_name == 'button':
                button_text = self._safe_execute(lambda el: el.text.strip(), element)
                if (not button_text or len(button_text) == 0) and not has_aria_label and not has_aria_labelledby:
                    defects.append(ScreenReaderDefect(
                        element_type=tag_name,
                        element_description=description,
                        issue="Button missing accessible name",
                        severity=SeverityLevel.CRITICAL,
                        recommendation="Add text content or aria-label to describe button purpose",
                        selector=selector
                    ))
            
            if tag_name == 'a':
                link_text = self._safe_execute(lambda el: el.text.strip(), element)
                if (not link_text or len(link_text) == 0) and not has_aria_label and not has_aria_labelledby:
                    # Check if it has an image with alt text
                    img_elements = self._safe_execute(lambda el: el.find_elements(By.TAG_NAME, "img"), element)
                    has_accessible_image = False
                    if img_elements:
                        for img in img_elements[:1]:  # Check first image only
                            img_alt = self._safe_execute(lambda el: el.get_attribute('alt'), img)
                            if img_alt:
                                has_accessible_image = True
                                break
                    
                    if not has_accessible_image:
                        defects.append(ScreenReaderDefect(
                            element_type=tag_name,
                            element_description=description,
                            issue="Link missing accessible name",
                            severity=SeverityLevel.CRITICAL,
                            recommendation="Add link text or aria-label to describe link destination",
                            selector=selector
                        ))
            
            if role_present and role in ['button', 'link', 'checkbox', 'radio', 'tab']:
                if not state_announced:
                    defects.append(ScreenReaderDefect(
                        element_type=tag_name,
                        element_description=description,
                        issue="Interactive element missing state announcements",
                        severity=SeverityLevel.HIGH,
                        recommendation="Add ARIA states like aria-expanded, aria-pressed, aria-selected, etc.",
                        selector=selector
                    ))
            
            # Check for form elements without labels
            if tag_name in ['input', 'select', 'textarea']:
                if not has_aria_label and not has_aria_labelledby:
                    # Check if there's an associated label
                    input_id = self._safe_execute(lambda el: el.get_attribute('id'), element)
                    if input_id:
                        label_elements = self._find_elements_safe(f"label[for='{input_id}']")
                        if not label_elements:
                            # Check for wrapping label
                            parent_label = self._safe_execute(lambda el: el.find_element(By.XPATH, "./ancestor::label"), element)
                            if not parent_label:
                                defects.append(ScreenReaderDefect(
                                    element_type=tag_name,
                                    element_description=description,
                                    issue="Form element missing accessible label",
                                    severity=SeverityLevel.CRITICAL,
                                    recommendation="Add associated label element or aria-label/aria-labelledby",
                                    selector=selector
                                ))
            
            # Check for empty headings
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                heading_text = self._safe_execute(lambda el: el.text.strip(), element)
                if not heading_text or len(heading_text) == 0:
                    defects.append(ScreenReaderDefect(
                        element_type=tag_name,
                        element_description=description,
                        issue="Empty heading element",
                        severity=SeverityLevel.HIGH,
                        recommendation="Add meaningful text content to heading",
                        selector=selector
                    ))
            
        except StaleElementReferenceException:
            self.logger.debug("Element became stale during screen reader testing")
        except Exception as e:
            self.logger.warning(f"Failed to test element screen reader support: {e}")
        
        return defects
    
    async def _has_state_announcements(self, element) -> bool:
        """Check if element has ARIA state announcements with stale protection"""
        try:
            states = [
                'aria-expanded', 'aria-pressed', 'aria-checked', 'aria-selected',
                'aria-disabled', 'aria-hidden', 'aria-invalid', 'aria-required',
                'aria-readonly', 'aria-busy'
            ]
            for state in states:
                state_value = self._safe_execute(lambda el: el.get_attribute(state), element)
                if state_value is not None:  # Check if attribute exists (even if false)
                    return True
            return False
        except StaleElementReferenceException:
            return False
        except Exception:
            return False
    
    async def _has_value_announcements(self, element) -> bool:
        """Check if element has value announcements with stale protection"""
        try:
            value_attributes = [
                'aria-valuenow', 'aria-valuetext', 'aria-valuemin', 'aria-valuemax'
            ]
            for attr in value_attributes:
                if self._safe_execute(lambda el: el.get_attribute(attr), element):
                    return True
            return False
        except StaleElementReferenceException:
            return False
        except Exception:
            return False