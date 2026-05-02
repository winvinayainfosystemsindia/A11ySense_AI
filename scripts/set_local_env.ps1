# Set PYTHONPATH to include the backend directory so 'common' module can be found
$env:PYTHONPATH="$PSScriptRoot\..\backend"

# Set Environment Variables for Service Discovery on Localhost
$env:AGENT_SERVICE_URL="http://localhost:8001"
$env:REPORTING_SERVICE_URL="http://localhost:8002"
$env:CRAWLER_SERVICE_URL="http://localhost:8003"
$env:ANALYZER_SERVICE_URL="http://localhost:8004"
$env:LLM_SERVICE_URL="http://localhost:8005"

# Load from .env file if it exists
if (Test-Path "$PSScriptRoot\..\.env") {
    Get-Content "$PSScriptRoot\..\.env" | ForEach-Object {
        if ($_ -match "^\s*([^#\s][^=]*)\s*=\s*(.*)\s*$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            $env:$name = $value
        }
    }
}

# LLM Configuration Defaults (Override with .env)
if (-not $env:LLM_PROVIDER) { $env:LLM_PROVIDER="mock" }
if (-not $env:GROQ_API_KEY) { $env:GROQ_API_KEY="your_groq_key_here" }

# Allure Reporting Path
$env:ALLURE_RESULTS_DIR="$PSScriptRoot\..\backend\storage\reports\allure-results"

Write-Host "Environment variables set for local startup." -ForegroundColor Green
Write-Host "To start a service, use: uvicorn app.main:app --port <PORT>"
Write-Host "Gateway: 8000, Agent: 8001, Reporting: 8002" -ForegroundColor Yellow
