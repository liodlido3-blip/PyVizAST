# PyVizAST - Python AST Visualization Analyzer Launch Script
# PowerShell Version

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PyVizAST - Python AST Visualization Analyzer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[Error] Python not found, please install Python 3.8+ first." -ForegroundColor Red
    Read-Host "Press Enter to exit."
    exit 1
}

# Test pip
try {
    pip --version | Out-Null
    Write-Host "[OK] pip already installed." -ForegroundColor Green
} catch {
    Write-Host "[Error] pip was not found." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install backend dependencies
Write-Host ""
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Backend dependencies installation completed." -ForegroundColor Green
} else {
    Write-Host "[Error] Backend dependency installation failed." -ForegroundColor Red
    Read-Host "Press Enter to exit."
    exit 1
}

# Test npm
$npmExists = Get-Command npm -ErrorAction SilentlyContinue
if ($npmExists) {
    Write-Host "[OK] npm is installed." -ForegroundColor Green
    
    # Install Front-End Dependencies
    Write-Host ""
    Write-Host "Installing Front-End Dependencies..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Front-end dependencies installation completed" -ForegroundColor Green
    } else {
        Write-Host "[Warning] Front-end dependency installation failed. Only the back-end will be started." -ForegroundColor Yellow
    }
} else {
    Write-Host "[Warning] npm not found, skipping frontend installation" -ForegroundColor Yellow
    Write-Host "       If front-end functionality is required, please install Node.js." -ForegroundColor Yellow
}

# Start Service
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Services..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Start Backend
Write-Host ""
Write-Host "Starting the backend service (http://localhost:8000)..." -ForegroundColor Yellow

$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
}

# Waiting for the backend to start
Start-Sleep -Seconds 3

# Verify whether the backend has started successfully
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] Backend service started successfully" -ForegroundColor Green
    Write-Host "      API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
} catch {
    Write-Host "[Error] An error has occurred in the backend service. Please check the logs in the logs folder and submit an issue to the repository." -ForegroundColor Red
}

# Start the frontend
if ($npmExists) {
    Write-Host ""
    Write-Host "Starting the frontend service (http://localhost:3000)..." -ForegroundColor Yellow
    
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location "$using:PSScriptRoot\frontend"
        npm start
    }
    
    Write-Host "[OK] Frontend service is starting..." -ForegroundColor Green
    Write-Host "      Visit address: http://localhost:3000" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " The service has started. Press Ctrl+C to stop all services." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

start http://localhost:3000

# Waiting for user interruption
try {
    while ($true) {
        # Check the backend logs
        $backendOutput = Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        if ($backendOutput) {
            Write-Host $backendOutput -ForegroundColor Gray
        }
        
        if ($npmExists -and $frontendJob) {
            $frontendOutput = Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
            if ($frontendOutput) {
                Write-Host $frontendOutput -ForegroundColor Gray
            }
        }
        
        Start-Sleep -Milliseconds 100
    }
} finally {
    Write-Host ""
    Write-Host "Service is being discontinued..." -ForegroundColor Yellow
    
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
    
    if ($npmExists -and $frontendJob) {
        Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $frontendJob -ErrorAction SilentlyContinue
    }
    
    Write-Host "[OK] The service has been stopped." -ForegroundColor Green
}
