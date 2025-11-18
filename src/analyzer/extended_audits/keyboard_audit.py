# src/analyzer/extended_audits/keyboard_audit.py
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from typing import List, Optional
from .base_audit import BaseAudit
from ..models.extended_audit_models import KeyboardDefect, SeverityLevel

class KeyboardAudit(BaseAudit):
    async def run_audit(self) -> List[KeyboardDefect]:
        """Test keyboard navigation and return defects"""
        defects = []
        
        try:
            # Get all potentially focusable elements
            selectors = [
                "a[href]", "button", "input", "select", "textarea",
                "[tabindex]", "[onclick]", "[role='button']", "[role='link']",
                "details", "summary", "[contenteditable='true']"
            ]
            
            # Collect elements safely
            all_elements = []
            for selector in selectors:
                elements = self._find_elements_safe(selector)
                all_elements.extend(elements)
                self.logger.debug(f"Found {len(elements)} elements with selector: {selector}")
            
            # Remove duplicates using selector strings instead of element objects
            unique_elements = self._get_unique_elements(all_elements)
            self.logger.info(f"Testing {len(unique_elements)} unique focusable elements")
            
            # Test each element with stale element protection
            tested_count = 0
            for element in unique_elements:
                try:
                    element_defects = await self._test_element_keyboard_navigation(element)
                    defects.extend(element_defects)
                    tested_count += 1
                except StaleElementReferenceException:
                    self.logger.debug("Element became stale during testing, skipping...")
                    continue
                except Exception as e:
                    self.logger.warning(f"Failed to test element: {e}")
                    continue
            
            self.logger.info(f"Successfully tested {tested_count}/{len(unique_elements)} elements")
            
        except Exception as e:
            self.logger.error(f"Keyboard navigation test failed: {e}")
        
        return defects
    
    async def _test_element_keyboard_navigation(self, element) -> List[KeyboardDefect]:
        """Test keyboard navigation for a single element and return defects"""
        defects = []
        
        try:
            # Refresh element reference to avoid staleness
            selector = self._get_element_selector(element)
            if not selector or selector == "unknown":
                return defects
            
            refreshed_elements = self._find_elements_safe(selector)
            if not refreshed_elements:
                return defects  # Element no longer exists
            
            element = refreshed_elements[0]  # Use fresh element reference
            
            tag_name = self._safe_execute(lambda el: el.tag_name.lower(), element)
            description = self._get_element_description(element)
            
            if not tag_name:
                return defects
            
            # Check if focusable
            is_focusable = await self._is_element_focusable(element)
            
            if is_focusable:
                # Check for negative tabindex
                tab_index = self._safe_execute(lambda el: el.get_attribute('tabindex'), element)
                if tab_index and tab_index.isdigit() and int(tab_index) < 0:
                    defects.append(KeyboardDefect(
                        element_type=tag_name,
                        element_description=description,
                        issue="Negative tabindex breaks navigation flow",
                        severity=SeverityLevel.HIGH,
                        recommendation="Remove negative tabindex or use positive values for logical focus order",
                        selector=selector
                    ))
                
                # Check visible focus
                has_visible_focus = await self._has_visible_focus_indicator(element)
                if not has_visible_focus:
                    defects.append(KeyboardDefect(
                        element_type=tag_name,
                        element_description=description,
                        issue="No visible focus indicator",
                        severity=SeverityLevel.HIGH,
                        recommendation="Add CSS outline or border changes on :focus state",
                        selector=selector
                    ))
                
                # Test actual keyboard interaction
                works_with_keyboard = await self._test_keyboard_interaction(element)
                if not works_with_keyboard:
                    defects.append(KeyboardDefect(
                        element_type=tag_name,
                        element_description=description,
                        issue="Element doesn't respond to keyboard input",
                        severity=SeverityLevel.CRITICAL,
                        recommendation="Ensure element can be activated with Enter/Space keys",
                        selector=selector
                    ))
            else:
                # Element should be focusable but isn't
                if tag_name in ['a', 'button', 'input', 'select', 'textarea']:
                    defects.append(KeyboardDefect(
                        element_type=tag_name,
                        element_description=description,
                        issue="Interactive element is not keyboard focusable",
                        severity=SeverityLevel.CRITICAL,
                        recommendation="Ensure element is visible and enabled, check tabindex",
                        selector=selector
                    ))
            
        except StaleElementReferenceException:
            self.logger.debug("Element became stale during detailed testing")
        except Exception as e:
            self.logger.warning(f"Failed to test element keyboard navigation: {e}")
        
        return defects
    
    async def _is_element_focusable(self, element) -> bool:
        """Check if element can receive focus with stale element protection"""
        try:
            # Check visibility and enabled state
            is_displayed = self._safe_execute(lambda el: el.is_displayed(), element)
            is_enabled = self._safe_execute(lambda el: el.is_enabled(), element)
            
            if not is_displayed or not is_enabled:
                return False
            
            # Check tabindex
            tabindex = self._safe_execute(lambda el: el.get_attribute('tabindex'), element)
            if tabindex and tabindex.isdigit() and int(tabindex) < 0:
                return False
            
            # Check if element is naturally focusable
            tag_name = self._safe_execute(lambda el: el.tag_name.lower(), element)
            naturally_focusable = tag_name in ['a', 'button', 'input', 'select', 'textarea', 'details', 'summary']
            
            # Check if element has explicit tabindex or role
            has_tabindex = tabindex is not None
            role = self._safe_execute(lambda el: el.get_attribute('role'), element)
            has_focusable_role = role in ['button', 'link', 'tab', 'menuitem']
            
            return naturally_focusable or has_tabindex or has_focusable_role
            
        except StaleElementReferenceException:
            return False
        except Exception:
            return False
    
    async def _has_visible_focus_indicator(self, element) -> bool:
        """Check if element has visible focus indicator with stale element protection"""
        try:
            # Get computed styles for focus using JavaScript (more reliable)
            selector = self._get_element_selector(element)
            if not selector:
                return False
            
            focus_script = f"""
            var element = document.querySelector('{selector}');
            if (!element) return false;
            
            var styles = window.getComputedStyle(element);
            var outline = styles.outline;
            var outlineWidth = styles.outlineWidth;
            var border = styles.border;
            
            // Check for visible outline
            var hasOutline = outline !== 'none' && outlineWidth !== '0px';
            
            // Check for border changes on focus
            var hasBorderFocus = false;
            try {{
                element.focus();
                var focusedStyles = window.getComputedStyle(element);
                hasBorderFocus = focusedStyles.border !== border;
                element.blur();
            }} catch (e) {{
                // Ignore focus/blur errors
            }}
            
            return hasOutline || hasBorderFocus;
            """
            
            result = self.driver.execute_script(focus_script)
            return bool(result)
            
        except StaleElementReferenceException:
            return False
        except Exception:
            return False
    
    async def _test_keyboard_interaction(self, element) -> bool:
        """Test if element responds to keyboard input with stale element protection"""
        try:
            selector = self._get_element_selector(element)
            if not selector:
                return False
            
            # Focus the element using JavaScript
            focus_script = f"""
            var element = document.querySelector('{selector}');
            if (element) {{
                element.focus();
                return document.activeElement === element;
            }}
            return false;
            """
            
            focus_result = self.driver.execute_script(focus_script)
            if not focus_result:
                return False
            
            # Small delay to ensure focus is applied
            await asyncio.sleep(0.3)
            
            # Test interaction based on element type
            tag_name = self._safe_execute(lambda el: el.tag_name.lower(), element)
            role = self._safe_execute(lambda el: el.get_attribute('role'), element)
            
            if tag_name in ['button', 'a'] or role in ['button', 'link']:
                # Test click simulation
                click_script = f"""
                var element = document.querySelector('{selector}');
                if (!element) return false;
                
                var clicked = false;
                var clickHandler = function() {{ clicked = true; }};
                
                element.addEventListener('click', clickHandler);
                element.focus();
                
                // Simulate Enter key press
                var enterEvent = new KeyboardEvent('keydown', {{ 
                    key: 'Enter', 
                    keyCode: 13, 
                    which: 13,
                    bubbles: true 
                }});
                element.dispatchEvent(enterEvent);
                
                var enterEventUp = new KeyboardEvent('keyup', {{ 
                    key: 'Enter', 
                    keyCode: 13, 
                    which: 13,
                    bubbles: true 
                }});
                element.dispatchEvent(enterEventUp);
                
                // Remove event listener
                setTimeout(function() {{
                    element.removeEventListener('click', clickHandler);
                }}, 100);
                
                return clicked;
                """
                
                click_result = self.driver.execute_script(click_script)
                return bool(click_result)
            
            # For other elements, just check if focus worked
            return focus_result
            
        except StaleElementReferenceException:
            return False
        except Exception:
            return False