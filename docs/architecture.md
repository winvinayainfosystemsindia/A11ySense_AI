# A11ySense AI Architecture

## Microservices Overview

A11ySense AI is designed as a decentralized system to ensure scalability and independence.

### 1. Gateway Service (Port 8000)
- Central entry point for all API requests.
- Handles Authentication and Authorization.
- Orchestrates tasks between specialized services.

### 2. Crawler Service
- Autonomous discovery of URLs and Sitemaps.
- Extracts page metadata for auditing.

### 3. Analyzer Service
- Executes accessibility audits using `axe-core`.
- Categorizes violations and collects evidence.

### 4. Agent Service (OpenClaw)
- Integrates **OpenClaw** for agentic auditing.
- Simulates user interactions and performs deep structural analysis.

### 5. LLM Service
- Provides AI-driven insights into accessibility issues.
- Generates code-level remediation suggestions.

### 6. Reporting Service
- Aggregates audit data into Allure and JSON reports.

## Frontend
- React + TypeScript + MUI Dashboard for real-time monitoring and reporting.
