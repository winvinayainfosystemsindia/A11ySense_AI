# A11ySense AI: Accessibility Audit Tool

![Logo](docs/logo/Generated%20Image%20November%2018,%202025%20-%205_05PM.png)

A powerful, microservices-based automated accessibility auditing solution designed to crawl websites, analyze pages for WCAG compliance, and generate comprehensive reports with actionable insights. 

---
📖 **Documentation**: [Architecture](docs/architecture.md) | [Modules & Roadmap](docs/modules.md)
---

This tool leverages **Playwright** for crawling, **axe-core** for accessibility testing, and **LLM (Large Language Model)** integration for business insights and ROI calculations.

## 🚀 Key Features

*   **Microservices Orchestration**: Independent services for Crawling, Analysis, LLM, and Reporting.
*   **Automated Crawling**: Async crawling using Playwright with configurable depth and anti-blocking.
*   **Axe-Core Auditing**: Full WCAG 2.0/2.1 compliance testing (A, AA).
*   **Advanced LLM Insights**: Uses Groq (Llama 3) to provide business impact analysis and code recommendations.
*   **CLI Automation**: A dedicated CLI tool to trigger audits and monitor progress.
*   **Comprehensive Reporting**: Generates detailed Excel and JSON reports.

## 🖥️ Professional System Requirements

For a professional deployment that ensures high-speed, parallelized auditing without internal bottlenecks or system hangs, the following specifications are recommended:

*   **Operating System**: 
    - **Development**: Windows 11 / macOS Sonoma
    - **Production**: Ubuntu 22.04+ (Long Term Support) or equivalent Linux distribution.
*   **Processor (CPU)**: 
    - **Minimum**: 4-core (e.g., Intel Core i5 / Ryzen 5)
    - **Recommended**: **8+ Core high-performance CPU** (e.g., Intel i7/i9 or AMD Ryzen 7/9) to handle concurrent Playwright browser instances and LLM processing.
*   **Memory (RAM)**: 
    - **Minimum**: 8GB
    - **Professional**: **16GB - 32GB RAM**. This is critical as every independent microservice and its child browser processes consume significant memory during full-site crawls.
*   **Storage**: 
    - **Type**: **NVMe SSD** (critical for fast log writing and report generation).
    - **Capacity**: 10GB+ available space to accommodate extensive audit histories, detailed JSON datasets, and Excel reports.
*   **Network**: High-speed, stable internet connection (**100Mbps+ recommended**) for low-latency crawling of remote web applications.

## 🛠️ Tool & Library Dependencies

### Core Tools
- **Python 3.10+**: The core runtime for all microservices.
- **Node.js** (Optional): While `playwright install` handles browser binaries, having Node.js available can help with advanced Playwright configuration.
- **Groq API Key**: Essential for the LLM Service to provide AI-powered accessibility insights.

### Primary Libraries
- **FastAPI / Uvicorn**: High-performance REST API framework and server.
- **Playwright**: Modern browser automation for crawling and analysis.
- **Axe-Playwright-Python**: axe-core engine integration.
- **Click**: Robust CLI framework for `a11y_cli.py`.
- **Httpx**: Next-generation HTTP client for service-to-service communication.
- **Pandas / Openpyxl**: Data processing and Excel report generation.

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd A11ySense_AI
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements/base.txt
    ```

3.  **Install Playwright browsers**
    ```bash
    playwright install chromium
    ```

4.  **Environment Setup**
    Copy `.env.example` to `.env` and add your `GROQ_API_KEY`.

## ⚙️ Microservices Orchestration

The project uses a Python-based manager to orchestrate multiple independent services.

### Start all services
```bash
python manager.py start
```

### Check service status
```bash
python manager.py status
```

### Stop all services
```bash
python manager.py stop
```

**Services list:**
- **Gateway (8000)**: Main entry point and orchestrator.
- **Crawler (8001)**: URL discovery.
- **Analyzer (8002)**: Accessibility testing.
- **LLM (8003)**: AI analysis.
- **Reporting (8004)**: Report generation.

## 🏃‍♂️ Usage (CLI Tool)

The automated audit is triggered via the CLI tool:

```bash
# Basic Audit
python scripts/a11y_cli.py run https://example.com --type basic --wait

# Comprehensive Audit (with LLM Insights)
python scripts/a11y_cli.py run https://example.com --type comprehensive --max-pages 20 --wait
```

### CLI Options:
- `--type [basic|comprehensive]`: Default is comprehensive.
- `--max-pages <int>`: Limits the crawl.
- `--max-depth <int>`: Limits the crawl depth.
- `--wait`: Waits for the audit to finish and displays the report paths.

## 📂 Project Structure

```
A11ySense_AI/
├── manager.py              # Microservices process manager
├── scripts/
│   ├── a11y_cli.py         # Main CLI tool
│   └── ...
├── src/
│   ├── services/           # FastAPI service wrappers (Gateway, Crawler, etc.)
│   ├── analyzer/           # Core audit logic
│   ├── crawler/            # Playwright crawler implementation
│   ├── llm/                # LLM integration (Groq)
│   ├── reporting/          # Report generation
│   └── utils/              # Shared utilities
├── storage/
│   ├── reports/            # Generated audit reports
│   └── logs/               # Service logs and error logs
└── requirements/           # Project dependencies
```

## 📄 License

This project is protected under a **Corporate Proprietary License**. 

Copyright © 2026 Win Vinaya Info Systems India. All rights reserved. 

Unauthorized copying, distribution, or modification of any part of this software is strictly prohibited. For licensing inquiries, please contact **Win Vinaya Info Systems India**.