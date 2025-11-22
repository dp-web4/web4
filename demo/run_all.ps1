# PowerShell script to launch Web4 demos: store, delegation manager, and trust visualizer

$ErrorActionPreference = "Stop"

# Ports used by the demos
$ports = 8000, 8001, 8002

Write-Host "Checking for existing processes on ports: $ports" -ForegroundColor Cyan

foreach ($port in $ports) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($conns) {
            foreach ($c in $conns) {
                Write-Host "Killing process $($c.OwningProcess) on port $port" -ForegroundColor Yellow
                Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Host "Could not inspect port $port: $_" -ForegroundColor Red
    }
}

# Helper to start a process in a given working directory
function Start-Web4Process {
    param(
        [string]$Name,
        [string]$WorkingDir,
        [string]$Arguments
    )

    Write-Host "Starting $Name in $WorkingDir" -ForegroundColor Green
    Start-Process -FilePath "python" -ArgumentList $Arguments -WorkingDirectory $WorkingDir
}

# Resolve repo root relative to this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent $scriptDir

# Start store (port 8000)
Start-Web4Process -Name "Store" -WorkingDir (Join-Path $repoRoot "demo\store") -Arguments "app.py"

# Start Delegation Manager (port 8001)
Start-Web4Process -Name "Delegation Manager" -WorkingDir (Join-Path $repoRoot "demo\delegation-ui") -Arguments "app.py"

# Start static server for trust visualizer (port 8002)
Write-Host "Starting Trust Visualizer on http://localhost:8002" -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "-m http.server 8002" -WorkingDirectory (Join-Path $repoRoot "examples\trust-visualizer")

Write-Host "\nAll services starting:" -ForegroundColor Cyan
Write-Host "  Store:              http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Delegation Manager: http://localhost:8001" -ForegroundColor Cyan
Write-Host "  Trust Visualizer:   http://localhost:8002" -ForegroundColor Cyan
