Param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$port = 8765

Write-Host "Restarting Python Skill Lab on port $port..." -ForegroundColor Cyan

# Stop any listener on :8765
$listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
$procIds = @()
if ($listeners) {
  $procIds += $listeners | Select-Object -ExpandProperty OwningProcess
}

# Some Windows environments do not report Python listeners through
# Get-NetTCPConnection. netstat still sees them, so use it as a fallback.
$netstatLines = netstat -ano | Select-String ":$port"
foreach ($line in $netstatLines) {
  $parts = ($line.Line -split "\s+") | Where-Object { $_ }
  if ($parts.Count -ge 5 -and $parts[1] -match ":$port$" -and $parts[3] -eq "LISTENING") {
    $procIds += [int]$parts[-1]
  }
}

$procIds = $procIds | Sort-Object -Unique
foreach ($procId in $procIds) {
  try {
    Stop-Process -Id $procId -Force -ErrorAction Stop
    Write-Host "Stopped process $procId on port $port"
  } catch {
    Write-Warning "Could not stop process ${procId}: $($_.Exception.Message)"
  }
}

for ($i = 0; $i -lt 20; $i++) {
  $stillListening = netstat -ano | Select-String ":$port" | Where-Object {
    $parts = ($_.Line -split "\s+") | Where-Object { $_ }
    $parts.Count -ge 5 -and $parts[1] -match ":$port$" -and $parts[3] -eq "LISTENING"
  }
  if (-not $stillListening) {
    break
  }
  Start-Sleep -Milliseconds 150
  if ($i -eq 19) {
    foreach ($line in $stillListening) {
      Write-Warning "Port $port is still listening: $($line.Line.Trim())"
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
