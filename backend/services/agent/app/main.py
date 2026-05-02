from fastapi import FastAPI, BackgroundTasks
from common.schemas.audit import AuditRequest, AuditTask
from app.services.audit_service import audit_service
from app.services.agent_logic import agent_intelligence
import uuid
import httpx
import os

app = FastAPI(title="OpenClaw Agent Service")

REPORTING_SERVICE_URL = os.getenv("REPORTING_SERVICE_URL", "http://reporting:8000")

@app.post("/audit", response_model=AuditTask)
async def start_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(orchestrate_agent_audit, task_id, request)
    return AuditTask(task_id=task_id, status="processing")

async def orchestrate_agent_audit(task_id: str, request: AuditRequest):
    try:
        # 1. Execute the Technical Audit (Axe-core)
        raw_result = await audit_service.run_audit(request)
        
        # 2. Apply Agent Intelligence (AI Remediation)
        refined_result = await agent_intelligence.analyze_violations(raw_result)
        
        # 3. Send to Reporting Service
        async with httpx.AsyncClient() as client:
            # Use model_dump(mode='json') to ensure complex types are serialized
            report_data = refined_result.model_dump(mode='json')
            await client.post(f"{REPORTING_SERVICE_URL}/generate", json=report_data)
            
        print(f"Task {task_id} completed successfully.")
    except Exception as e:
        print(f"Error in task {task_id}: {str(e)}")

@app.get("/status/{task_id}", response_model=AuditTask)
async def get_status(task_id: str):
    return AuditTask(task_id=task_id, status="completed")
