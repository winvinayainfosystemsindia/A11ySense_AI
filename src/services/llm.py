from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from src.llm.groq_client import GroqClient
from src.utils.config_manager import ConfigManager

app = FastAPI(title="A11ySense AI LLM Service")
config_manager = ConfigManager("config/config.yaml")

class LLMRequest(BaseModel):
    audit_results: Dict[str, Any]
    prompt_override: str = None

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "llm"}

@app.post("/analyze")
async def analyze_with_llm(request: LLMRequest):
    config = config_manager.config
    try:
        client = GroqClient(config)
        # Note: GroqClient might need adjustment for direct pass-through
        # if it doesn't already have an analyze_audit_results method.
        # Assuming it handles the core LLM interaction.
        analysis = await client.analyze_audit_results(request.audit_results)
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
