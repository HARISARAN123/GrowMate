# GrowMate Development Startup Script (PowerShell)
# Launches Flask backend and Voice Agent in parallel with monitoring

param(
    [switch]$SkipPythonCheck = $false,
    [switch]$CheckOnly = $false,
    [int]$BackendPort = 5000,
    [int]$AgentPort = 8081
)

function Write-Header {
    param([string]$Text)
    Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan + "`n"
}

function Write-Status {
    param([string]$Status, [string]$Color = "Green")
    Write-Host "  ✓ $Status" -ForegroundColor $Color
}

function Write-Error-Custom {
    param([string]$Error)
    Write-Host "  ✗ $Error" -ForegroundColor Red
}

# Start Script
Write-Header "GrowMate Development Environment"

# 1. Check Python
if (-not $SkipPythonCheck) {
    Write-Host "Checking Python installation..." -ForegroundColor Yellow
    try {
        $pythonVersion = python --version 2>&1
        Write-Status "Python found: $pythonVersion"
    } catch {
        Write-Error-Custom "Python not found. Install Python 3.8+ and add to PATH."
        exit 1
    }
}

# 2. Check Working Directory
$workDir = "d:\GrowMate"
if (-not (Test-Path $workDir)) {
    Write-Error-Custom "Directory not found: $workDir"
    exit 1
}

Set-Location $workDir
Write-Status "Working directory: $workDir"

# 3. Check .env
if (-not (Test-Path ".env")) {
    Write-Error-Custom ".env file not found. Create it with LiveKit configuration."
    exit 1
}
Write-Status ".env file found"

# 4. Check Requirements
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import livekit" 2>&1 | Out-Null
    Write-Status "Dependencies installed"
} catch {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to install dependencies."
        exit 1
    }
    Write-Status "Dependencies installed"
}

# 5. Check Port Availability
Write-Host "Checking port availability..." -ForegroundColor Yellow

$backendPortInUse = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
if ($backendPortInUse) {
    Write-Error-Custom "Port $BackendPort (Flask) is already in use"
    exit 1
}
Write-Status "Port $BackendPort available for Flask"

$agentPortInUse = Get-NetTCPConnection -LocalPort $AgentPort -ErrorAction SilentlyContinue
if ($agentPortInUse) {
    Write-Error-Custom "Port $AgentPort (Agent) is already in use"
    exit 1
}
Write-Status "Port $AgentPort available for Agent"

# 6. If CheckOnly, exit here
if ($CheckOnly) {
    Write-Header "All checks passed! Ready to run."
    Write-Host "  Run: .\start-dev.ps1 -CheckOnly:`$false`n" -ForegroundColor Green
    exit 0
}

# 7. Start Services
Write-Header "Starting Services"

Write-Host "Launching Flask Backend (Port $BackendPort)..." -ForegroundColor Yellow
$backendProcess = Start-Process python -ArgumentList "app.py" `
    -WindowStyle Normal -PassThru `
    -ErrorAction SilentlyContinue

if ($backendProcess) {
    Write-Status "Flask Backend started (PID: $($backendProcess.Id))"
} else {
    Write-Error-Custom "Failed to start Flask Backend"
}

Start-Sleep -Seconds 2

Write-Host "Launching Voice Agent Worker (Port $AgentPort)..." -ForegroundColor Yellow
$agentProcess = Start-Process python -ArgumentList "voice_agent.py" `
    -WindowStyle Normal -PassThru `
    -ErrorAction SilentlyContinue

if ($agentProcess) {
    Write-Status "Voice Agent started (PID: $($agentProcess.Id))"
} else {
    Write-Error-Custom "Failed to start Voice Agent"
}

# 8. Display Summary
Write-Header "Services Running"

Write-Host "Flask Backend:" -ForegroundColor Green
Write-Host "  URL: http://localhost:$BackendPort" -ForegroundColor Gray
Write-Host "  Terminal: Check 'GrowMate Backend' window" -ForegroundColor Gray

Write-Host "`nVoice Agent Worker:" -ForegroundColor Green
Write-Host "  Port: $AgentPort (internal)" -ForegroundColor Gray
Write-Host "  Terminal: Check 'GrowMate Voice Agent' window" -ForegroundColor Gray

Write-Host "`nAccess Application:" -ForegroundColor Green
Write-Host "  Main: http://localhost:$BackendPort/" -ForegroundColor Cyan
Write-Host "  Voice Bot: http://localhost:$BackendPort/voicebot" -ForegroundColor Cyan

Write-Host "`nDeveloper Commands:" -ForegroundColor Green
Write-Host "  Check logs: Get-Content *.log -Tail 20" -ForegroundColor Gray
Write-Host "  Stop all: Get-Process python | Stop-Process" -ForegroundColor Gray
Write-Host "  Stop Flask: Stop-Process -Id $($backendProcess.Id)" -ForegroundColor Gray
Write-Host "  Stop Agent: Stop-Process -Id $($agentProcess.Id)" -ForegroundColor Gray

Write-Host "`nPress Ctrl+C to stop or close any window to terminate." -ForegroundColor Yellow
Write-Host "`n"

# 9. Monitor Processes
$monitoring = $true
while ($monitoring) {
    Start-Sleep -Seconds 5
    
    if (-not (Get-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Flask Backend crashed! Check logs."
        $monitoring = $false
    }
    
    if (-not (Get-Process -Id $agentProcess.Id -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Voice Agent crashed! Check logs."
        $monitoring = $false
    }
}

Write-Host "Development environment stopped.`n" -ForegroundColor Yellow
