import asyncio
import random
from typing import Callable, Any
from functools import wraps
from ..core.exceptions import CrawlerException
from ..utils.logger import setup_logger

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = setup_logger(__name__)
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt) + random.uniform(0, 0.1)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                            f"Retrying in {wait_time:.2f}s. Error: {e}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )
            raise CrawlerException(f"Operation failed after {max_retries + 1} attempts: {last_exception}")
        return wrapper
    return decorator

class ErrorHandler:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
        self.ignored_errors = [
            "Cannot read properties of null",
            "Cannot read properties of undefined",
            "addEventListener",
            "is not a function",
            "script error",
            "undefined is not an object"
        ]
    
    def _should_ignore_error(self, error_message: str) -> bool:
        """Check if error should be ignored"""
        return any(ignored in error_message for ignored in self.ignored_errors)
    
    async def handle_navigation_errors(self, page, url: str):
        """Handle common navigation errors"""
        try:
            # Set up error monitoring with filtering
            def handle_page_error(error):
                if not self._should_ignore_error(error.message):
                    self.logger.error(f"Page error: {error.message}")
            
            def handle_console_message(msg):
                if msg.type == 'error' and not self._should_ignore_error(msg.text):
                    self.logger.debug(f"Console error: {msg.text}")
            
            page.on("pageerror", handle_page_error)
            page.on("console", handle_console_message)
            
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if response and response.status >= 400:
                if response.status == 404:
                    self.logger.warning(f"HTTP 404 (Page not found): {url}")
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
            
            return response
        except Exception as e:
            self.logger.error(f"Navigation error for {url}: {e}")
            raise