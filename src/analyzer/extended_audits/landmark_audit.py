# src/analyzer/extended_audits/landmark_audit.py
import asyncio
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from typing import List, Dict
from .base_audit import BaseAudit
from ..models.extended_audit_models import LandmarkDefect, LandmarkType, SeverityLevel

class LandmarkAudit(BaseAudit):
    async def run_audit(self) -> List[LandmarkDefect]:
        """Check for proper landmark structure and return defects"""
        defects = []
        
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
            
            landmark_counts: Dict[LandmarkType, int] = {}
            
            for landmark_type, selector in landmark_selectors.items():
                try:
                    elements = self._find_elements_safe(selector)
                    landmark_counts[landmark_type] = len(elements)
                    
                    for element in elements:
                        try:
                            element_defects = await self._check_landmark_element(element, landmark_type)
                            defects.extend(element_defects)
                        except StaleElementReferenceException:
                            self.logger.debug(f"Stale landmark element {landmark_type}, skipping...")
                            continue
                        except Exception as e:
                            self.logger.warning(f"Failed to process landmark {landmark_type}: {e}")
                            continue
                            
                except Exception as e:
                    self.logger.warning(f"Failed to process landmark selector {selector}: {e}")
                    continue
            
            # Check for structural defects
            structural_defects = await self._check_structural_issues(landmark_counts)
            defects.extend(structural_defects)
            
            self.logger.info(f"Landmark audit: found {len(defects)} defects across {len(landmark_counts)} landmark types")
            
        except Exception as e:
            self.logger.error(f"Landmark check failed: {e}")
        
        return defects
    
    async def _check_landmark_element(self, element, landmark_type: LandmarkType) -> List[LandmarkDefect]:
        """Check individual landmark element and return defects"""
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
            
            description = self._get_element_description(element)
            
            # Check if landmark has a label
            has_label = bool(self._safe_execute(lambda el: el.get_attribute('aria-label'), element) or 
                           self._safe_execute(lambda el: el.get_attribute('aria-labelledby'), element))
            
            label_text = self._safe_execute(lambda el: el.get_attribute('aria-label'), element)
            
            # Check for uniqueness (we'll check this in structural issues)
            
            # Landmark-specific checks
            if not has_label:
                if landmark_type in [LandmarkType.REGION, LandmarkType.FORM, LandmarkType.COMPLEMENTARY]:
                    defects.append(LandmarkDefect(
                        landmark_type=landmark_type,
                        element_description=description,
                        issue="Landmark missing accessible label",
                        severity=SeverityLevel.MEDIUM,
                        recommendation="Add aria-label or aria-labelledby to describe landmark purpose",
                        selector=selector
                    ))
            
            # Check if landmark is properly nested
            nesting_issue = await self._check_landmark_nesting(element, landmark_type)
            if nesting_issue:
                defects.append(LandmarkDefect(
                    landmark_type=landmark_type,
                    element_description=description,
                    issue=nesting_issue,
                    severity=SeverityLevel.LOW,
                    recommendation="Ensure proper landmark nesting according to ARIA specifications",
                    selector=selector
                ))
            
            # Check if landmark has meaningful content
            has_content = await self._landmark_has_content(element)
            if not has_content and landmark_type != LandmarkType.FORM:
                defects.append(LandmarkDefect(
                    landmark_type=landmark_type,
                    element_description=description,
                    issue="Landmark appears to be empty or lacks meaningful content",
                    severity=SeverityLevel.LOW,
                    recommendation="Ensure landmark contains relevant content or consider removing it",
                    selector=selector
                ))
            
        except StaleElementReferenceException:
            self.logger.debug("Element became stale during landmark checking")
        except Exception as e:
            self.logger.warning(f"Failed to check landmark element: {e}")
        
        return defects
    
    async def _check_structural_issues(self, landmark_counts: Dict[LandmarkType, int]) -> List[LandmarkDefect]:
        """Check for structural landmark issues"""
        defects = []
        
        try:
            # Check for missing main landmark
            if LandmarkType.MAIN not in landmark_counts or landmark_counts[LandmarkType.MAIN] == 0:
                defects.append(LandmarkDefect(
                    landmark_type=LandmarkType.MAIN,
                    element_description="Page structure",
                    issue="Missing main landmark",
                    severity=SeverityLevel.HIGH,
                    recommendation="Add <main> element or role='main' to identify main content area"
                ))
            
            # Check for multiple banners
            if landmark_counts.get(LandmarkType.BANNER, 0) > 1:
                defects.append(LandmarkDefect(
                    landmark_type=LandmarkType.BANNER,
                    element_description="Page structure",
                    issue="Multiple banner landmarks found",
                    severity=SeverityLevel.MEDIUM,
                    recommendation="Ensure only one banner landmark per page"
                ))
            
            # Check for multiple contentinfo
            if landmark_counts.get(LandmarkType.CONTENTINFO, 0) > 1:
                defects.append(LandmarkDefect(
                    landmark_type=LandmarkType.CONTENTINFO,
                    element_description="Page structure",
                    issue="Multiple contentinfo landmarks found",
                    severity=SeverityLevel.MEDIUM,
                    recommendation="Ensure only one contentinfo landmark per page"
                ))
            
            # Check for navigation landmarks without labels when multiple exist
            if landmark_counts.get(LandmarkType.NAVIGATION, 0) > 1:
                defects.append(LandmarkDefect(
                    landmark_type=LandmarkType.NAVIGATION,
                    element_description="Page structure",
                    issue="Multiple navigation landmarks without distinguishing labels",
                    severity=SeverityLevel.MEDIUM,
                    recommendation="Add aria-label to distinguish between multiple navigation landmarks"
                ))
            
        except Exception as e:
            self.logger.warning(f"Failed to check structural issues: {e}")
        
        return defects
    
    async def _check_landmark_nesting(self, element, landmark_type: LandmarkType) -> str:
        """Check if landmark is properly nested"""
        try:
            tag_name = self._safe_execute(lambda el: el.tag_name.lower(), element)
            role = self._safe_execute(lambda el: el.get_attribute('role'), element)
            
            # Check for inappropriate nesting
            if landmark_type == LandmarkType.BANNER and tag_name != 'header':
                return "Banner role used on non-header element"
            
            if landmark_type == LandmarkType.CONTENTINFO and tag_name != 'footer':
                return "Contentinfo role used on non-footer element"
            
            # Check for landmark inside landmark (some are allowed, some aren't)
            parent_landmark = self._safe_execute(
                lambda el: el.find_element(By.XPATH, "./ancestor::*[@role]"), 
                element
            )
            
            if parent_landmark:
                parent_role = self._safe_execute(lambda el: el.get_attribute('role'), parent_landmark)
                if parent_role in ['banner', 'main', 'contentinfo'] and landmark_type.value in ['banner', 'main', 'contentinfo']:
                    return f"Landmark {landmark_type.value} nested inside {parent_role} landmark"
            
            return ""
            
        except Exception:
            return ""
    
    async def _landmark_has_content(self, element) -> bool:
        """Check if landmark has meaningful content"""
        try:
            # Use JavaScript to check for visible content
            selector = self._get_element_selector(element)
            if not selector:
                return False
            
            content_check_script = f"""
            var element = document.querySelector('{selector}');
            if (!element) return false;
            
            // Get all text content
            var textContent = element.textContent || '';
            var visibleText = textContent.replace(/\\s+/g, ' ').trim();
            
            // Check for child elements
            var hasChildren = element.children.length > 0;
            
            // Check for images with alt text
            var images = element.getElementsByTagName('img');
            var hasMeaningfulImages = false;
            for (var i = 0; i < images.length; i++) {{
                if (images[i].alt && images[i].alt.trim().length > 0) {{
                    hasMeaningfulImages = true;
                    break;
                }}
            }}
            
            return visibleText.length > 0 || hasChildren || hasMeaningfulImages;
            """
            
            result = self.driver.execute_script(content_check_script)
            return bool(result)
            
        except Exception:
            return False