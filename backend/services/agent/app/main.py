import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from common.config import setup_environment
# Initialize environment
setup_environment()

from fastapi import FastAPI, BackgroundTasks
from common.schemas.audit import AuditRequest, AuditTask
from app.services.audit_service import audit_service
from app.services.agent_logic import agent_intelligence
import uuid
import httpx
import os

app = FastAPI(title="OpenClaw Agent Service")

REPORTING_SERVICE_URL = os.getenv("REPORTING_SERVICE_URL", "http://localhost:8002")

from app.agents.manager import ManagerAgent
manager_agent = ManagerAgent()

@app.post("/audit", response_model=AuditTask)
async def start_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(orchestrate_agent_audit, task_id, request)
    return AuditTask(task_id=task_id, status="processing")

async def orchestrate_agent_audit(task_id: str, request: AuditRequest):
    try:
        # Execute the Multi-Agent Audit
        refined_result = await manager_agent.run_audit(request)
        
        # Send to Reporting Service
        async with httpx.AsyncClient() as client:
            report_data = refined_result.model_dump(mode='json')
            await client.post(f"{REPORTING_SERVICE_URL}/generate", json=report_data)
            
        print(f"Task {task_id} completed successfully.")
    except Exception as e:
        print(f"Error in task {task_id}: {str(e)}")

@app.get("/status/{task_id}", response_model=AuditTask)
async def get_status(task_id: str):
    return AuditTask(task_id=task_id, status="completed")
