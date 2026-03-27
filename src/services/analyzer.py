from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from src.analyzer.audit_runner import AuditRunner
from src.utils.config_manager import ConfigManager

app = FastAPI(title="A11ySense AI Analyzer Service")
config_manager = ConfigManager("config/config.yaml")

class AuditRequest(BaseModel):
    urls: List[str]
    audit_type: str = "basic" # basic or comprehensive

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "analyzer"}

@app.post("/audit")
async def run_audit(request: AuditRequest):
    config = config_manager.config
    try:
        runner = AuditRunner(config)
        # Note: In a real microservice, we might want to handle comprehensive 
        # via the IntegratedAuditRunner or a separate service.
        # For now, we'll keep it simple.
        if request.audit_type == "comprehensive":
            from src.analyzer.integrated_audit_runner import IntegratedAuditRunner
            runner = IntegratedAuditRunner(config)
            results = await runner.run_comprehensive_audit(request.urls)
        else:
            results = await runner.run_audit(request.urls)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
