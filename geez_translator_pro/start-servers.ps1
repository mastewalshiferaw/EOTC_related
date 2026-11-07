<#
    start-servers.ps1
    Starts the Ge'ez translator backend (Django) and frontend (Next.js)
    from a single command using absolute paths.

    Usage:
        powershell -ExecutionPolicy Bypass -File start-servers.ps1

    Optionally override ports:
        powershell -ExecutionPolicy Bypass -File start-servers.ps1 -BackendPort 8000 -FrontendPort 3000

    Configuration (absolute path):
        $ProjectRoot = "C:\Users\Billy\Interview\experment\EOTC_related\geez_translator_pro"
#>
[CmdletBinding()]
param(
    # Backend port for Django runserver. Default 8000.
    [int]$BackendPort = 8000,
    # Frontend port for Next.js dev. Default 3000.
    [int]$FrontendPort = 3000,
    # Absolute path to the geez_translator_pro project root.
    [Parameter(Mandatory)]
    [string]$ProjectRoot = "/d/interview/experment/EOTC_related/geez_translator_pro"
)

$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"

# Resolve to full paths so the script works regardless of CWD.
$BackendDir  = Resolve-Path $BackendDir  -ErrorAction Stop
$FrontendDir = Resolve-Path $FrontendDir -ErrorAction Stop

Write-Host ('=== Ge' + "'" + 'ez Translator - starting both servers ===') -ForegroundColor Cyan
Write-Host ('Backend:  python manage.py runserver 0.0.0.0:' + $BackendPort)
Write-Host ('Frontend: npx next dev  (PORT=' + $FrontendPort + ')')
Write-Host ''

# ---- Backend (Django) ----
$env:DEBUG = 'False'
$env:DJANGO_SETTINGS_MODULE = 'core.settings'

$backendStart = New-Object System.Diagnostics.ProcessStartInfo
$backendStart.FileName = 'python'
$backendStart.Arguments = '-u manage.py runserver 0.0.0.0:' + $BackendPort
$backendStart.WorkingDirectory = $BackendDir
$backendStart.CreateNoWindow = $false
$backendStart.UseShellExecute = $false
$backendStart.RedirectStandardOutput = $true
$backendStart.RedirectStandardError = $true
$backendStart.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$backendStart.StandardErrorEncoding = [System.Text.Encoding]::UTF8

$backendProc = New-Object System.Diagnostics.Process
$backendProc.StartInfo = $backendStart
$backendProc.Start()
Start-Sleep -Seconds 1

# Persist PID so you can stop both later.
$pidFile = Join-Path (Split-Path $BackendDir) 'pid.backend.txt'
'$($backendProc.Id)' | Out-File -FilePath $pidFile -Encoding ASCII -Force
Write-Host ('Backend PID: ' + $backendProc.Id + '  ->  ' + $pidFile) -ForegroundColor Green

# Let the backend bind before launching the frontend.
Start-Sleep -Seconds 3

# ---- Frontend (Next.js) ----
$frontendStart = New-Object System.Diagnostics.ProcessStartInfo
$frontendStart.FileName = 'npx'
$frontendStart.Arguments = 'next', 'dev', '-p', $FrontendPort
$frontendStart.WorkingDirectory = $FrontendDir
$frontendStart.CreateNoWindow = $false
$frontendStart.UseShellExecute = $false
$frontendStart.RedirectStandardOutput = $true
$frontendStart.RedirectStandardError = $true
$frontendStart.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$frontendStart.StandardErrorEncoding = [System.Text.Encoding]::UTF8

$frontendProc = New-Object System.Diagnostics.Process
$frontendProc.StartInfo = $frontendStart
$frontendProc.Start()
Start-Sleep -Seconds 1
Write-Host ('Frontend PID: ' + $frontendProc.Id) -ForegroundColor Green

Write-Host '' ; Write-Host ('Both servers are up. Press Ctrl+C to stop.') -ForegroundColor Yellow
Write-Host ('Backend:  http://localhost:' + $BackendPort + '/api/health/')
Write-Host ('Frontend: http://localhost:' + $FrontendPort + '/')
Write-Host ''

# Keep the console open until the user stops the script.
try {
    while ($true) { Start-Sleep -Seconds 1 }
} catch {
    Write-Host ''; Write-Host 'Stopping servers...' -ForegroundColor Yellow
    $backendProc.CloseMainWindow() | Out-Null
    if ($frontendProc) { $frontendProc.CloseMainWindow() | Out-Null }
}
