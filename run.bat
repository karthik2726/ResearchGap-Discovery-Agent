@echo off
echo ==============================================
echo ResearchIQ - Application Runner
echo ==============================================

echo Starting FastAPI Backend...
start cmd /k "cd backend && venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting React Frontend...
start cmd /k "cd frontend && npm run dev"

echo Both services are starting up!
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo ==============================================
