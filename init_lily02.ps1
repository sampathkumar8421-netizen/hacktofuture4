# Lily02 Workstation Initialization Script (Windows)

Write-Host "🌊 Initializing Lily02 Scientific Workstation..." -ForegroundColor Cyan

# 1. Install Backend Dependencies
Write-Host "`n[1/3] Installing Python Dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install -e .

# 2. Build Frontend
Write-Host "`n[2/3] Building Scientific UI (React)..." -ForegroundColor Yellow
if (Test-Path "lily02_frontend") {
    Push-Location "lily02_frontend"
    npm install
    npm run build
    Pop-Location
} else {
    Write-Error "Error: lily02_frontend directory not found."
}

# 3. Final Health Check
Write-Host "`n[3/3] Environment Ready!" -ForegroundColor Green
Write-Host "`nCommands available:"
Write-Host " - 'python recovery.py' : Start Hub + Public Tunnel"
Write-Host " - 'lily02 chat'        : Launch Interactive Terminal"
Write-Host "`nMission Ready. 🐳🚀"
