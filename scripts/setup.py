#!/usr/bin/env python3
import subprocess
import sys

def install_playwright_browsers():
    """Install Playwright browsers"""
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("Playwright browsers installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Playwright browsers: {e}")

if __name__ == "__main__":
    install_playwright_browsers()