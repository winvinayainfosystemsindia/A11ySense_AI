# src/analyzer/extended_audits/skip_link_audit.py
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from typing import List
from .base_audit import BaseAudit
from ..models.extended_audit_models import SkipLinkDefect, SeverityLevel

class SkipLinkAudit(BaseAudit):
    async def run_audit(self) -> List[SkipLinkDefect]:
        """Check for skip links and return defects"""
        defects = []
        
        try:
            # Look for skip links with various patterns
            skip_link_selectors = [
                "a[href*='#main']",
                "a[href*='#content']",
                "a[href*='#navigation']",
                "a[href*='#nav']",
                "a[href^='#']",
                "[class*='skip']",
                "[class*='sr-only']",
                "[class*='screen-reader']",
                "[class*='visually-hidden']"
            ]
            
            skip_links_found = False
            total_links_checked = 0
            
            for selector in skip_link_selectors:
                elements = self._find_elements_safe(selector)
                total_links_checked += len(elements)
                
                for element in elements:
                    try:
                        # Check if this looks like a skip link
                        is_skip_link = await self._is_skip_link(element)
                        if is_skip_link:
                            skip_links_found = True
                            element_defects = await self._test_skip_link(element)
                            defects.extend(element_defects)
                    except StaleElementReferenceException:
                        self.logger.debug(f"Stale skip link with selector {selector}, skipping...")
                        continue
                    except Exception as e:
                        self.logger.warning(f"Failed to process skip link with selector {selector}: {e}")
                        continue
            
            # If no skip links found, add a defect
            if not skip_links_found:
                defects.append(SkipLinkDefect(
                    issue="No skip links found",
                    severity=SeverityLevel.MEDIUM,
                    recommendation="Add skip links to allow keyboard users to bypass repetitive content"
                ))
            
            self.logger.info(f"Skip link audit: checked {total_links_checked} elements, found {len([d for d in defects if 'No skip links' not in d.issue])} skip links")
            
        except Exception as e:
            self.logger.error(f"Skip link check failed: {e}")
        
        return defects
    
    async def _is_skip_link(self, element) -> bool:
        """Determine if an element is a skip link"""
        try:
            # Refresh element reference
            selector = self._get_element_selector(element)
            refreshed_elements = self._find_elements_safe(selector)
            if not refreshed_elements:
                return False
            
            element = refreshed_elements[0]
            
            # Check link text for skip-related keywords
            link_text = self._safe_execute(lambda el: el.text.lower(), element) or ""
            skip_keywords = ['skip', 'jump', 'main', 'content', 'navigation', 'menu', 'search']
            
            if any(keyword in link_text for keyword in skip_keywords):
                return True
            
            # Check href for common skip link patterns
            href = self._safe_execute(lambda el: el.get_attribute('href'), element) or ""
            if '#' in href:
                target_id = href.split('#')[-1]
                target_keywords = ['main', 'content', 'navigation', 'nav', 'search']
                if any(keyword in target_id.lower() for keyword in target_keywords):
                    return True
            
            # Check for visually hidden skip links
            is_visually_hidden = await self._is_visually_hidden(element)
            if is_visually_hidden and href and '#' in href:
                return True
            
            return False
            
        except StaleElementReferenceException:
            return False
        except Exception as e:
            self.logger.debug(f"Failed to check if element is skip link: {e}")
            return False
    
    async def _test_skip_link(self, element) -> List[SkipLinkDefect]:
        """Test skip link functionality and return defects"""
        defects = []
        
        try:
            # Refresh element reference
            selector = self._get_element_selector(element)
            refreshed_elements = self._find_elements_safe(selector)
            if not refreshed_elements:
                defects.append(SkipLinkDefect(
                    issue="Skip link element not found",
                    severity=SeverityLevel.HIGH,
                    recommendation="Skip link selector may be incorrect or element was removed"
                ))
                return defects
            
            element = refreshed_elements[0]
            
            href = self._safe_execute(lambda el: el.get_attribute('href'), element)
            target_id = None
            target_exists = False
            works_properly = False
            is_visible_on_focus = False
            
            if href and '#' in href:
                target_id = href.split('#')[-1]
                if target_id:
                    # Check if target exists
                    target_exists = await self._check_target_exists(target_id)
                    
                    if target_exists:
                        # Test if skip link works
                        works_properly = await self._test_skip_link_functionality(element, target_id)
                        
                        # Check if link becomes visible on focus
                        is_visible_on_focus = await self._is_visible_on_focus(element)
            
            # Report defects
            if not target_exists:
                defects.append(SkipLinkDefect(
                    issue="Skip link target not found",
                    severity=SeverityLevel.HIGH,
                    recommendation=f"Ensure target element with id='{target_id}' exists on the page",
                    target_id=target_id
                ))
            
            if not works_properly and target_exists:
                defects.append(SkipLinkDefect(
                    issue="Skip link doesn't properly focus target",
                    severity=SeverityLevel.HIGH,
                    recommendation="Ensure skip link properly transfers focus to target element",
                    target_id=target_id
                ))
            
            if not is_visible_on_focus:
                defects.append(SkipLinkDefect(
                    issue="Skip link is not visible when focused",
                    severity=SeverityLevel.MEDIUM,
                    recommendation="Ensure skip link becomes visible when it receives keyboard focus",
                    target_id=target_id
                ))
            
        except StaleElementReferenceException:
            self.logger.debug("Skip link became stale during testing")
            defects.append(SkipLinkDefect(
                issue="Skip link testing failed due to element staleness",
                severity=SeverityLevel.MEDIUM,
                recommendation="Ensure skip link implementation is stable"
            ))
        except Exception as e:
            self.logger.warning(f"Failed to test skip link: {e}")
            defects.append(SkipLinkDefect(
                issue="Error testing skip link functionality",
                severity=SeverityLevel.MEDIUM,
                recommendation="Check skip link implementation and target element"
            ))
        
        return defects
    
    async def _check_target_exists(self, target_id: str) -> bool:
        """Check if skip link target exists"""
        try:
            target_elements = self._find_elements_safe(f"#{target_id}")
            return len(target_elements) > 0
        except Exception:
            return False
    
    async def _test_skip_link_functionality(self, element, target_id: str) -> bool:
        """Test if skip link properly focuses the target"""
        try:
            # Use JavaScript to simulate skip link behavior
            selector = self._get_element_selector(element)
            if not selector:
                return False
            
            test_script = f"""
            var skipLink = document.querySelector('{selector}');
            var target = document.getElementById('{target_id}');
            
            if (!skipLink || !target) return false;
            
            // Store current focus
            var previousFocus = document.activeElement;
            
            // Simulate clicking the skip link
            skipLink.click();
            
            // Check if focus moved to target
            var focusMoved = document.activeElement === target;
            
            // Restore previous focus for continued testing
            if (previousFocus) previousFocus.focus();
            
            return focusMoved;
            """
            
            result = self.driver.execute_script(test_script)
            return bool(result)
            
        except Exception:
            return False
    
    async def _is_visible_on_focus(self, element) -> bool:
        """Check if skip link becomes visible when focused"""
        try:
            selector = self._get_element_selector(element)
            if not selector:
                return False
            
            visibility_script = f"""
            var element = document.querySelector('{selector}');
            if (!element) return false;
            
            // Get initial styles
            var initialDisplay = window.getComputedStyle(element).display;
            var initialVisibility = window.getComputedStyle(element).visibility;
            var initialOpacity = window.getComputedStyle(element).opacity;
            var initialWidth = window.getComputedStyle(element).width;
            var initialHeight = window.getComputedStyle(element).height;
            
            // Focus the element
            element.focus();
            
            // Get styles after focus
            var focusedDisplay = window.getComputedStyle(element).display;
            var focusedVisibility = window.getComputedStyle(element).visibility;
            var focusedOpacity = window.getComputedStyle(element).opacity;
            var focusedWidth = window.getComputedStyle(element).width;
            var focusedHeight = window.getComputedStyle(element).height;
            
            // Check if element became more visible
            var wasHidden = initialDisplay === 'none' || 
                           initialVisibility === 'hidden' || 
                           initialOpacity === '0' ||
                           initialWidth === '0px' ||
                           initialHeight === '0px';
            
            var isVisible = focusedDisplay !== 'none' && 
                          focusedVisibility !== 'hidden' && 
                          focusedOpacity !== '0' &&
                          focusedWidth !== '0px' &&
                          focusedHeight !== '0px';
            
            return wasHidden && isVisible;
            """
            
            result = self.driver.execute_script(visibility_script)
            return bool(result)
            
        except Exception:
            return False
    
    async def _is_visually_hidden(self, element) -> bool:
        """Check if element is visually hidden"""
        try:
            selector = self._get_element_selector(element)
            if not selector:
                return False
            
            hidden_script = f"""
            var element = document.querySelector('{selector}');
            if (!element) return false;
            
            var styles = window.getComputedStyle(element);
            
            // Common techniques for visually hiding content
            var isHidden = styles.display === 'none' ||
                          styles.visibility === 'hidden' ||
                          styles.opacity === '0' ||
                          styles.width === '0px' ||
                          styles.height === '0px' ||
                          styles.clip === 'rect(0px, 0px, 0px, 0px)' ||
                          (styles.position === 'absolute' && styles.left === '-9999px');
            
            return isHidden;
            """
            
            result = self.driver.execute_script(hidden_script)
            return bool(result)
            
        except Exception:
            return False