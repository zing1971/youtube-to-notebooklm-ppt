<#
.SYNOPSIS
  YouTube to NotebookLM Auto Execution Script
.DESCRIPTION
  This script is designed for Windows Task Scheduler.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$LogFile = "run_logs.txt"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Function Log-Info {
    param([string]$Message)
    $LogMsg = "[$Timestamp] [INFO] $Message"
    Write-Host $LogMsg
    Add-Content -Path $LogFile -Value $LogMsg -Encoding UTF8
}

Function Log-Error {
    param([string]$Message)
    $LogMsg = "[$Timestamp] [ERROR] $Message"
    Write-Host $LogMsg -ForegroundColor Red
    Add-Content -Path $LogFile -Value $LogMsg -Encoding UTF8
}

Log-Info "=== Starting New Automation Execution ==="

$VenvActivationPath = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivationPath) {
    Log-Info "Activating Venv: $VenvActivationPath"
    . $VenvActivationPath
}
else {
    Log-Info "Venv not found, using global python..."
}

Log-Info "Running main.py ..."
$MainResult = Start-Process -FilePath "python" -ArgumentList "main.py" -NoNewWindow -Wait -PassThru
if ($MainResult.ExitCode -ne 0) {
    Log-Error "main.py failed (Exit code: $($MainResult.ExitCode))"
}
else {
    Log-Info "main.py succeeded"
}

Log-Info "Running archive_studio.py ..."
$ArchiveResult = Start-Process -FilePath "python" -ArgumentList "archive_studio.py" -NoNewWindow -Wait -PassThru
if ($ArchiveResult.ExitCode -ne 0) {
    Log-Error "archive_studio.py failed (Exit code: $($ArchiveResult.ExitCode))"
}
else {
    Log-Info "archive_studio.py succeeded"
}

Log-Info "Starting GitHub sync..."
git add processed_videos.json

$GitStatus = git status --porcelain
if ([string]::IsNullOrWhiteSpace($GitStatus)) {
    Log-Info "No changes to commit."
}
else {
    Log-Info "Changes detected, committing..."
    git commit -m "chore(auto): update processed_videos.json from local scheduler"
    if ($LASTEXITCODE -eq 0) {
        $PushResult = git push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Log-Info "Successfully pushed to GitHub."
        }
        else {
            Log-Error "Push failed: $PushResult"
        }
    }
    else {
        Log-Error "Commit failed."
    }
}

Log-Info "=== Automation Execution Finished ==="
Write-Host ""
