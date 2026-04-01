@echo off
REM GrowMate Development Startup Script
REM Starts Flask backend (port 5000) and Voice Agent (port 8081) in separate windows

setlocal enabledelayedexpansion

cd /d d:\GrowMate

echo.
echo ====================================================
echo      GrowMate Development Environment Startup
echo ====================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ and add to PATH.
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import livekit" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
)

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found. Please create it with LiveKit configuration.
    pause
    exit /b 1
)

echo.
echo Starting Flask Backend (Port 5000)...
start "GrowMate Backend" cmd /k "python app.py"

timeout /t 2 /nobreak

echo.
echo Starting Voice Agent Worker (Port 8081)...
start "GrowMate Voice Agent" cmd /k "python voice_agent.py"

timeout /t 2 /nobreak

echo.
echo ====================================================
echo      ✅ GrowMate is running!
echo ====================================================
echo.
echo Flask Backend:  http://localhost:5000
echo Voice Agent:    Connecting to LiveKit...
echo.
echo Open http://localhost:5000/voicebot in your browser
echo.
echo Press Ctrl+C in each window to stop.
echo.
pause
