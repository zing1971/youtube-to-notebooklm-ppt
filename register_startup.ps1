# This script creates a shortcut in the Windows Startup folder to run auto_run.ps1 on login.
# 此腳本將在 Windows 啟動資料夾中建立一個捷徑，設定在登入時自動執行 auto_run.ps1。

$ShortcutPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\YouTubeToNotebookLM.lnk"
$ScriptPath = Join-Path $PSScriptRoot "auto_run.ps1"

# Check if script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Could not find file: $ScriptPath"
    exit 1
}

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "powershell.exe"
    # Escaping quotes properly for the path
    $Shortcut.Arguments = "-WindowStyle Hidden -ExecutionPolicy Bypass -File ""$ScriptPath"""
    $Shortcut.WorkingDirectory = $PSScriptRoot
    $Shortcut.WindowStyle = 7 # Minimized
    $Shortcut.Save()
    
    Write-Host "Success! Created shortcut: $ShortcutPath"
    Write-Host "This script will now run automatically next time you log in."
}
catch {
    Write-Error "Failed to create shortcut: $_"
}
