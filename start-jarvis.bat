@echo on
setlocal enabledelayedexpansion

title Jarvis AI Assistant
color 0f

echo ===============================================================================
echo                                 JARVIS AI ASSISTANT
echo ===============================================================================
echo.

:: 1. Environment Checks
echo [1/4] Checking System Requirements...

:: check python
echo Checking Python...
python --version 
if errorlevel 1 (
    color 0c
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)
echo Python OK.
echo.
pause

:: check node
echo Checking Node.js...
node --version 
if errorlevel 1 (
    color 0c
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js 18+ from nodejs.org
    pause
    exit /b 1
)
:: Check npm explicitly after node
echo Checking npm...
call npm --version
if errorlevel 1 (
    echo [WARNING] npm might be missing, but node exists.
    pause
)

echo [OK] System requirements met.
echo.
pause

:: 2. Backend Setup
echo [2/4] Starting Backend...
cd /d "%~dp0backend"

if not exist ".env" (
    echo [WARNING] .env file missing in backend.
    if exist ".env.example" (
        copy .env.example .env
        echo [INFO] Created .env from template.
    ) else (
        echo [ERROR] .env.example missing! Cannot configure.
    )
)

if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

echo [INFO] checking dependencies...
:: Run install in foreground to verify it works
call venv\Scripts\activate && pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
)

echo [INFO] Launching Backend Server...
start "Jarvis Backend" cmd /k "title Jarvis Backend && cd /d %~dp0backend && venv\Scripts\activate && python main.py"

:: 3. Frontend Setup
echo.
echo [3/4] Starting Frontend...
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [INFO] Installing frontend modules (first run only)...
    call npm install
)

echo [INFO] Launching Frontend Server...
start "Jarvis Frontend" cmd /k "title Jarvis Frontend && cd /d %~dp0frontend && npm run dev"

:: 4. Ready
echo.
echo [4/4] Launching Interface...
echo.
echo ===============================================================================
echo    JARVIS IS ONLINE
echo ===============================================================================
echo.
echo Backend API:    http://localhost:8000
echo User Interface: http://localhost:5173
echo.
echo [INFO] Waiting for servers to initialize...
timeout /t 5 /nobreak
start http://localhost:5173

echo.
echo Keep this window open to monitor status.
echo Press any key to stop Jarvis.
pause

:: Cleanup
taskkill /fi "WINDOWTITLE eq Jarvis Backend" /f
taskkill /fi "WINDOWTITLE eq Jarvis Frontend" /f
