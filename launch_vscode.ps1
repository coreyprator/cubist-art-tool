# === CUBIST STAMP BEGIN ===
# Project: Cubist Art
# File: launch_vscode.ps1
# Version: v2.3.7
# Build: 2025-09-01T11:18:25
# Commit: 374dfa9
# Stamped: 2025-09-01T11:18:27+02:00
# === CUBIST STAMP END ===
# Cubist Art Project - VS Code Launcher with Local .venv
# PowerShell version of the launcher

Write-Host "Starting Cubist Art Project with local .venv..." -ForegroundColor Green

# Check if .venv exists, create it if it doesn't
if (-not (Test-Path ".venv")) {
    Write-Host "Creating local virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Write-Host "Make sure Python is installed and available in PATH" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
} else {
    # Check if .venv is properly set up (has python.exe)
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Host "ERROR: Virtual environment exists but is incomplete" -ForegroundColor Red
        Write-Host "Missing .venv\Scripts\python.exe - environment may be corrupted" -ForegroundColor Red
        Write-Host "Please delete .venv folder and run setup script again" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "✓ Virtual environment found and verified" -ForegroundColor Green
}

# Activate the local virtual environment
Write-Host "Activating local virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install/update requirements if requirements.txt exists
if (Test-Path "requirements.txt") {
    Write-Host "Checking and installing/updating packages from requirements.txt..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Some packages failed to install" -ForegroundColor Yellow
        Write-Host "You may need to update requirements.txt or check package availability" -ForegroundColor Yellow
    } else {
        Write-Host "✓ All dependencies installed successfully" -ForegroundColor Green
    }
} else {
    Write-Host "No requirements.txt found - skipping package installation" -ForegroundColor Yellow
}

# Launch VS Code in current directory
Write-Host "Launching VS Code with project environment..." -ForegroundColor Green
code .

Write-Host "VS Code launched. You can close this window." -ForegroundColor Green

# === CUBIST FOOTER STAMP BEGIN ===
# End of file - v2.3.7 - stamped 2025-09-01T11:18:27+02:00
# === CUBIST FOOTER STAMP END ===
