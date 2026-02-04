#!/bin/bash

# Coloring
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}[INFO] Cleaning up ports 8000 (Backend) and 5173 (Frontend)...${NC}"
kill -9 $(lsof -t -i:8000) 2>/dev/null
kill -9 $(lsof -t -i:5173) 2>/dev/null
pkill -f 'uvicorn app.main:app' 2>/dev/null || true

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
echo -e "${BLUE}[INFO] Starting Frontend (Background)...${NC}"
cd frontend
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}[SUCCESS] Frontend running at http://localhost:5173${NC}"
cd ..

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
echo -e "${GREEN}[SUCCESS] Backend running at http://localhost:8000${NC}"

# Define cleanup function
cleanup() {
    echo -e "\n${BLUE}[INFO] Stopping services...${NC}"
    kill $FRONTEND_PID 2>/dev/null
    # The backend will be killed by the script exit if it's the last command, 
    # but if we background it we need to kill it.
    # Here we will exec uvicorn so it takes over the shell provided we don't need to do anything else.
}

# Trap SIGINT (Ctrl+C)
trap cleanup EXIT

# Run Uvicorn directly
$PYTHON_EXEC -m uvicorn app.main:app --host 127.0.0.1 --reload

