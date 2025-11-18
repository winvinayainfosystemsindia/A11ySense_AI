import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List
from ..utils.logger import setup_logger

@dataclass
class PageMetrics:
    url: str
    load_time: float
    page_size: int
    request_count: int
    success: bool
    error: str = None

class PerformanceMonitor:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
        self.metrics: List[PageMetrics] = []
        self.start_time = None
    
    def start_crawl(self):
        """Start monitoring crawl session"""
        self.start_time = time.time()
        self.metrics = []
        self.logger.info("Performance monitoring started")
    
    async def measure_page_load(self, page, url: str) -> PageMetrics:
        """Measure page load performance"""
        start_time = time.time()
        
        try:
            # Enable request interception to count requests
            requests = []
            
            async def on_request(request):
                requests.append(request)
            
            page.on("request", on_request)
            
            # Navigate to page
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            load_time = time.time() - start_time
            
            # Get page size
            content = await page.content()
            page_size = len(content.encode('utf-8'))
            
            metrics = PageMetrics(
                url=url,
                load_time=load_time,
                page_size=page_size,
                request_count=len(requests),
                success=True
            )
            
            self.metrics.append(metrics)
            return metrics
            
        except Exception as e:
            metrics = PageMetrics(
                url=url,
                load_time=time.time() - start_time,
                page_size=0,
                request_count=0,
                success=False,
                error=str(e)
            )
            self.metrics.append(metrics)
            return metrics
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        if not self.metrics:
            return {}
        
        successful_metrics = [m for m in self.metrics if m.success]
        
        return {
            "total_pages": len(self.metrics),
            "successful_pages": len(successful_metrics),
            "success_rate": len(successful_metrics) / len(self.metrics) * 100,
            "average_load_time": sum(m.load_time for m in successful_metrics) / len(successful_metrics),
            "average_page_size": sum(m.page_size for m in successful_metrics) / len(successful_metrics),
            "average_requests_per_page": sum(m.request_count for m in successful_metrics) / len(successful_metrics),
            "total_crawl_time": time.time() - self.start_time,
            "pages_per_minute": len(self.metrics) / ((time.time() - self.start_time) / 60),
        }
    
    def generate_performance_report(self):
        """Generate detailed performance report"""
        summary = self.get_performance_summary()
        
        report = ["🚀 PERFORMANCE REPORT", "=" * 50]
        report.append(f"Total pages crawled: {summary['total_pages']}")
        report.append(f"Success rate: {summary['success_rate']:.1f}%")
        report.append(f"Average load time: {summary['average_load_time']:.2f}s")
        report.append(f"Average page size: {summary['average_page_size'] / 1024:.1f} KB")
        report.append(f"Average requests per page: {summary['average_requests_per_page']:.1f}")
        report.append(f"Total crawl time: {summary['total_crawl_time']:.1f}s")
        report.append(f"Pages per minute: {summary['pages_per_minute']:.1f}")
        
        # Slowest pages
        slow_pages = sorted([m for m in self.metrics if m.success], 
                           key=lambda x: x.load_time, reverse=True)[:5]
        
        if slow_pages:
            report.append("\n🐌 SLOWEST PAGES:")
            for i, metric in enumerate(slow_pages, 1):
                report.append(f"  {i}. {metric.url} ({metric.load_time:.2f}s)")
        
        return "\n".join(report)