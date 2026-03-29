$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$logsDir = Join-Path $root "logs"
$backendPidFile = Join-Path $logsDir "backend.pid"
$frontendPidFile = Join-Path $logsDir "frontend.pid"

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

if (-not $env:ADMIN_JWT_SECRET) {
    $env:ADMIN_JWT_SECRET = "club-amsterdam-local-admin-secret"
}

if (-not $env:ADMIN_JWT_EXPIRE_MINUTES) {
    $env:ADMIN_JWT_EXPIRE_MINUTES = "720"
}

$backendPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $backendPython)) {
    throw "No se encontro el Python de la venv en $backendPython"
}

function Start-ServiceProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string]$Arguments,
        [string]$WorkingDirectory,
        [string]$PidFile
    )

    if (Test-Path $PidFile) {
        $existingPid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($existingPid) {
            $existing = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
            if ($existing) {
                Write-Output "$Name ya estaba corriendo con PID $existingPid"
                return
            }
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }

    $stdout = Join-Path $logsDir "$Name.out.log"
    $stderr = Join-Path $logsDir "$Name.err.log"

    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru

    Set-Content -Path $PidFile -Value $process.Id
    Write-Output "$Name iniciado con PID $($process.Id)"
}

Start-ServiceProcess `
    -Name "backend" `
    -FilePath $backendPython `
    -Arguments "-m uvicorn main:app --host 127.0.0.1 --port 8000" `
    -WorkingDirectory $root `
    -PidFile $backendPidFile

Start-ServiceProcess `
    -Name "frontend" `
    -FilePath "cmd.exe" `
    -Arguments "/c npm run dev -- --hostname 127.0.0.1 --port 3000" `
    -WorkingDirectory (Join-Path $root "booking-frontend") `
    -PidFile $frontendPidFile

Write-Output "Stack iniciada. Backend: http://127.0.0.1:8000 - Frontend: http://127.0.0.1:3000"
