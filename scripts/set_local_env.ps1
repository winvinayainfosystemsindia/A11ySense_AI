# Set Environment Variables for Service Discovery on Localhost
$env:AGENT_SERVICE_URL="http://localhost:8001"
$env:REPORTING_SERVICE_URL="http://localhost:8002"
$env:CRAWLER_SERVICE_URL="http://localhost:8003"
$env:ANALYZER_SERVICE_URL="http://localhost:8004"
$env:LLM_SERVICE_URL="http://localhost:8005"

Write-Host "Environment variables set for local startup." -ForegroundColor Green
Write-Host "To start a service, use: uvicorn app.main:app --port <PORT>"
Write-Host "Gateway: 8000, Agent: 8001, Reporting: 8002" -ForegroundColor Yellow
