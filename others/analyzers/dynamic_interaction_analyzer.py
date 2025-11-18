import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from playwright.async_api import Page, TimeoutError
from ...utils.logger import setup_logger

@dataclass
class DynamicInteractionResult:
    button_interactions: Dict[str, Any]
    form_submissions: Dict[str, Any]
    dynamic_content_changes: Dict[str, Any]
    keyboard_navigation: Dict[str, Any]
    focus_management: Dict[str, Any]
    aria_live_regions: Dict[str, Any]

class DynamicInteractionAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def analyze_dynamic_interactions(self, page: Page) -> DynamicInteractionResult:
        """Analyze dynamic interactions and content changes"""
        self.logger.debug("Analyzing dynamic interactions")
        
        # Run all interaction tests
        button_interactions = await self._test_button_interactions(page)
        form_submissions = await self._test_form_submissions(page)
        dynamic_content = await self._test_dynamic_content_changes(page)
        keyboard_nav = await self._test_keyboard_navigation(page)
        focus_mgmt = await self._test_focus_management(page)
        aria_live = await self._analyze_aria_live_regions(page)
        
        return DynamicInteractionResult(
            button_interactions=button_interactions,
            form_submissions=form_submissions,
            dynamic_content_changes=dynamic_content,
            keyboard_navigation=keyboard_nav,
            focus_management=focus_mgmt,
            aria_live_regions=aria_live
        )
    
    async def _test_button_interactions(self, page: Page) -> Dict[str, Any]:
        """Test button interactions and their accessibility impact"""
        self.logger.debug("Testing button interactions")
        
        results = {
            "total_buttons_tested": 0,
            "buttons_with_onclick": 0,
            "buttons_with_correct_focus": 0,
            "buttons_triggering_dynamic_content": 0,
            "interaction_issues": []
        }
        
        # Find all interactive buttons
        buttons = await page.query_selector_all('button, [role="button"], input[type="button"], input[type="submit"]')
        
        for i, button in enumerate(buttons[:10]):  # Test first 10 buttons to avoid timeouts
            try:
                button_info = await self._test_single_button(page, button, i)
                results["total_buttons_tested"] += 1
                
                if button_info.get("has_onclick"):
                    results["buttons_with_onclick"] += 1
                
                if button_info.get("maintains_focus"):
                    results["buttons_with_correct_focus"] += 1
                
                if button_info.get("triggers_dynamic_content"):
                    results["buttons_triggering_dynamic_content"] += 1
                
                if button_info.get("issues"):
                    results["interaction_issues"].extend(button_info["issues"])
                    
            except Exception as e:
                self.logger.warning(f"Button interaction test failed: {e}")
                continue
        
        return results
    
    async def _test_single_button(self, page: Page, button, index: int) -> Dict[str, Any]:
        """Test a single button interaction"""
        button_info = {
            "index": index,
            "has_onclick": False,
            "maintains_focus": False,
            "triggers_dynamic_content": False,
            "issues": []
        }
        
        # Get button properties
        tag_name = await button.evaluate('el => el.tagName')
        button_type = await button.get_attribute('type')
        has_onclick = await button.evaluate('el => !!el.onclick || el.hasAttribute("onclick")')
        button_info["has_onclick"] = has_onclick
        
        # Skip if button is disabled
        is_disabled = await button.evaluate('el => el.disabled')
        if is_disabled:
            button_info["issues"].append("Button is disabled")
            return button_info
        
        # Take screenshot before interaction
        initial_screenshot = await page.screenshot()
        
        try:
            # Click the button and wait for potential changes
            await button.click(timeout=5000)
            
            # Wait for any dynamic changes
            await page.wait_for_timeout(1000)
            
            # Check if focus is maintained or moved appropriately
            focused_element = await page.evaluate('() => document.activeElement')
            is_same_button = await button.evaluate('(el, focused) => el === focused', focused_element)
            button_info["maintains_focus"] = is_same_button
            
            if not is_same_button:
                button_info["issues"].append("Focus not maintained after click")
            
            # Check for dynamic content changes
            content_changed = await self._detect_content_changes(page, initial_screenshot)
            button_info["triggers_dynamic_content"] = content_changed
            
            if content_changed:
                # Check if dynamic content is accessible
                accessibility_issues = await self._check_dynamic_content_accessibility(page)
                if accessibility_issues:
                    button_info["issues"].extend(accessibility_issues)
            
        except TimeoutError:
            button_info["issues"].append("Button click timed out")
        except Exception as e:
            button_info["issues"].append(f"Click failed: {str(e)}")
        
        return button_info
    
    async def _test_form_submissions(self, page: Page) -> Dict[str, Any]:
        """Test form submissions and their accessibility impact"""
        self.logger.debug("Testing form submissions")
        
        results = {
            "total_forms_tested": 0,
            "forms_with_validation": 0,
            "forms_with_accessible_errors": 0,
            "submission_issues": []
        }
        
        forms = await page.query_selector_all('form')
        
        for i, form in enumerate(forms[:3]):  # Test first 3 forms
            try:
                form_info = await self._test_single_form(page, form, i)
                results["total_forms_tested"] += 1
                
                if form_info.get("has_validation"):
                    results["forms_with_validation"] += 1
                
                if form_info.get("accessible_errors"):
                    results["forms_with_accessible_errors"] += 1
                
                if form_info.get("issues"):
                    results["submission_issues"].extend(form_info["issues"])
                    
            except Exception as e:
                self.logger.warning(f"Form submission test failed: {e}")
                continue
        
        return results
    
    async def _test_single_form(self, page: Page, form, index: int) -> Dict[str, Any]:
        """Test a single form submission"""
        form_info = {
            "index": index,
            "has_validation": False,
            "accessible_errors": False,
            "issues": []
        }
        
        # Check for HTML5 validation
        has_required = await form.query_selector('[required]')
        form_info["has_validation"] = bool(has_required)
        
        # Try to submit form with empty required fields
        try:
            # Take screenshot before submission
            initial_screenshot = await page.screenshot()
            
            # Find submit button
            submit_button = await form.query_selector('button[type="submit"], input[type="submit"]')
            if submit_button:
                await submit_button.click(timeout=5000)
                
                # Wait for validation or submission
                await page.wait_for_timeout(2000)
                
                # Check for error messages
                error_messages = await form.query_selector_all('[aria-invalid="true"], .error, .invalid, [role="alert"]')
                if error_messages:
                    form_info["accessible_errors"] = await self._check_error_accessibility(error_messages)
                
                # Check for content changes
                content_changed = await self._detect_content_changes(page, initial_screenshot)
                if content_changed:
                    form_info["issues"].append("Page navigation occurred during form test")
                    
        except Exception as e:
            form_info["issues"].append(f"Form submission test failed: {str(e)}")
        
        return form_info
    
    async def _test_dynamic_content_changes(self, page: Page) -> Dict[str, Any]:
        """Test various dynamic content changes"""
        self.logger.debug("Testing dynamic content changes")
        
        results = {
            "ajax_requests": 0,
            "dom_modifications": 0,
            "modal_dialogs": 0,
            "tab_interfaces": 0,
            "accessibility_issues": []
        }
        
        # Test tab interfaces
        tabs = await page.query_selector_all('[role="tab"], [data-tab], .tab')
        if tabs:
            tab_issues = await self._test_tab_interface(page, tabs)
            results["tab_interfaces"] = len(tabs)
            results["accessibility_issues"].extend(tab_issues)
        
        # Test modal dialogs
        modals = await page.query_selector_all('[role="dialog"], .modal, .popup')
        if modals:
            modal_issues = await self._test_modal_dialogs(page, modals)
            results["modal_dialogs"] = len(modals)
            results["accessibility_issues"].extend(modal_issues)
        
        # Monitor for AJAX requests and DOM changes
        dom_changes = await self._monitor_dom_changes(page)
        results.update(dom_changes)
        
        return results
    
    async def _test_tab_interface(self, page: Page, tabs: List) -> List[str]:
        """Test tab interface accessibility"""
        issues = []
        
        try:
            # Click first tab
            first_tab = tabs[0]
            await first_tab.click()
            await page.wait_for_timeout(500)
            
            # Check if tab is properly selected
            is_selected = await first_tab.evaluate('el => el.getAttribute("aria-selected") === "true"')
            if not is_selected:
                issues.append("Tab selection not properly indicated with aria-selected")
            
            # Check if tab panel is accessible
            tabpanel_id = await first_tab.get_attribute('aria-controls')
            if tabpanel_id:
                tabpanel = await page.query_selector(f'#{tabpanel_id}')
                if tabpanel:
                    is_visible = await tabpanel.evaluate('el => el.offsetParent !== null')
                    if not is_visible:
                        issues.append("Tab panel not visible after tab selection")
                else:
                    issues.append("Tab panel not found for tab controls")
            
        except Exception as e:
            issues.append(f"Tab interface test failed: {str(e)}")
        
        return issues
    
    async def _test_modal_dialogs(self, page: Page, modals: List) -> List[str]:
        """Test modal dialog accessibility"""
        issues = []
        
        for modal in modals[:2]:  # Test first 2 modals
            try:
                # Try to open modal (if it has a trigger)
                trigger = await modal.evaluate_handle('''
                    el => {
                        // Find trigger by aria-controls or data attributes
                        const modalId = el.id;
                        if (modalId) {
                            return document.querySelector(`[aria-controls="${modalId}"], [data-target="#${modalId}"]`);
                        }
                        return null;
                    }
                ''')
                
                if trigger:
                    await trigger.click()
                    await page.wait_for_timeout(1000)
                    
                    # Check modal accessibility
                    modal_issues = await self._check_modal_accessibility(page, modal)
                    issues.extend(modal_issues)
                    
                    # Close modal
                    close_btn = await modal.query_selector('[aria-label*="close"], .close, [data-dismiss="modal"]')
                    if close_btn:
                        await close_btn.click()
                    
            except Exception as e:
                issues.append(f"Modal test failed: {str(e)}")
        
        return issues
    
    async def _check_modal_accessibility(self, page: Page, modal) -> List[str]:
        """Check modal dialog for accessibility issues"""
        issues = []
        
        # Check if focus is trapped in modal
        focused_element = await page.evaluate('() => document.activeElement')
        is_in_modal = await modal.evaluate('(modal, focused) => modal.contains(focused)', focused_element)
        if not is_in_modal:
            issues.append("Focus not trapped in modal dialog")
        
        # Check for proper aria attributes
        has_label = await modal.evaluate('el => el.hasAttribute("aria-labelledby") || el.hasAttribute("aria-label")')
        if not has_label:
            issues.append("Modal missing accessible label")
        
        # Check if backdrop prevents interaction
        backdrop = await page.query_selector('.modal-backdrop, .overlay')
        if backdrop:
            backdrop_style = await backdrop.evaluate('el => getComputedStyle(el).pointerEvents')
            if backdrop_style != 'none':
                issues.append("Modal backdrop may not properly prevent background interactions")
        
        return issues
    
    async def _test_keyboard_navigation(self, page: Page) -> Dict[str, Any]:
        """Test keyboard navigation through interactive elements"""
        self.logger.debug("Testing keyboard navigation")
        
        results = {
            "keyboard_traps": 0,
            "focus_order_issues": 0,
            "missing_keyboard_handlers": 0,
            "navigation_issues": []
        }
        
        # Test tab order
        try:
            # Focus first element
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(100)
            
            first_focused = await page.evaluate('() => document.activeElement')
            
            # Tab through several elements
            for i in range(20):  # Limit to 20 tabs to avoid infinite loops
                await page.keyboard.press('Tab')
                await page.wait_for_timeout(50)
                
                current_focused = await page.evaluate('() => document.activeElement')
                
                # Check for focus traps (same element focused repeatedly)
                if i > 5 and await first_focused.evaluate('(first, current) => first === current', current_focused):
                    results["keyboard_traps"] += 1
                    results["navigation_issues"].append("Possible keyboard trap detected")
                    break
                
                # Check if focus is visible
                is_focus_visible = await current_focused.evaluate('''
                    el => {
                        const style = getComputedStyle(el);
                        return style.outline !== 'none' || 
                               style.outlineStyle !== 'none' || 
                               style.boxShadow !== 'none' ||
                               el.getAttribute('data-custom-focus');
                    }
                ''')
                
                if not is_focus_visible:
                    results["navigation_issues"].append(f"Focus not visible on {await current_focused.evaluate('el => el.tagName')}")
                    
        except Exception as e:
            results["navigation_issues"].append(f"Keyboard navigation test failed: {str(e)}")
        
        return results
    
    async def _test_focus_management(self, page: Page) -> Dict[str, Any]:
        """Test focus management during dynamic interactions"""
        results = {
            "focus_restoration_issues": 0,
            "focus_target_issues": 0,
            "management_issues": []
        }
        
        # Test focus restoration after modal close
        modals = await page.query_selector_all('[role="dialog"]')
        for modal in modals[:2]:
            try:
                initial_focus = await page.evaluate('() => document.activeElement')
                
                # Open and close modal
                trigger = await self._find_modal_trigger(page, modal)
                if trigger:
                    await trigger.click()
                    await page.wait_for_timeout(500)
                    
                    # Close modal
                    close_btn = await modal.query_selector('[aria-label*="close"], .close')
                    if close_btn:
                        await close_btn.click()
                        await page.wait_for_timeout(500)
                        
                        # Check if focus returned
                        final_focus = await page.evaluate('() => document.activeElement')
                        focus_restored = await initial_focus.evaluate('(initial, final) => initial === final', final_focus)
                        
                        if not focus_restored:
                            results["focus_restoration_issues"] += 1
                            results["management_issues"].append("Focus not properly restored after modal close")
                            
            except Exception as e:
                results["management_issues"].append(f"Focus management test failed: {str(e)}")
        
        return results
    
    async def _analyze_aria_live_regions(self, page: Page) -> Dict[str, Any]:
        """Analyze ARIA live regions for dynamic content announcements"""
        results = {
            "live_regions_found": 0,
            "polite_regions": 0,
            "assertive_regions": 0,
            "live_region_issues": []
        }
        
        live_regions = await page.query_selector_all('[aria-live]')
        results["live_regions_found"] = len(live_regions)
        
        for region in live_regions:
            live_value = await region.get_attribute('aria-live')
            if live_value == 'polite':
                results["polite_regions"] += 1
            elif live_value == 'assertive':
                results["assertive_regions"] += 1
            
            # Check if live region has content
            has_content = await region.evaluate('el => el.textContent.trim().length > 0')
            if not has_content:
                results["live_region_issues"].append("Live region exists but has no content")
        
        return results
    
    # Helper methods
    async def _detect_content_changes(self, page: Page, initial_screenshot: bytes) -> bool:
        """Detect if content has changed after interaction"""
        try:
            current_screenshot = await page.screenshot()
            # Simple comparison - in production, you might want more sophisticated detection
            return initial_screenshot != current_screenshot
        except:
            return False
    
    async def _check_dynamic_content_accessibility(self, page: Page) -> List[str]:
        """Check accessibility of dynamically loaded content"""
        issues = []
        
        # Check for new focusable elements without proper focus management
        new_focusable = await page.query_selector_all('a, button, input, [tabindex]')
        for element in new_focusable[-5:]:  # Check last 5 new elements
            has_focus_indicator = await element.evaluate('''
                el => {
                    const style = getComputedStyle(el);
                    return style.outline !== 'none' || style.boxShadow !== 'none';
                }
            ''')
            if not has_focus_indicator:
                issues.append("New dynamic content lacks focus indicators")
                break
        
        return issues
    
    async def _check_error_accessibility(self, error_elements: List) -> bool:
        """Check if error messages are accessible"""
        if not error_elements:
            return False
        
        for error in error_elements:
            # Check if error is announced to screen readers
            has_aria_live = await error.evaluate('el => el.getAttribute("aria-live") === "assertive"')
            has_role_alert = await error.evaluate('el => el.getAttribute("role") === "alert"')
            
            if has_aria_live or has_role_alert:
                return True
        
        return False
    
    async def _find_modal_trigger(self, page: Page, modal):
        """Find the trigger element for a modal"""
        modal_id = await modal.get_attribute('id')
        if modal_id:
            return await page.query_selector(f'[aria-controls="{modal_id}"], [data-target="#{modal_id}"]')
        return None
    
    async def _monitor_dom_changes(self, page: Page) -> Dict[str, Any]:
        """Monitor DOM for changes during interactions"""
        # This would be implemented with MutationObserver in a real scenario
        # For now, return basic metrics
        return {
            "ajax_requests": 0,  # Would be detected via network monitoring
            "dom_modifications": 0  # Would be detected via MutationObserver
        }