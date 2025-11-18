class AuditToolException(Exception):
    """Base exception for the audit tool"""
    pass

class CrawlerException(AuditToolException):
    """Crawler related exceptions"""
    pass

class CloudFlareBlockedException(CrawlerException):
    """Raised when CloudFlare blocks the crawler"""
    pass

class SitemapParseException(CrawlerException):
    """Raised when sitemap parsing fails"""
    pass

class AnalysisException(AuditToolException):
    """Analysis related exceptions"""
    pass

class LLMException(AuditToolException):
    """LLM related exceptions"""
    pass

class ReportGenerationException(AuditToolException):
    """Report generation exceptions"""
    pass