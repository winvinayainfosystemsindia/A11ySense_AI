import time
from typing import Dict, Any, List

def create_empty_report() -> Dict[str, Any]:
    """Create empty report for no URLs"""
    return {
        'report': {
            'summary': {
                'total_pages': 0,
                'pages_audited': 0,
                'total_violations': 0,
                'average_score': 0,
                'audit_duration': 0
            },
            'page_results': [],
            'metadata': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_pages_analyzed': 0
            }
        },
        'output_paths': {}
    }

def create_error_report(urls: List[str], error: str) -> Dict[str, Any]:
    """Create error report when audit fails"""
    return {
        'report': {
            'summary': {
                'total_pages': len(urls),
                'pages_audited': 0,
                'total_violations': 0,
                'average_score': 0,
                'audit_duration': 0,
                'pages_with_errors': urls
            },
            'page_results': [],
            'metadata': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_pages_analyzed': len(urls),
                'error': error
            }
        },
        'output_paths': {}
    }
