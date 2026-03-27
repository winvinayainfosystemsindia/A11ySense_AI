from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
import asyncio
import os
import uuid

app = FastAPI(title="A11ySense AI Gateway")

# Service URLs (would normally be in config/env)
SERVICES = {
    "crawler": "http://127.0.0.1:8001",
    "analyzer": "http://127.0.0.1:8002",
    "llm": "http://127.0.0.1:8003",
    "reporting": "http://127.0.0.1:8004",
}

class AuditJob(BaseModel):
    url: str
    audit_type: str = "comprehensive"
    max_pages: int = 10
    max_depth: int = 3

# Simple in-memory task tracking
tasks = {}

async def run_audit_flow(task_id: str, job: AuditJob):
    tasks[task_id] = {"status": "starting", "url": job.url}
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            # 1. Crawl
            tasks[task_id]["status"] = "crawling"
            crawl_resp = await client.post(f"{SERVICES['crawler']}/crawl", json={
                "url": job.url,
                "max_pages": job.max_pages,
                "max_depth": job.max_depth
            })
            crawl_resp.raise_for_status()
            urls = crawl_resp.json()["urls"]
            tasks[task_id]["urls_found"] = len(urls)

            # 2. Audit
            tasks[task_id]["status"] = "auditing"
            audit_resp = await client.post(f"{SERVICES['analyzer']}/audit", json={
                "urls": urls,
                "audit_type": job.audit_type
            })
            audit_resp.raise_for_status()
            audit_results = audit_resp.json()

            # 3. LLM Analysis (if comprehensive)
            if job.audit_type == "comprehensive":
                tasks[task_id]["status"] = "llm_analyzing"
                try:
                    llm_resp = await client.post(f"{SERVICES['llm']}/analyze", json={
                        "audit_results": audit_results
                    })
                    llm_resp.raise_for_status()
                    audit_results["llm_analysis"] = llm_resp.json()["analysis"]
                except Exception as e:
                    tasks[task_id]["llm_error"] = str(e)

            # 4. Report Generation
            tasks[task_id]["status"] = "reporting"
            report_resp = await client.post(f"{SERVICES['reporting']}/generate", json={
                "audit_data": audit_results,
                "report_type": job.audit_type
            })
            report_resp.raise_for_status()
            report_paths = report_resp.json()["output_paths"]

            tasks[task_id]["status"] = "completed"
            tasks[task_id]["report_paths"] = report_paths
            
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)

@app.post("/start_audit")
async def start_audit(job: AuditJob, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "starting", "url": job.url}
    background_tasks.add_task(run_audit_flow, task_id, job)
    return {"task_id": task_id, "message": "Audit started in background"}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gateway"}
