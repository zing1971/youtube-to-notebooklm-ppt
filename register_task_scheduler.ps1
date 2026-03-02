# 此腳本將在 Windows 排程工作中建立一個任務，設定在系統啟動時自動執行 auto_run.ps1。
# 需要以管理員權限執行此腳本。

$TaskName = "YouTubeToNotebookLMSync"
$ScriptPath = Join-Path $PSScriptRoot "auto_run.ps1"
$WorkingDirectory = $PSScriptRoot

# 檢查檔案是否存在
if (-not (Test-Path $ScriptPath)) {
    Write-Error "找不到 $ScriptPath"
    exit 1
}

# 設定執行動作 (啟動 PowerShell 並執行腳本)
$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory $WorkingDirectory

# 設定觸發條件 (系統啟動時)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# 設定運行權限 (使用當前使用者帳戶)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# 設定其他任務選項 (如：避免同時執行)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# 註冊任務
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
    Write-Host "✅ 已成功建立排程工作：$TaskName"
    Write-Host "該腳本將在系統下一次開機啟動時自動背景執行。"
}
catch {
    Write-Error "❌ 建立排程工作失敗: $_"
    Write-Host "💡 提示：請嘗試以「系統管理員身分」執行此 PowerShell 視窗後再試一次。" -ForegroundColor Yellow
}
