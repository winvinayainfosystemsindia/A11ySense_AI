import uuid
import time
import json
import os
from typing import List, Dict, Any
from common.schemas.audit import AuditResult, Violation

class AllureManager:
    """
    Manages the creation of industry-standard Allure reports.
    Follows a structured approach: Scenarios -> Test Cases -> Execution Steps -> Defect Reports.
    """
    
    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

    def map_severity(self, severity: str) -> str:
        mapping = {
            "critical": "blocker",
            "high": "critical",
            "medium": "normal",
            "low": "minor"
        }
        return mapping.get(severity.lower(), "normal")

    def generate_allure_json(self, result: AuditResult) -> str:
        task_id = str(uuid.uuid4())
        # Use a stable start time for Allure
        start_time = int(time.time() * 1000)
        
        # 1. Create Environment Metadata
        self._write_environment_properties(result)

        # 2. Build the main test result
        allure_result = {
            "uuid": task_id,
            "historyId": f"{result.url}-audit",
            "name": f"Accessibility Audit: {result.metadata.get('page_title', result.url)}",
            "status": "failed" if result.violations else "passed",
            "statusDetails": {
                "message": f"Audit Summary: {len(result.violations)} Violations | {len(result.passes or [])} Passed"
            },
            "stage": "finished",
            "steps": [],
            "attachments": [],
            "parameters": [
                {"name": "Target URL", "value": str(result.url)},
                {"name": "Page Title", "value": str(result.metadata.get("page_title", "Unknown"))}
            ],
            "labels": [
                {"name": "feature", "value": "Compliance Audit"},
                {"name": "epic", "value": "Enterprise Accessibility"},
                {"name": "story", "value": "WCAG 2.2 Standards Verification"},
                {"name": "suite", "value": "A11ySense Audit Suite"},
                {"name": "subSuite", "value": result.url},
                {"name": "owner", "value": "A11ySense-Reporting-Service"}
            ],
            "links": [{"name": "Audited Page", "url": str(result.url)}],
            "start": start_time,
            "stop": start_time + 5000
        }

        # 3. Scenario 1: Automated Compliance Verification (Passes)
        if result.passes:
            pass_scenario = self._build_scenario_step(
                "Scenario: Automated Compliance Verification", 
                "Verifying page elements against automated WCAG rules.",
                result.passes, 
                "passed",
                start_time
            )
            allure_result["steps"].append(pass_scenario)

        # 4. Scenario 2: Accessibility Defect Reporting (Failures)
        if result.violations:
            fail_scenario = self._build_defect_scenario(
                "Scenario: Accessibility Defect Reporting",
                "Identifying and documenting barriers for assistive technology users.",
                result.violations,
                start_time
            )
            allure_result["steps"].append(fail_scenario)

        # 5. Save and Return
        result_path = os.path.join(self.results_dir, f"{task_id}-result.json")
        with open(result_path, "w") as f:
            json.dump(allure_result, f, indent=4)
            
        self._attach_raw_data(allure_result, result, result_path)
        
        return task_id

    def _build_scenario_step(self, name: str, description: str, items: List[Any], status: str, start_time: int) -> Dict[str, Any]:
        """Builds a high-level test scenario step."""
        scenario = {
            "name": name,
            "status": status,
            "statusDetails": {"message": str(description)},
            "steps": [],
            "start": start_time,
            "stop": start_time + 100
        }
        for item in items:
            # Safely handle items which could be dicts or objects
            item_help = item.get('help', item.get('id')) if isinstance(item, dict) else getattr(item, 'help', getattr(item, 'id', 'Unknown'))
            item_desc = item.get('description', 'Standard followed.') if isinstance(item, dict) else getattr(item, 'description', 'Standard followed.')
            
            scenario["steps"].append({
                "name": f"Test Case: {item_help}",
                "status": status,
                "statusDetails": {"message": str(item_desc)},
                "start": start_time,
                "stop": start_time + 10
            })
        return scenario

    def _build_defect_scenario(self, name: str, description: str, violations: List[Violation], start_time: int) -> Dict[str, Any]:
        """Builds a defect-heavy scenario step with full execution details."""
        scenario = {
            "name": name,
            "status": "failed",
            "statusDetails": {"message": str(description)},
            "steps": [],
            "start": start_time,
            "stop": start_time + 1000
        }
        
        for v in violations:
            # Safety check: if remediation or other AI data is a dict, stringify it
            wcag_info = v.metadata.get('wcag_criteria', 'N/A')
            exp_res = v.metadata.get('expected_result', '')
            act_res = v.metadata.get('actual_result', '')
            repro = v.metadata.get('steps_to_reproduce', '')
            remedy = v.metadata.get('remediation', '')

            # Convert to string if they are complex objects
            if not isinstance(remedy, str): remedy = json.dumps(remedy, indent=2)
            if not isinstance(repro, str): repro = json.dumps(repro, indent=2)
            if not isinstance(act_res, str): act_res = json.dumps(act_res, indent=2)

            test_case = {
                "name": f"Test Case: {v.metadata.get('friendly_name', v.id)}",
                "status": "failed",
                "steps": [
                    {
                        "name": "Execution: Contextual Analysis",
                        "status": "passed",
                        "statusDetails": {"message": f"WCAG: {wcag_info} (Level {v.metadata.get('wcag_level', 'AA')})"},
                        "start": start_time, "stop": start_time + 5
                    },
                    {
                        "name": "Execution: Experience Gap Identification",
                        "status": "failed",
                        "statusDetails": {"message": f"Expected: {exp_res}\nActual: {act_res}"},
                        "start": start_time, "stop": start_time + 5
                    },
                    {
                        "name": "Defect Report: Reproduction Steps",
                        "status": "passed",
                        "statusDetails": {"message": str(repro)},
                        "start": start_time, "stop": start_time + 5
                    },
                    {
                        "name": "Defect Report: Remediation Strategy",
                        "status": "passed",
                        "statusDetails": {"message": str(remedy)},
                        "start": start_time, "stop": start_time + 5
                    }
                ],
                "start": start_time,
                "stop": start_time + 100
            }
            scenario["steps"].append(test_case)
            
        return scenario

    def _write_environment_properties(self, result: AuditResult):
        env_path = os.path.join(self.results_dir, "environment.properties")
        with open(env_path, "w") as f:
            f.write(f"Auditor.Platform=A11ySense Enterprise\n")
            f.write(f"Auditor.Engine=Axe-Core\n")
            f.write(f"Audit.URL={result.url}\n")
            f.write(f"Audit.Timestamp={result.timestamp.isoformat()}\n")

    def _attach_raw_data(self, allure_result: Dict, result: AuditResult, result_path: str):
        attachment_id = str(uuid.uuid4())
        attachment_path = os.path.join(self.results_dir, f"{attachment_id}-attachment.json")
        with open(attachment_path, "w") as f:
            json.dump(result.model_dump(mode='json'), f, indent=4)
        
        allure_result["attachments"].append({
            "name": "Full Technical Evidence",
            "source": f"{attachment_id}-attachment.json",
            "type": "application/json"
        })
        
        with open(result_path, "w") as f:
            json.dump(allure_result, f, indent=4)
