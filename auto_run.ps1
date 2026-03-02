<#
.SYNOPSIS
  YouTube to NotebookLM Auto Execution Script
.DESCRIPTION
  This script is designed for Windows Task Scheduler.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$LogFile = "run_logs.txt"

Function Log-Message {
    param([string]$Level, [string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMsg = "[$Timestamp] [$Level] $Message"
    if ($Level -eq "ERROR") {
        Write-Host $LogMsg -ForegroundColor Red
    }
    else {
        Write-Host $LogMsg
    }
    Add-Content -Path $LogFile -Value $LogMsg -Encoding UTF8
}

Log-Message "INFO" "=== Start Auto Run ==="

$VenvPath = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvPath) {
    Log-Message "INFO" "Activate Venv: $VenvPath"
    . $VenvPath
}
else {
    Log-Message "INFO" "Venv not found, using global python..."
}

Log-Message "INFO" "Refreshing auth state using export_auth.py..."
$pAuth = Start-Process -FilePath "py" -ArgumentList "export_auth.py" -NoNewWindow -Wait -PassThru
if ($pAuth.ExitCode -ne 0) {
    Log-Message "ERROR" "Auth refresh failed. Browser profile might be expired. Please run 'python login_manual.py' manually."
    exit 1
}

Log-Message "INFO" "Running main.py..."
$p1 = Start-Process -FilePath "py" -ArgumentList "main.py" -NoNewWindow -Wait -PassThru
if ($p1.ExitCode -ne 0) {
    Log-Message "ERROR" "main.py failed with code $($p1.ExitCode)"
}
else {
    Log-Message "INFO" "main.py success"
}

Log-Message "INFO" "Running archive_studio.py..."
$p2 = Start-Process -FilePath "py" -ArgumentList "archive_studio.py" -NoNewWindow -Wait -PassThru
if ($p2.ExitCode -ne 0) {
    Log-Message "ERROR" "archive_studio.py failed with code $($p2.ExitCode)"
}
else {
    Log-Message "INFO" "archive_studio.py success"
}

Log-Message "INFO" "Sync GitHub..."
git add processed_videos.json
$st = git status --porcelain
if ([string]::IsNullOrWhiteSpace($st)) {
    Log-Message "INFO" "No changes to commit"
}
else {
    Log-Message "INFO" "Changes detected, committing..."
    git commit -m "chore(auto): update processed_videos.json from local scheduler"
    if ($LASTEXITCODE -eq 0) {
        $pushRes = git push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Log-Message "INFO" "Github push success"
        }
        else {
            Log-Message "ERROR" "Github push failed: $pushRes"
        }
    }
    else {
        Log-Message "ERROR" "Github commit failed"
    }
}

Log-Message "INFO" "=== End Auto Run ==="
Write-Host ""
