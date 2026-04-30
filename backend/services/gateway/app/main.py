from fastapi import FastAPI, HTTPException
from common.schemas.audit import AuditRequest, AuditTask
import httpx
import os

app = FastAPI(title="A11ySense AI Gateway")

AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent:8000")
REPORTING_SERVICE_URL = os.getenv("REPORTING_SERVICE_URL", "http://reporting:8000")

@app.post("/start_audit", response_model=AuditTask)
async def start_audit(request: AuditRequest):
    async with httpx.AsyncClient() as client:
        try:
            # 1. Trigger the Agent (OpenClaw)
            response = await client.post(f"{AGENT_SERVICE_URL}/audit", json=request.dict())
            response.raise_for_status()
            return AuditTask(**response.json())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}", response_model=AuditTask)
async def get_task_status(task_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AGENT_SERVICE_URL}/status/{task_id}")
            response.raise_for_status()
            return AuditTask(**response.json())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
