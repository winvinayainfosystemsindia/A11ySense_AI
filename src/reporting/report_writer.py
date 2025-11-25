# src/utils/report_writer.py
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from ..utils.logger import setup_logger

class ReportWriter:
    def __init__(self, base_output_dir: str = "storage/reports"):
        self.base_output_dir = Path(base_output_dir)
        self.json_dir = self.base_output_dir / "json"
        self.excel_dir = self.base_output_dir / "excel"
        self.logger = setup_logger(__name__)
        
        # Create directories
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.excel_dir.mkdir(parents=True, exist_ok=True)
    
    def save_json_report(self, data: Dict[str, Any], filename: str, 
                        timestamp: bool = True) -> str:
        """
        Save data as JSON report
        
        Args:
            data: Data to save as JSON
            filename: Base filename (without extension)
            timestamp: Whether to append timestamp to filename
            
        Returns:
            Path to the saved JSON file
        """
        try:
            # Generate filename
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp_str}.json"
            else:
                filename = f"{filename}.json"
            
            file_path = self.json_dir / filename
            
            # Make sure data is JSON serializable
            serializable_data = self._make_serializable(data)
            
            # Save as JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON report saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save JSON report: {e}")
            raise
    
    def save_excel_report(self, data: Dict[str, Any], filename: str,
                         timestamp: bool = True) -> str:
        """
        Save data as Excel report with multiple sheets
        
        Args:
            data: Data to save as Excel (can contain multiple DataFrames)
            filename: Base filename (without extension)
            timestamp: Whether to append timestamp to filename
            
        Returns:
            Path to the saved Excel file
        """
        try:
            # Generate filename
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp_str}.xlsx"
            else:
                filename = f"{filename}.xlsx"
            
            file_path = self.excel_dir / filename
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Process different types of data
                if isinstance(data, dict):
                    self._process_dict_data(data, writer)
                elif isinstance(data, list):
                    self._process_list_data(data, writer, filename)
                else:
                    # Convert single object to DataFrame
                    df = self._convert_to_dataframe(data, "Summary")
                    df.to_excel(writer, sheet_name="Summary", index=False)
            
            self.logger.info(f"Excel report saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save Excel report: {e}")
            raise
    
    def save_comprehensive_audit_report(self, audit_data: Dict[str, Any], 
                                      filename: str) -> Dict[str, str]:
        """
        Save comprehensive audit report in both JSON and Excel formats
        
        Args:
            audit_data: Comprehensive audit data
            filename: Base filename (without extension)
            
        Returns:
            Dictionary with paths to saved files
        """
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{filename}_{timestamp_str}"
        
        json_path = self.save_json_report(audit_data, base_filename, timestamp=False)
        excel_path = self.save_excel_report(audit_data, base_filename, timestamp=False)
        
        return {
            'json': json_path,
            'excel': excel_path
        }
    
    def _process_dict_data(self, data: Dict[str, Any], writer: pd.ExcelWriter):
        """Process dictionary data for Excel export"""
        for sheet_name, sheet_data in data.items():
            if isinstance(sheet_data, (list, dict)):
                df = self._convert_to_dataframe(sheet_data, sheet_name)
                # Truncate sheet name if too long (Excel limit: 31 characters)
                safe_sheet_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
    
    def _process_list_data(self, data: List[Any], writer: pd.ExcelWriter, filename: str):
        """Process list data for Excel export"""
        if data and isinstance(data[0], dict):
            df = self._convert_to_dataframe(data, filename)
            df.to_excel(writer, sheet_name="Data", index=False)
        else:
            # Simple list
            df = pd.DataFrame(data, columns=["Items"])
            df.to_excel(writer, sheet_name="Data", index=False)
    
    def _convert_to_dataframe(self, data: Any, sheet_name: str) -> pd.DataFrame:
        """Convert various data types to pandas DataFrame"""
        try:
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    return pd.DataFrame(data)
                else:
                    return pd.DataFrame(data, columns=[sheet_name])
            elif isinstance(data, dict):
                # Flatten nested dictionaries
                flattened_data = self._flatten_dict(data)
                return pd.DataFrame([flattened_data])
            else:
                return pd.DataFrame([{"Value": str(data)}])
        except Exception as e:
            self.logger.warning(f"Failed to convert data to DataFrame for {sheet_name}: {e}")
            return pd.DataFrame([{"Error": "Failed to process data"}])
    
    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', 
                     sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for Excel export"""
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to string for Excel
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable formats"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        elif hasattr(obj, '__dict__'):
            # Convert objects to dict
            return self._make_serializable(obj.__dict__)
        else:
            # Convert to string as fallback
            return str(obj)
    
    def generate_audit_excel_report(self, audit_report: Dict[str, Any], 
                                  filename: str) -> str:
        """
        Generate a comprehensive Excel report specifically for audit results
        
        Args:
            audit_report: Audit report data
            filename: Base filename
            
        Returns:
            Path to saved Excel file
        """
        try:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp_str}.xlsx"
            file_path = self.excel_dir / filename
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Summary Sheet
                if 'summary' in audit_report:
                    summary_data = self._prepare_summary_data(audit_report['summary'])
                    summary_df = pd.DataFrame([summary_data])
                    summary_df.to_excel(writer, sheet_name="Summary", index=False)
                
                # Detailed Violations Sheet
                if 'page_results' in audit_report:
                    violations_data = self._prepare_detailed_violations_data(audit_report['page_results'])
                    if violations_data:
                        violations_df = pd.DataFrame(violations_data)
                        violations_df.to_excel(writer, sheet_name="Violations_Detailed", index=False)
                
                # Extended Audit Defects Sheet
                if 'page_results' in audit_report:
                    extended_defects_data = self._prepare_extended_defects_data(audit_report['page_results'])
                    if extended_defects_data:
                        extended_df = pd.DataFrame(extended_defects_data)
                        extended_df.to_excel(writer, sheet_name="Extended_Defects", index=False)
                
                # Page Results Sheet
                if 'page_results' in audit_report:
                    page_results_data = self._prepare_page_results_data(audit_report['page_results'])
                    if page_results_data:
                        page_results_df = pd.DataFrame(page_results_data)
                        page_results_df.to_excel(writer, sheet_name="Page_Results", index=False)
                
                # Violations Summary Sheet
                if 'page_results' in audit_report:
                    violations_summary_data = self._prepare_violations_summary_data(audit_report['page_results'])
                    if violations_summary_data:
                        violations_summary_df = pd.DataFrame(violations_summary_data)
                        violations_summary_df.to_excel(writer, sheet_name="Violations_Summary", index=False)
            
            self.logger.info(f"Comprehensive audit Excel report saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate audit Excel report: {e}")
            raise
    
    def _prepare_summary_data(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare summary data for Excel export"""
        summary_data = {}
        
        # Basic metrics
        basic_metrics = ['total_pages', 'pages_audited', 'total_violations', 
                        'average_score', 'audit_duration']
        for metric in basic_metrics:
            if metric in summary:
                summary_data[metric] = summary[metric]
        
        # Extended defects
        if 'total_extended_defects' in summary:
            summary_data['total_extended_defects'] = summary['total_extended_defects']
        
        # Violations by level
        if 'violations_by_level' in summary:
            for level, count in summary['violations_by_level'].items():
                summary_data[f'violations_{level}'] = count
        
        # Extended defects by category
        if 'extended_defects_by_category' in summary:
            for category, count in summary['extended_defects_by_category'].items():
                summary_data[f'defects_{category}'] = count
        
        return summary_data
    
    def _prepare_detailed_violations_data(self, page_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare detailed violations data for Excel export with page info"""
        violations_data = []
        
        for page in page_results:
            url = page.get('url', 'Unknown')
            page_title = page.get('page_title', 'Unknown')
            testing_mode = "Automation"  # Default testing mode
            
            if 'violations' in page:
                for violation in page['violations']:
                    violation_data = {
                        'page_url': url,
                        'page_title': page_title,
                        'testing_mode': testing_mode,
                        'violation_id': violation.get('id', ''),
                        'violation_impact': violation.get('impact', ''),
                        'violation_level': violation.get('level', ''),
                        'violation_description': violation.get('description', ''),
                        'violation_help': violation.get('help', ''),
                        'violation_help_url': violation.get('help_url', ''),
                        'nodes_affected': len(violation.get('nodes', [])),
                        'wcag_criteria': self._extract_wcag_criteria(violation),
                        'element_selectors': self._extract_element_selectors(violation),
                        'recommendation': self._generate_recommendation(violation)
                    }
                    violations_data.append(violation_data)
        
        return violations_data
    
    def _prepare_violations_summary_data(self, page_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare violations summary data grouped by violation type"""
        violations_summary = {}
        
        for page in page_results:
            if 'violations' in page:
                for violation in page['violations']:
                    violation_id = violation.get('id', 'unknown')
                    if violation_id not in violations_summary:
                        violations_summary[violation_id] = {
                            'violation_id': violation_id,
                            'violation_description': violation.get('description', ''),
                            'violation_impact': violation.get('impact', ''),
                            'violation_level': violation.get('level', ''),
                            'total_occurrences': 0,
                            'pages_affected': set(),
                            'total_elements_affected': 0,
                            'help_url': violation.get('help_url', '')
                        }
                    
                    violations_summary[violation_id]['total_occurrences'] += 1
                    violations_summary[violation_id]['pages_affected'].add(page.get('url', 'Unknown'))
                    violations_summary[violation_id]['total_elements_affected'] += len(violation.get('nodes', []))
        
        # Convert to list and format pages_affected
        summary_data = []
        for violation in violations_summary.values():
            summary_data.append({
                'violation_id': violation['violation_id'],
                'violation_description': violation['violation_description'],
                'violation_impact': violation['violation_impact'],
                'violation_level': violation['violation_level'],
                'total_occurrences': violation['total_occurrences'],
                'pages_affected_count': len(violation['pages_affected']),
                'total_elements_affected': violation['total_elements_affected'],
                'help_url': violation['help_url']
            })
        
        return summary_data
    
    def _prepare_extended_defects_data(self, page_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare extended defects data for Excel export"""
        defects_data = []
        
        for page in page_results:
            url = page.get('url', 'Unknown')
            page_title = page.get('page_title', 'Unknown')
            testing_mode = "Automation"
            extended_audit = page.get('extended_audit', {})
            
            # Keyboard defects
            for defect in extended_audit.get('keyboard_defects', []):
                defect_data = {
                    'page_url': url,
                    'page_title': page_title,
                    'testing_mode': testing_mode,
                    'defect_type': 'keyboard',
                    'element_type': defect.get('element_type', ''),
                    'element_description': defect.get('element_description', ''),
                    'issue': defect.get('issue', ''),
                    'severity': defect.get('severity', ''),
                    'recommendation': defect.get('recommendation', ''),
                    'selector': defect.get('selector', '')
                }
                defects_data.append(defect_data)
            
            # Screen reader defects
            for defect in extended_audit.get('screen_reader_defects', []):
                defect_data = {
                    'page_url': url,
                    'page_title': page_title,
                    'testing_mode': testing_mode,
                    'defect_type': 'screen_reader',
                    'element_type': defect.get('element_type', ''),
                    'element_description': defect.get('element_description', ''),
                    'issue': defect.get('issue', ''),
                    'severity': defect.get('severity', ''),
                    'recommendation': defect.get('recommendation', ''),
                    'selector': defect.get('selector', '')
                }
                defects_data.append(defect_data)
            
            # Landmark defects
            for defect in extended_audit.get('landmark_defects', []):
                defect_data = {
                    'page_url': url,
                    'page_title': page_title,
                    'testing_mode': testing_mode,
                    'defect_type': 'landmark',
                    'landmark_type': defect.get('landmark_type', ''),
                    'element_description': defect.get('element_description', ''),
                    'issue': defect.get('issue', ''),
                    'severity': defect.get('severity', ''),
                    'recommendation': defect.get('recommendation', ''),
                    'selector': defect.get('selector', '')
                }
                defects_data.append(defect_data)
            
            # Skip link defects
            for defect in extended_audit.get('skip_link_defects', []):
                defect_data = {
                    'page_url': url,
                    'page_title': page_title,
                    'testing_mode': testing_mode,
                    'defect_type': 'skip_link',
                    'issue': defect.get('issue', ''),
                    'severity': defect.get('severity', ''),
                    'recommendation': defect.get('recommendation', ''),
                    'target_id': defect.get('target_id', '')
                }
                defects_data.append(defect_data)
        
        return defects_data
    
    def _prepare_page_results_data(self, page_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare detailed page results for Excel export"""
        detailed_data = []
        
        for page in page_results:
            page_data = {
                'page_url': page.get('url', ''),
                'page_title': page.get('page_title', 'Unknown'),
                'testing_mode': 'Automation',
                'accessibility_score': page.get('score', 0),
                'total_violations': page.get('violation_count', 0),
                'load_time_seconds': page.get('load_time', 0),
                'error_message': page.get('error', ''),
                'audit_timestamp': page.get('timestamp', '')
            }
            
            # Add violations breakdown
            if 'violations' in page:
                violations_by_level = {}
                for violation in page['violations']:
                    level = violation.get('level', 'unknown')
                    violations_by_level[level] = violations_by_level.get(level, 0) + 1
                
                for level in ['critical', 'serious', 'moderate', 'minor']:
                    page_data[f'violations_{level}'] = violations_by_level.get(level, 0)
            
            # Add extended audit summary
            extended_audit = page.get('extended_audit', {})
            if extended_audit:
                page_data['total_extended_defects'] = extended_audit.get('total_defects', 0)
                page_data['keyboard_defects'] = extended_audit.get('defects_by_category', {}).get('keyboard', 0)
                page_data['screen_reader_defects'] = extended_audit.get('defects_by_category', {}).get('screen_reader', 0)
                page_data['landmark_defects'] = extended_audit.get('defects_by_category', {}).get('landmark', 0)
                page_data['skip_link_defects'] = extended_audit.get('defects_by_category', {}).get('skip_links', 0)
            
            detailed_data.append(page_data)
        
        return detailed_data
    
    def _extract_wcag_criteria(self, violation: Dict[str, Any]) -> str:
        """Extract WCAG criteria from violation tags"""
        tags = violation.get('tags', [])
        wcag_tags = [tag for tag in tags if tag.startswith('wcag')]
        return ', '.join(wcag_tags) if wcag_tags else 'Not specified'
    
    def _extract_element_selectors(self, violation: Dict[str, Any]) -> str:
        """Extract element selectors from violation nodes"""
        nodes = violation.get('nodes', [])
        selectors = []
        
        for node in nodes[:5]:  # Limit to first 5 nodes to avoid overwhelming data
            target = node.get('target', [])
            if target:
                # Take the first selector from the target array
                selectors.append(target[0] if isinstance(target, list) else str(target))
        
        return '; '.join(selectors) if selectors else 'No specific elements'
    
    def _generate_recommendation(self, violation: Dict[str, Any]) -> str:
        """Generate a recommendation based on violation type"""
        violation_id = violation.get('id', '')
        help_text = violation.get('help', '')
        
        recommendations = {
            'empty-heading': 'Add meaningful text content to empty heading elements.',
            'frame-title': 'Add descriptive title attribute to iframe elements.',
            'landmark-one-main': 'Ensure only one main landmark exists per page.',
            'link-name': 'Add descriptive text or aria-label to links.',
            'meta-viewport': 'Ensure viewport meta tag allows zooming and scaling.',
            'page-has-heading-one': 'Add at least one h1 heading to the page.',
            'region': 'Ensure all content is contained within appropriate landmarks.'
        }
        
        return recommendations.get(violation_id, help_text)