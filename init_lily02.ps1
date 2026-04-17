# -----------------------------------------------------------------------------
# Lily02 Scientific Workstation - Initialization & Environment Orchestrator
# Author: Elite Engineering Layer (v2.2.1)
# -----------------------------------------------------------------------------

$ErrorActionPreference = "Stop"
$StartTime = Get-Date

Write-Host "`n  _      _ _             ___ ___  " -ForegroundColor Cyan
Write-Host " | |    (_) |           / _ \__ \ " -ForegroundColor Cyan
Write-Host " | |     _| |_   _ ___ | | | | ) |" -ForegroundColor Cyan
Write-Host " | |    | | | | | / _ \| | | |/ / " -ForegroundColor Cyan
Write-Host " | |____| | | |_| | (_) | |_| / /_ " -ForegroundColor Cyan
Write-Host " |______|_|_|\__, |\___/ \___/____|" -ForegroundColor Cyan
Write-Host "              __/ |                " -ForegroundColor Cyan
Write-Host "             |___/                 " -ForegroundColor Cyan
Write-Host "`n[Mission Control] Initializing Scientific Stack...`n" -ForegroundColor Gray

# --- [ Pre-Flight Checks ] ---
try {
    $ProjectRoot = $PSScriptRoot
    if (-not $ProjectRoot) { $ProjectRoot = Get-Location }
    Set-Location $ProjectRoot
    
    Write-Host "[Check] System Root Detected: $ProjectRoot" -ForegroundColor Gray
    
    # Check Python
    $pythonVer = python --version 2>$null
    if ($null -eq $pythonVer) { throw "Python not found in PATH." }
    Write-Host "[Check] $pythonVer detected." -ForegroundColor Green
    
    # Check Node
    $nodeVer = node --version 2>$null
    if ($null -eq $nodeVer) { throw "Node.js not found in PATH." }
    Write-Host "[Check] Node $nodeVer detected." -ForegroundColor Green

} catch {
    Write-Host "`n[FATAL] Pre-flight check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# --- [ Step 1: Python Dependency Layer ] ---
Write-Host "`n[1/3] Synchronizing Dependency Manifest..." -ForegroundColor Yellow
try {
    # We use --upgrade to ensure the latest patch-compatible versions for stability
    python -m pip install --upgrade pip
    pip install -r requirements.txt --quiet
    pip install -e . --quiet
    Write-Host "    > Python environment calibrated successfully." -ForegroundColor Gray
} catch {
    Write-Host "    > Dependency installation failed. Check internet or permissions." -ForegroundColor Red
}

# --- [ Step 2: Frontend Asset Compilation ] ---
Write-Host "`n[2/3] Compiling Scientific UI (React + Vite)..." -ForegroundColor Yellow
if (Test-Path "lily02_frontend") {
    Push-Location "lily02_frontend"
    npm install --silent
    npm run build --silent
    Pop-Location
    Write-Host "    > UI Assets optimized for production." -ForegroundColor Gray
} else {
    Write-Host "    > Frontend source not found. Skipping UI build." -ForegroundColor Red
}

# --- [ Step 3: Deployment Summary ] ---
$Duration = (Get-Date) - $StartTime
Write-Host "`n[3/3] Deployment Finalized in $($Duration.Seconds)s." -ForegroundColor Green
Write-Host "`n-----------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host " LILY02 MISSION DASHBOARD" -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host " * Start Hub     : [ python recovery.py ]" -ForegroundColor White
Write-Host " * Launch UI     : [ lily02 hub ]" -ForegroundColor White
Write-Host " * CLI Mission   : [ lily02 chat ]" -ForegroundColor White
Write-Host "-----------------------------------------------------------------------------`n" -ForegroundColor Gray

Write-Host "Elite Status: System Operational. �🚀`n" -ForegroundColor Green
