@echo off
echo ====================================
echo Stopping all Python processes...
echo ====================================
taskkill /F /IM python.exe 2>nul

timeout /t 2 /nobreak >nul

echo.
echo ====================================
echo Starting Bot...
echo ====================================
cd /d "%~dp0"
call venv\Scripts\activate
start "Educational Bot" cmd /k "venv\Scripts\python.exe -m bot.main"

timeout /t 3 /nobreak >nul

echo.
echo ====================================
echo Starting Dashboard...
echo ====================================
start "Dashboard" cmd /k "venv\Scripts\python.exe -m uvicorn admin_dashboard.app:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo ====================================
echo Done! Bot and Dashboard are running
echo ====================================
echo.
pause
