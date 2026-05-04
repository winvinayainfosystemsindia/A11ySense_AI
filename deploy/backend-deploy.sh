#!/bin/bash
set -e

ENV=$1
if [[ -z "$ENV" ]]; then
  echo "Usage: ./backend-deploy.sh [dev|qa|prod]"
  exit 1
fi

PROJECT_ROOT="/var/www/a11ysense-ai/$ENV"
echo "Deploying Backend for $ENV environment in $PROJECT_ROOT..."

cd $PROJECT_ROOT

# 1. Load environment variables
if [ -f ".env.$ENV" ]; then
    cp .env.$ENV .env
    echo "Environment file .env.$ENV copied to .env"
fi

# 2. Setup/Activate Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Install dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt --quiet

# 4. Extract ports from .env for PM2 startup
G_PORT=$(grep GATEWAY_PORT .env | cut -d '=' -f2 | tr -d '\r')
A_PORT=$(grep AGENT_PORT .env | cut -d '=' -f2 | tr -d '\r')
R_PORT=$(grep REPORTING_PORT .env | cut -d '=' -f2 | tr -d '\r')

G_PORT=${G_PORT:-8000}
A_PORT=${A_PORT:-8001}
R_PORT=${R_PORT:-8002}

# 5. Restart services via PM2
echo "Restarting services via PM2..."
pm2 stop gateway-$ENV agent-$ENV reporting-$ENV --quiet || true

pm2 start "uvicorn app.main:app --host 0.0.0.0 --port $G_PORT" --name gateway-$ENV --cwd $PROJECT_ROOT/backend/services/gateway
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port $A_PORT" --name agent-$ENV --cwd $PROJECT_ROOT/backend/services/agent
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port $R_PORT" --name reporting-$ENV --cwd $PROJECT_ROOT/backend/services/reporting

echo "Backend deployment to $ENV completed successfully."
