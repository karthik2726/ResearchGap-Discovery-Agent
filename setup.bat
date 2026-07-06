@echo off
echo ==============================================
echo ResearchIQ - Setup Script
echo ==============================================

echo.
echo [1/3] Setting up Python Virtual Environment...
cd backend
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo [2/3] Installing Backend Dependencies...
pip install -r requirements.txt

echo.
echo [3/3] Installing Frontend Dependencies...
cd ..\frontend
call npm install

echo.
echo ==============================================
echo Setup Complete! 
echo Please configure your API keys in backend/.env
echo You can now run the application using run.bat
echo ==============================================
pause
