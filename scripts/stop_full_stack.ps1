$ErrorActionPreference = "SilentlyContinue"

$root = Split-Path -Parent $PSScriptRoot
$logsDir = Join-Path $root "logs"
$backendPidFile = Join-Path $logsDir "backend.pid"
$frontendPidFile = Join-Path $logsDir "frontend.pid"

foreach ($pidFile in @($backendPidFile, $frontendPidFile)) {
    if (-not (Test-Path $pidFile)) {
        continue
    }

    $pidValue = Get-Content $pidFile
    if ($pidValue) {
        Stop-Process -Id $pidValue -Force
    }

    Remove-Item $pidFile -Force
}

Write-Output "Stack detenida."
