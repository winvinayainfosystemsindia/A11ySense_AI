from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from src.crawler.playwright_crawler import PlaywrightCrawler
from src.utils.config_manager import ConfigManager
import asyncio

app = FastAPI(title="A11ySense AI Crawler Service")
config_manager = ConfigManager("config/config.yaml")

class CrawlRequest(BaseModel):
    url: str
    max_pages: int = None
    max_depth: int = None

class CrawlResponse(BaseModel):
    urls: List[str]
    count: int

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "crawler"}

@app.post("/crawl", response_model=CrawlResponse)
async def run_crawl(request: CrawlRequest):
    config = config_manager.config.copy()
    if request.max_pages:
        config['website']['max_pages'] = request.max_pages
    if request.max_depth:
        config['crawler']['max_depth'] = request.max_depth

    crawler = PlaywrightCrawler(config)
    try:
        urls = await crawler.crawl(request.url)
        return CrawlResponse(urls=urls, count=len(urls))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await crawler.close()
