<#
.SYNOPSIS
  YouTube to NotebookLM 自動化執行與同步腳本
.DESCRIPTION
  此腳本設計用於 Windows 排程工作。
  它會自動切換目錄、啟用虛擬環境、執行 main.py 和 archive_studio.py。
  最後將 processed_videos.json 變更提交並推送到 GitHub 備份。
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

# 設定日誌檔案路徑
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

Log-Info "=== 開始新的自動化排程執行 ==="

# 檢查虛擬環境並啟動
$VenvActivationPath = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivationPath) {
    Log-Info "啟動虛擬環境: $VenvActivationPath"
    . $VenvActivationPath
} else {
    Log-Error "找不到虛擬環境: $VenvActivationPath"
    exit 1
}

# 執行主要任務 1: main.py
Log-Info "執行 main.py ..."
$MainResult = Start-Process -FilePath "python" -ArgumentList "main.py" -NoNewWindow -Wait -PassThru
if ($MainResult.ExitCode -ne 0) {
    Log-Error "main.py 執行失敗 (Exit code: $($MainResult.ExitCode))"
} else {
    Log-Info "main.py 執行成功"
}

# 執行主要任務 2: archive_studio.py
Log-Info "執行 archive_studio.py ..."
$ArchiveResult = Start-Process -FilePath "python" -ArgumentList "archive_studio.py" -NoNewWindow -Wait -PassThru
if ($ArchiveResult.ExitCode -ne 0) {
    Log-Error "archive_studio.py 執行程式失敗或遇到錯誤 (Exit code: $($ArchiveResult.ExitCode))"
} else {
    Log-Info "archive_studio.py 執行成功"
}

# Github 同步作業
Log-Info "開始 GitHub 同步作業..."
# 這裡特別指定要 git add 的檔案，以防將機密的 run_logs 或 .env 加進去
git add processed_videos.json

# 檢查是否有未提交的變更
$GitStatus = git status --porcelain
if ([string]::IsNullOrWhiteSpace($GitStatus)) {
    Log-Info "沒有變更需要提交。"
} else {
    Log-Info "偵測到 processed_videos.json 有變更，準備提交..."
    git commit -m "chore(auto): update processed_videos.json from local scheduler"
    if ($LASTEXITCODE -eq 0) {
        $PushResult = git push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Log-Info "成功同步至 GitHub。"
        } else {
            Log-Error "Push 失敗: $PushResult"
        }
    } else {
        Log-Error "Commit 失敗。"
    }
}

Log-Info "=== 自動化排程執行完畢 ==="
Write-Host ""
