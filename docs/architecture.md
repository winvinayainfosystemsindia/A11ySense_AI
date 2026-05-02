# A11ySense AI - Technical Architecture

A11ySense AI is a microservices-based platform designed for autonomous, AI-driven accessibility auditing.

## Service Architecture

### 1. Gateway (`port: 8000`)
- **Role**: Orchestrator and API Entry Point.
- **Responsibilities**: Receives audit requests from the frontend and forwards them to the Agent.
- **Tech Stack**: FastAPI, HTTPX.

### 2. Agent / OpenClaw (`port: 8001`)
- **Role**: The Execution Engine.
- **Responsibilities**: 
  - Runs technical audits using **Axe-core** via **Playwright**.
  - Performs AI-driven remediation analysis using **Groq (Llama 3)**, **Claude**, or **Gemini**.
  - Aggregates data and sends it to the Reporting service.
- **Tech Stack**: FastAPI, Playwright, Pydantic, LLM SDKs.

### 3. Reporting (`port: 8002`)
- **Role**: Report Generator.
- **Responsibilities**: Transforms raw audit results into Allure JSON format and manages report storage.
- **Tech Stack**: FastAPI, Allure-python-commons.

## Communication Flow

1. **User Action**: User submits a URL in the React Frontend.
2. **Gateway**: Forwards the URL to the Agent.
3. **Agent**: 
   - Starts a background task.
   - Crawls the URL and finds technical WCAG violations.
   - For each violation, it asks the LLM for a "Friendly Name," "User Impact," and "Remediation Plan."
   - Sends the enriched data to Reporting.
4. **Reporting**: Saves Allure JSON files to `backend/storage/reports/allure-results`.
5. **Viewer**: `allure serve` reads these files and presents a professional dashboard to the user.

## Data Schemas
All services share common schemas located in `backend/common/schemas/audit.py` to ensure type safety and consistent data flow.
