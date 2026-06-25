$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$port = if ($args.Count -gt 0 -and $args[0]) { [int]$args[0] } else { 8000 }

$adkCmd = "adk"
$pythonCmd = "python"
$venvPath = Join-Path $root ".venv"
if (Test-Path -LiteralPath $venvPath) {
    $adkCmd = Join-Path $venvPath "Scripts\adk.exe"
    $pythonCmd = Join-Path $venvPath "Scripts\python.exe"
}

function Test-PortFree {
    param([int]$Port)

    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

if (-not (Test-PortFree -Port $port)) {
    throw "Port $port dang bi chiem. Hoi dung tien trinh dang chay hoac chay: .\start_app.ps1 8001"
}

Write-Host "Khoi dong X-Agent bang ADK tren port $port..." -ForegroundColor Cyan

# Khoi dong bo phan tu dong nap du lieu (Background)
Write-Host "Dang kich hoat bo phan tu dong nap du lieu (hot_folder)..." -ForegroundColor Yellow
Start-Process $pythonCmd -ArgumentList "scripts/auto_watcher.py" -WorkingDirectory $root -WindowStyle Hidden

# Khoi dong server xac thuc (FastAPI Auth Server) tren port 8001 (Background)
Write-Host "Dang kich hoat server xac thuc (auth_server) tren port 8001..." -ForegroundColor Yellow
$authArgs = "-m uvicorn auth_server:app --host 127.0.0.1 --port 8001"
Start-Process $pythonCmd -ArgumentList $authArgs -WorkingDirectory $root -WindowStyle Hidden

& $adkCmd web --port $port --allow_origins "http://localhost:5173"
