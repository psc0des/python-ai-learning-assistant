Param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$port = 8765

Write-Host "Restarting Python Skill Lab on port $port..." -ForegroundColor Cyan

# Stop any listener on :8765
$listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listeners) {
  $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($pid in $pids) {
    try {
      Stop-Process -Id $pid -Force -ErrorAction Stop
      Write-Host "Stopped process $pid on port $port"
    } catch {
      Write-Warning "Could not stop process $pid: $($_.Exception.Message)"
    }
  }
}

Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "app.py" -WorkingDirectory $projectRoot | Out-Null
Start-Sleep -Milliseconds 900

try {
  $resp = Invoke-WebRequest "http://127.0.0.1:$port/api/curriculum" -UseBasicParsing -TimeoutSec 3
  $json = $resp.Content | ConvertFrom-Json
  Write-Host "Started http://127.0.0.1:$port (mode=$($json.content_mode), topics=$($json.topics.Count), exercises=$($json.exercises.Count))" -ForegroundColor Green
} catch {
  Write-Warning "Server started, but health check failed: $($_.Exception.Message)"
}
