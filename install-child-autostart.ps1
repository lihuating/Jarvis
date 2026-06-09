# 以管理员身份在 PowerShell 中运行，注册 Windows 登录自启任务
# 用法: powershell -ExecutionPolicy Bypass -File D:\code_pub\Jarvis\install-child-autostart.ps1

$TaskName = "Jarvis-Child-lht-home-windos"
$BatchPath = "D:\code_pub\Jarvis\start-child-node-wsl.bat"

if (-not (Test-Path $BatchPath)) {
    Write-Error "找不到启动脚本: $BatchPath"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $BatchPath
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force

Write-Host "已注册计划任务: $TaskName"
Write-Host "登录 Windows 时将自动执行: $BatchPath"
