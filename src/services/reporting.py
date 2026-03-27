from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from src.analyzer.result_processor import ResultProcessor
from src.utils.config_manager import ConfigManager

app = FastAPI(title="A11ySense AI Reporting Service")
config_manager = ConfigManager("config/config.yaml")

class ReportRequest(BaseModel):
    audit_data: Dict[str, Any]
    report_type: str = "basic" # basic or comprehensive

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "reporting"}

@app.post("/generate")
async def generate_report(request: ReportRequest):
    config = config_manager.config
    try:
        processor = ResultProcessor(config)
        if request.report_type == "comprehensive":
            paths = processor.save_comprehensive_results(request.audit_data)
        else:
            paths = processor.save_audit_results(request.audit_data)
        
        return {"output_paths": paths}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
