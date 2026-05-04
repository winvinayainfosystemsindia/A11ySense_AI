import os
import asyncio
import sys
from dotenv import load_dotenv

# Fix for Playwright/Subprocess on Windows
# Set policy at module level to ensure it runs as soon as this config is imported
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def setup_environment():
    """
    Loads environment variables from the appropriate .env file based on APP_ENV.

    Priority:
    1. .env.[APP_ENV] if APP_ENV is set
    2. .env (default)
    """
    app_env = os.getenv("APP_ENV", "dev")
    env_file = f".env.{app_env}"
    
    # Search for the env file in the root directory
    # Assuming the services are run from their own directories or project root
    root_env_path = os.path.join(os.path.dirname(__file__), "../../", env_file)
    default_env_path = os.path.join(os.path.dirname(__file__), "../../.env")

    if os.path.exists(root_env_path):
        load_dotenv(root_env_path)
    elif os.path.exists(default_env_path):
        load_dotenv(default_env_path)
    
    return app_env
