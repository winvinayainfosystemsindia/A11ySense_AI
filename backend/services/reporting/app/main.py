from fastapi import FastAPI
from common.schemas.audit import AuditResult, Violation
import os
import json
import uuid
import time

app = FastAPI(title="Reporting Service")

# Use an environment variable for the results directory, fallback to a local relative path
ALLURE_RESULTS_DIR = os.getenv("ALLURE_RESULTS_DIR", "storage/reports/allure-results")

def map_severity(impact: str) -> str:
    mapping = {
        "critical": "blocker",
        "serious": "critical",
        "moderate": "normal",
        "minor": "minor"
    }
    return mapping.get(impact, "normal")

@app.post("/generate")
async def generate_report(result: AuditResult):
    task_id = str(uuid.uuid4())
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
    
    # 1. Prepare Allure Result JSON
    start_time = int(result.timestamp.timestamp() * 1000)
    
    allure_result = {
        "uuid": task_id,
        "historyId": str(uuid.uuid4()),
        "name": f"A11y Audit: {result.metadata.get('page_title', result.url)}",
        "status": "failed" if result.violations else "passed",
        "statusDetails": {
            "message": f"Summary: {len(result.violations)} Violations, {len(result.passes or [])} Passes."
        },
        "stage": "finished",
        "steps": [],
        "attachments": [],
        "parameters": [
            {"name": "Audited URL", "value": str(result.url)},
            {"name": "Page Title", "value": str(result.metadata.get("page_title", "Unknown"))},
            {"name": "Manager Thought", "value": str(result.metadata.get("manager_thought", "Autonomous audit plan."))}
        ],
        "labels": [
            {"name": "feature", "value": "Accessibility Audit"},
            {"name": "epic", "value": "Compliance"},
            {"name": "framework", "value": "A11ySense MAS / OpenClaw"}
        ],
        "links": [],
        "start": start_time,
        "stop": start_time + 5000
    }

    # 2. Add Passes as passed steps
    if result.passes:
        for p in result.passes:
            allure_result["steps"].append({
                "name": f"PASS: {p.get('help', p.get('id'))}",
                "status": "passed",
                "statusDetails": {"message": p.get("description", "Criterion met.")},
                "start": start_time,
                "stop": start_time + 10
            })

    # 3. Add violations as failed steps with detailed data
    for v in result.violations:
        friendly_title = v.metadata.get("friendly_name", v.help)
        wcag_criteria = v.metadata.get("wcag_criteria", "N/A")
        wcag_level = v.metadata.get("wcag_level", "AA")
        severity = v.metadata.get("severity", "Normal")
        impact_desc = v.metadata.get("business_impact", "")
        expected = v.metadata.get("expected_result", "")
        actual = v.metadata.get("actual_result", "")
        steps = v.metadata.get("steps_to_reproduce", "")
        remediation = v.metadata.get("remediation", "")

        allure_result["labels"].append({"name": "severity", "value": map_severity(severity.lower())})
        
        message = (
            f"WCAG CRITERIA: {wcag_criteria} (Level {wcag_level})\n"
            f"USER IMPACT: {impact_desc}\n\n"
            f"EXPECTED: {expected}\n"
            f"ACTUAL: {actual}\n\n"
            f"STEPS TO REPRODUCE:\n{steps}\n\n"
            f"REMEDIATION:\n{remediation}"
        )

        step = {
            "name": f"VIOLATION: {friendly_title}",
            "status": "failed",
            "statusDetails": {
                "message": message,
                "trace": f"Technical ID: {v.id}\nNodes Affected: {len(v.nodes)}"
            },
            "attachments": [],
            "start": start_time,
            "stop": start_time + 100
        }
        allure_result["steps"].append(step)

    # 3. Save Allure Result File
    result_path = os.path.join(ALLURE_RESULTS_DIR, f"{task_id}-result.json")
    with open(result_path, "w") as f:
        json.dump(allure_result, f, indent=4)

    # 4. Save Raw Audit Data as Attachment
    attachment_id = str(uuid.uuid4())
    attachment_path = os.path.join(ALLURE_RESULTS_DIR, f"{attachment_id}-attachment.json")
    with open(attachment_path, "w") as f:
        json.dump(result.dict(), f, indent=4, default=str)
    
    # Register attachment in result
    allure_result["attachments"].append({
        "name": "Raw Audit Data",
        "source": f"{attachment_id}-attachment.json",
        "type": "application/json"
    })
    
    # Re-save with attachment reference
    with open(result_path, "w") as f:
        json.dump(allure_result, f, indent=4)

    return {"status": "success", "task_id": task_id, "report_path": ALLURE_RESULTS_DIR}
