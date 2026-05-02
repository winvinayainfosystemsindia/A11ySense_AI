# Load environment variables
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
& "$scriptPath\set_local_env.ps1"

Write-Host "Starting A11ySense AI Backend Services..." -ForegroundColor Cyan

# Start Gateway (Port 8000)
Write-Host "Starting Gateway on port 8000..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend/services/gateway; & '$scriptPath\set_local_env.ps1'; uvicorn app.main:app --port 8000" -WindowStyle Normal

# Start Agent (Port 8001)
Write-Host "Starting Agent on port 8001..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend/services/agent; & '$scriptPath\set_local_env.ps1'; uvicorn app.main:app --port 8001" -WindowStyle Normal

# Start Reporting (Port 8002)
Write-Host "Starting Reporting on port 8002..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend/services/reporting; & '$scriptPath\set_local_env.ps1'; uvicorn app.main:app --port 8002" -WindowStyle Normal

# Start Allure Server
Write-Host "Starting Allure Report Server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "allure serve backend/storage/reports/allure-results" -WindowStyle Normal

Write-Host "All services started! You can now use the frontend at http://localhost:5173/audit" -ForegroundColor Green
