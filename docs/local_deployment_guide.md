# A11ySense AI - Local Deployment Guide

This guide provides step-by-step instructions for running the A11ySense AI platform locally without Docker.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Java 11+** (Required for Allure)
- **Allure Commandline**: [Install Guide](https://allurereport.org/docs/install/)
- **Git**

## 1. Environment Setup

### 1.1 Create Secrets File
Create a file named `.env` in the root of the project:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

### 1.2 Initialize Environment Variables
Before starting any service, you must run the environment script in **every new terminal window**:
```powershell
.\scripts\set_local_env.ps1
```

## 2. Starting Backend Services (One by One)

Open three separate terminals and perform the following steps for each:

### terminal 1: Gateway Service (Port 8000)
The entry point for the frontend.
```powershell
.\scripts\set_local_env.ps1
cd backend/services/gateway
uvicorn app.main:app --port 8000
```

### terminal 2: Agent (OpenClaw) Service (Port 8001)
The "brain" that runs audits and AI remediation.
```powershell
.\scripts\set_local_env.ps1
cd backend/services/agent
# Install dependencies if first time
pip install -r requirements.txt
playwright install
# Start service
uvicorn app.main:app --port 8001
```

### terminal 3: Reporting Service (Port 8002)
Generates Allure-compatible JSON reports.
```powershell
.\scripts\set_local_env.ps1
cd backend/services/reporting
uvicorn app.main:app --port 8002
```

## 3. Starting the Frontend

Open a new terminal:
```powershell
cd frontend
npm install
npm run dev
```
The UI will be available at `http://localhost:5173`.

## 4. Viewing Reports

To see the AI-driven audit results, run the Allure server:
```powershell
allure serve backend/storage/reports/allure-results
```

## Troubleshooting

- **ModuleNotFoundError: 'common'**: Ensure you ran `.\scripts\set_local_env.ps1` to set the `PYTHONPATH`.
- **405 Method Not Allowed**: Ensure the Gateway has CORS enabled (it is by default in the latest code).
- **Serialization Errors**: Ensure all services are updated to use `model_dump(mode='json')` for Pydantic models.
