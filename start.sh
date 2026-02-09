#!/bin/bash

# Coloring
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
DEBUG_MODE=false
BACKEND_ONLY=false
for arg in "$@"; do
    if [ "$arg" == "--debug" ]; then
        DEBUG_MODE=true
    fi
    if [ "$arg" == "--backend-only" ]; then
        BACKEND_ONLY=true
    fi
done

echo -e "${BLUE}[INFO] Cleaning up ports 8001 (Backend)...${NC}"
kill -9 $(lsof -t -i:8001) 2>/dev/null
pkill -f 'uvicorn app.main:app' 2>/dev/null || true

if [ "$BACKEND_ONLY" = false ]; then
    echo -e "${BLUE}[INFO] Cleaning up port 5173 (Frontend)...${NC}"
    kill -9 $(lsof -t -i:5173) 2>/dev/null
fi

# 1. Start Langfuse
echo -e "${BLUE}[INFO] Starting Langfuse Infrastructure...${NC}"
cd backend
if [ -f "start_langfuse.sh" ]; then
    bash start_langfuse.sh
else
    echo "Warning: start_langfuse.sh not found in backend/. skipping..."
fi
cd ..

# 2. Start Frontend
if [ "$BACKEND_ONLY" = false ]; then
    echo -e "${BLUE}[INFO] Starting Frontend (Background)...${NC}"
    cd frontend
    npm run dev > /dev/null 2>&1 &
    FRONTEND_PID=$!
    echo -e "${GREEN}[SUCCESS] Frontend running at http://localhost:5173${NC}"
    cd ..
fi

# 3. Start Backend
echo -e "${BLUE}[INFO] Starting Backend...${NC}"
cd backend

# Use the virtual environment python
PYTHON_EXEC=".venv/bin/python"
if [ ! -f "$PYTHON_EXEC" ]; then
    echo "Virtual environment not found, trying system python..."
    PYTHON_EXEC="python3"
fi

export PYTHONPATH=$(pwd)

# Load .env variables so OTel/Langfuse can pick them up
if [ -f ".env" ]; then
    echo -e "${BLUE}[INFO] Loading .env variables...${NC}"
    set -a
    source .env
    set +a
fi

echo -e "${GREEN}[SUCCESS] Backend running at http://localhost:8001${NC}"

# Define cleanup function
cleanup() {
    echo -e "\n${BLUE}[INFO] Stopping services...${NC}"
    if [ "$BACKEND_ONLY" = false ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    # The backend will be killed by the script exit if it's the last command, 
    # but if we background it we need to kill it.
    # Here we will exec uvicorn so it takes over the shell provided we don't need to do anything else.
}

# Trap SIGINT (Ctrl+C)
trap cleanup EXIT



if [ "$DEBUG_MODE" = true ]; then
    echo -e "${BLUE}[INFO] Starting Backend in DEBUG mode (listening on 5678, waiting for client)...${NC}"
    $PYTHON_EXEC -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
else
    echo -e "${BLUE}[INFO] Starting Backend in NORMAL mode...${NC}"
    $PYTHON_EXEC -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
fi

