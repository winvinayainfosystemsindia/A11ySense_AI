from typing import Dict, List, Optional
from dataclasses import dataclass
from playwright.async_api import Page
from ..utils.logger import setup_logger

@dataclass
class ContentMetrics:
    title: str
    title_length: int
    meta_description: str
    meta_description_length: int
    h1_count: int
    h2_count: int
    h3_count: int
    images_without_alt: int
    internal_links: int
    external_links: int
    word_count: int
    canonical_url: Optional[str]

class ContentAnalyzer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def analyze_page_content(self, page: Page, url: str) -> ContentMetrics:
        """Analyze page content for SEO and accessibility insights"""
        
        # Extract basic SEO elements
        title = await page.title() or ""
        meta_description = await page.evaluate('''() => {
            const meta = document.querySelector('meta[name="description"]');
            return meta ? meta.content : '';
        }''')
        
        # Count heading elements
        h1_count = await page.locator('h1').count()
        h2_count = await page.locator('h2').count()
        h3_count = await page.locator('h3').count()
        
        # Check images without alt text
        images_without_alt = await page.evaluate('''() => {
            return Array.from(document.images).filter(img => !img.alt).length;
        }''')
        
        # Count links
        internal_links = await page.locator(f'a[href^="/"], a[href^="{url}"]').count()
        external_links = await page.locator('a[href^="http"]').count() - internal_links
        
        # Get word count
        word_count = await page.evaluate('''() => {
            const text = document.body.innerText;
            return text.trim().split(/\\s+/).length;
        }''')
        
        # Get canonical URL
        canonical_url = await page.evaluate('''() => {
            const canonical = document.querySelector('link[rel="canonical"]');
            return canonical ? canonical.href : null;
        }''')
        
        return ContentMetrics(
            title=title,
            title_length=len(title),
            meta_description=meta_description,
            meta_description_length=len(meta_description),
            h1_count=h1_count,
            h2_count=h2_count,
            h3_count=h3_count,
            images_without_alt=images_without_alt,
            internal_links=internal_links,
            external_links=external_links,
            word_count=word_count,
            canonical_url=canonical_url
        )
    
    async def generate_seo_report(self, content_metrics: Dict[str, ContentMetrics]) -> str:
        """Generate SEO insights from content metrics"""
        report = ["🔍 SEO & CONTENT ANALYSIS", "=" * 40]
        
        # Analyze titles
        short_titles = [url for url, metrics in content_metrics.items() 
                       if metrics.title_length < 30]
        long_titles = [url for url, metrics in content_metrics.items() 
                      if metrics.title_length > 60]
        
        if short_titles:
            report.append(f"\n⚠️  Pages with short titles (<30 chars): {len(short_titles)}")
        if long_titles:
            report.append(f"⚠️  Pages with long titles (>60 chars): {len(long_titles)}")
        
        # Analyze meta descriptions
        no_meta_desc = [url for url, metrics in content_metrics.items() 
                       if not metrics.meta_description]
        if no_meta_desc:
            report.append(f"❌ Pages without meta descriptions: {len(no_meta_desc)}")
        
        # Analyze heading structure
        multiple_h1 = [url for url, metrics in content_metrics.items() 
                      if metrics.h1_count > 1]
        no_h1 = [url for url, metrics in content_metrics.items() 
                if metrics.h1_count == 0]
        
        if multiple_h1:
            report.append(f"⚠️  Pages with multiple H1 tags: {len(multiple_h1)}")
        if no_h1:
            report.append(f"❌ Pages without H1 tags: {len(no_h1)}")
        
        # Analyze images
        images_no_alt = [(url, metrics.images_without_alt) 
                        for url, metrics in content_metrics.items() 
                        if metrics.images_without_alt > 0]
        
        if images_no_alt:
            report.append(f"\n🖼️  Pages with images missing alt text:")
            for url, count in sorted(images_no_alt, key=lambda x: x[1], reverse=True)[:5]:
                report.append(f"  • {url}: {count} images")
        
        return "\n".join(report)