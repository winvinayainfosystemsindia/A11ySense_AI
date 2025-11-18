# src/analyzer/extended_audit_runner.py
import asyncio
import time
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..core.exceptions import AnalysisException
from ..utils.logger import setup_logger
from .models.extended_audit_models import (
    ExtendedAuditResult, KeyboardNavigationResult, ScreenReaderResult,
    LandmarkResult, SkipLinkResult, NavigationType, LandmarkType
)

class ExtendedAuditRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
        self.driver = None
    
    async def run_extended_audit(self, url: str) -> ExtendedAuditResult:
        """Run extended accessibility audits beyond axe-core"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting extended audit for: {url}")
            
            # Setup browser
            await self._setup_browser()
            
            # Navigate to URL
            self.driver.get(url)
            await asyncio.sleep(3)  # Wait for page load
            
            # Run all extended audits
            keyboard_results = await self._test_keyboard_navigation()
            screen_reader_results = await self._test_screen_reader_support()
            landmark_results = await self._check_landmarks()
            skip_link_results = await self._check_skip_links()
            
            # Create result object
            result = ExtendedAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                keyboard_navigation=keyboard_results,
                screen_reader_support=screen_reader_results,
                landmarks=landmark_results,
                skip_links=skip_link_results
            )
            
            result.calculate_scores()
            
            self.logger.info(
                f"Extended audit completed for {url}: "
                f"Keyboard: {result.keyboard_score:.1f}%, "
                f"Screen Reader: {result.screen_reader_score:.1f}%, "
                f"Structure: {result.structure_score:.1f}%"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Extended audit failed for {url}: {e}")
            return ExtendedAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                keyboard_navigation=[],
                screen_reader_support=[],
                landmarks=[],
                skip_links=[],
                error=str(e)
            )
        finally:
            await self._close_browser()
    
    async def _setup_browser(self):
        """Setup Chrome browser for extended testing"""
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.implicitly_wait(10)
    
    async def _close_browser(self):
        """Close browser instance"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")
    
    async def _test_keyboard_navigation(self) -> List[KeyboardNavigationResult]:
        """Test keyboard navigation for all interactive elements"""
        results = []
        
        try:
            # Get all potentially focusable elements
            selectors = [
                "a[href]", "button", "input", "select", "textarea",
                "[tabindex]", "[onclick]", "[role='button']", "[role='link']",
                "details", "summary", "[contenteditable='true']"
            ]
            
            focusable_elements = []
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                focusable_elements.extend(elements)
            
            # Remove duplicates
            seen_elements = set()
            unique_elements = []
            for element in focusable_elements:
                element_id = element.id
                if element_id not in seen_elements:
                    seen_elements.add(element_id)
                    unique_elements.append(element)
            
            # Test each element
            for i, element in enumerate(unique_elements):
                result = await self._test_element_keyboard_navigation(element, i)
                results.append(result)
            
        except Exception as e:
            self.logger.error(f"Keyboard navigation test failed: {e}")
        
        return results
    
    async def _test_element_keyboard_navigation(self, element, order: int) -> KeyboardNavigationResult:
        """Test keyboard navigation for a single element"""
        try:
            tag_name = element.tag_name.lower()
            element_type = tag_name
            issues = []
            
            # Get element description
            description = self._get_element_description(element)
            
            # Check if focusable
            is_focusable = await self._is_element_focusable(element)
            navigation_type = NavigationType.NONE
            
            if is_focusable:
                # Determine navigation type
                if tag_name in ['a', 'button', 'input', 'select', 'textarea']:
                    navigation_type = NavigationType.TAB
                elif tag_name in ['details', 'summary']:
                    navigation_type = NavigationType.BOTH
                else:
                    # Check ARIA role
                    role = element.get_attribute('role')
                    if role in ['button', 'link', 'tab', 'menuitem']:
                        navigation_type = NavigationType.TAB
                    else:
                        navigation_type = NavigationType.ARROW
            
            # Check tabindex
            tab_index = element.get_attribute('tabindex')
            if tab_index and int(tab_index) < 0:
                issues.append("Negative tabindex can break navigation flow")
            
            # Check visible focus
            has_visible_focus = await self._has_visible_focus_indicator(element)
            if not has_visible_focus and is_focusable:
                issues.append("No visible focus indicator")
            
            # Test actual keyboard interaction
            if is_focusable:
                works_with_keyboard = await self._test_keyboard_interaction(element)
                if not works_with_keyboard:
                    issues.append("Element doesn't respond to keyboard input")
            
            return KeyboardNavigationResult(
                element_type=element_type,
                element_description=description,
                is_focusable=is_focusable,
                navigation_type=navigation_type,
                tab_index=int(tab_index) if tab_index and tab_index.isdigit() else None,
                has_visible_focus=has_visible_focus,
                focus_order=order,
                issues=issues
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to test element keyboard navigation: {e}")
            return KeyboardNavigationResult(
                element_type="unknown",
                element_description="Error testing element",
                is_focusable=False,
                navigation_type=NavigationType.NONE,
                issues=[f"Test error: {str(e)}"]
            )
    
    async def _test_screen_reader_support(self) -> List[ScreenReaderResult]:
        """Test screen reader compatibility for key elements"""
        results = []
        
        try:
            # Test interactive elements and important semantic elements
            selectors = [
                "button", "a[href]", "input", "select", "textarea",
                "img", "[role]", "[aria-label]", "[aria-labelledby]",
                "header", "nav", "main", "footer", "section", "article",
                "[aria-expanded]", "[aria-hidden]", "[aria-live]"
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    result = await self._test_element_screen_reader_support(element)
                    results.append(result)
            
        except Exception as e:
            self.logger.error(f"Screen reader support test failed: {e}")
        
        return results
    
    async def _test_element_screen_reader_support(self, element) -> ScreenReaderResult:
        """Test screen reader support for a single element"""
        try:
            tag_name = element.tag_name.lower()
            description = self._get_element_description(element)
            issues = []
            
            # Check ARIA attributes
            has_aria_label = bool(element.get_attribute('aria-label'))
            has_aria_labelledby = bool(element.get_attribute('aria-labelledby'))
            has_aria_describedby = bool(element.get_attribute('aria-describedby'))
            
            # Check alt text for images
            has_alt_text = bool(element.get_attribute('alt')) if tag_name == 'img' else False
            
            # Check role
            role = element.get_attribute('role')
            role_present = bool(role)
            
            # Check state announcements
            state_announced = await self._has_state_announcements(element)
            
            # Check value announcements for form elements
            value_announced = await self._has_value_announcements(element)
            
            # Identify issues
            if tag_name in ['img', 'button', 'a'] and not any([has_aria_label, has_aria_labelledby, has_alt_text]):
                if tag_name == 'img' and not has_alt_text:
                    issues.append("Image missing alt text")
                elif tag_name == 'button' and not element.text.strip():
                    issues.append("Button missing accessible name")
                elif tag_name == 'a' and not element.text.strip() and not has_aria_label:
                    issues.append("Link missing accessible name")
            
            if role_present and role in ['button', 'link', 'checkbox', 'radio']:
                if not state_announced:
                    issues.append("Interactive element missing state announcements")
            
            return ScreenReaderResult(
                element_type=tag_name,
                element_description=description,
                has_aria_label=has_aria_label,
                has_aria_labelledby=has_aria_labelledby,
                has_aria_describedby=has_aria_describedby,
                has_alt_text=has_alt_text,
                role_present=role_present,
                role_value=role,
                state_announced=state_announced,
                value_announced=value_announced,
                issues=issues
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to test element screen reader support: {e}")
            return ScreenReaderResult(
                element_type="unknown",
                element_description="Error testing element",
                issues=[f"Test error: {str(e)}"]
            )
    
    async def _check_landmarks(self) -> List[LandmarkResult]:
        """Check for proper landmark structure"""
        results = []
        
        try:
            # Standard HTML5 landmarks
            landmark_selectors = {
                LandmarkType.BANNER: "header, [role='banner']",
                LandmarkType.MAIN: "main, [role='main']",
                LandmarkType.NAVIGATION: "nav, [role='navigation']",
                LandmarkType.COMPLEMENTARY: "aside, [role='complementary']",
                LandmarkType.CONTENTINFO: "footer, [role='contentinfo']",
                LandmarkType.SEARCH: "[role='search']",
                LandmarkType.FORM: "form, [role='form']",
                LandmarkType.REGION: "section, [role='region']"
            }
            
            for landmark_type, selector in landmark_selectors.items():
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    result = await self._check_landmark_element(element, landmark_type)
                    results.append(result)
            
        except Exception as e:
            self.logger.error(f"Landmark check failed: {e}")
        
        return results
    
    async def _check_skip_links(self) -> List[SkipLinkResult]:
        """Check for skip links and their functionality"""
        results = []
        
        try:
            # Look for skip links
            skip_link_selectors = [
                "a[href*='#main']",
                "a[href*='#content']",
                "a[href*='#navigation']",
                "a[href^='#']",
                "[class*='skip']",
                "[class*='sr-only']"
            ]
            
            for selector in skip_link_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    link_text = element.text.lower()
                    if any(keyword in link_text for keyword in ['skip', 'jump', 'main', 'content', 'navigation']):
                        result = await self._test_skip_link(element)
                        results.append(result)
            
            # If no skip links found, add a result indicating absence
            if not results:
                results.append(SkipLinkResult(
                    exists=False,
                    issues=["No skip links found"]
                ))
            
        except Exception as e:
            self.logger.error(f"Skip link check failed: {e}")
        
        return results
    
    # Helper methods for the actual testing
    async def _is_element_focusable(self, element) -> bool:
        """Check if element can receive focus"""
        try:
            # Check visibility and enabled state
            if not element.is_displayed() or not element.is_enabled():
                return False
            
            # Check tabindex
            tabindex = element.get_attribute('tabindex')
            if tabindex and int(tabindex) < 0:
                return False
            
            return True
        except:
            return False
    
    async def _has_visible_focus_indicator(self, element) -> bool:
        """Check if element has visible focus indicator"""
        try:
            # Get computed styles for focus
            outline = element.value_of_css_property('outline')
            outline_width = element.value_of_css_property('outline-width')
            border = element.value_of_css_property('border')
            
            has_outline = outline != 'none' and outline_width != '0px'
            has_border_change = 'focus' in str(element.get_attribute('class')).lower()
            
            return has_outline or has_border_change
        except:
            return False
    
    async def _test_keyboard_interaction(self, element) -> bool:
        """Test if element responds to keyboard input"""
        try:
            # Try to focus the element
            self.driver.execute_script("arguments[0].focus();", element)
            
            # Check if it actually got focus
            focused_element = self.driver.switch_to.active_element
            is_focused = focused_element.id == element.id
            
            # Test Enter key for buttons/links
            tag_name = element.tag_name.lower()
            if tag_name in ['button', 'a'] or element.get_attribute('role') in ['button', 'link']:
                try:
                    element.send_keys(Keys.ENTER)
                    # If we're still on the same page or no error occurred, consider it successful
                    return True
                except:
                    return False
            
            return is_focused
        except:
            return False
    
    async def _has_state_announcements(self, element) -> bool:
        """Check if element has ARIA state announcements"""
        try:
            states = [
                'aria-expanded', 'aria-pressed', 'aria-checked', 'aria-selected',
                'aria-disabled', 'aria-hidden', 'aria-invalid'
            ]
            return any(element.get_attribute(state) for state in states)
        except:
            return False
    
    async def _has_value_announcements(self, element) -> bool:
        """Check if element has value announcements"""
        try:
            value_attributes = [
                'aria-valuenow', 'aria-valuetext', 'aria-valuemin', 'aria-valuemax'
            ]
            return any(element.get_attribute(attr) for attr in value_attributes)
        except:
            return False
    
    async def _check_landmark_element(self, element, landmark_type: LandmarkType) -> LandmarkResult:
        """Check individual landmark element"""
        try:
            description = self._get_element_description(element)
            issues = []
            
            # Check if landmark has a label
            has_label = bool(element.get_attribute('aria-label') or 
                           element.get_attribute('aria-labelledby'))
            label_text = element.get_attribute('aria-label')
            
            # Check for uniqueness (basic check)
            same_type_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                element.tag_name + "[role='" + landmark_type.value + "']" if element.get_attribute('role') 
                else element.tag_name
            )
            is_unique = len(same_type_elements) <= 1
            
            if not has_label and landmark_type in [LandmarkType.REGION, LandmarkType.FORM]:
                issues.append("Landmark missing accessible label")
            
            if not is_unique and landmark_type in [LandmarkType.BANNER, LandmarkType.CONTENTINFO]:
                issues.append("Multiple landmarks of same type found")
            
            return LandmarkResult(
                landmark_type=landmark_type,
                element_description=description,
                has_label=has_label,
                label_text=label_text,
                is_unique=is_unique,
                issues=issues
            )
        except Exception as e:
            return LandmarkResult(
                landmark_type=landmark_type,
                element_description="Error checking landmark",
                issues=[f"Check error: {str(e)}"]
            )
    
    async def _test_skip_link(self, element) -> SkipLinkResult:
        """Test skip link functionality"""
        try:
            href = element.get_attribute('href')
            target_id = None
            target_exists = False
            works_properly = False
            
            if href and '#' in href:
                target_id = href.split('#')[-1]
                if target_id:
                    try:
                        target_element = self.driver.find_element(By.ID, target_id)
                        target_exists = True
                        
                        # Test if skip link works
                        element.send_keys(Keys.ENTER)
                        await asyncio.sleep(1)
                        
                        # Check if target received focus
                        focused_element = self.driver.switch_to.active_element
                        works_properly = focused_element.id == target_id
                        
                    except:
                        target_exists = False
            
            issues = []
            if not target_exists:
                issues.append("Skip link target not found")
            if not works_properly:
                issues.append("Skip link doesn't properly focus target")
            
            return SkipLinkResult(
                exists=True,
                is_visible_on_focus=element.is_displayed(),
                target_exists=target_exists,
                target_id=target_id,
                works_properly=works_properly,
                issues=issues
            )
        except Exception as e:
            return SkipLinkResult(
                exists=False,
                issues=[f"Test error: {str(e)}"]
            )
    
    def _get_element_description(self, element) -> str:
        """Get descriptive text for an element"""
        try:
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
            
        except:
            return "Unknown element"