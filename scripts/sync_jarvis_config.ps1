#!/usr/bin/env pwsh

# sync_jarvis_config.ps1
# 用于将全局配置同步到当前工程目录的 .jarvis/ 子目录
# 用法: .\sync_jarvis_config.ps1 [-Force]

param(
    [switch]$Force,    # 强制覆盖，不询问确认
    [switch]$Help      # 显示帮助
)

# 颜色定义
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    $colorMap = @{
        "Red" = "31"
        "Green" = "32"
        "Yellow" = "33"
        "Blue" = "34"
        "White" = "37"
    }
    $code = $colorMap[$Color]
    Write-Host "$([char]27)[${code}m${Message}$([char]27)[0m" -NoNewline
    Write-Host ""
}

# 显示帮助
if ($Help) {
    Write-Host "用法: .\sync_jarvis_config.ps1 [-Force] [-Help]"
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  -Force    强制覆盖，不询问确认"
    Write-Host "  -Help     显示此帮助信息"
    exit 0
}

$SourceDir = "$HOME\.jarvis"
# 目标目录：使用独立的 .jarvis_config 目录，避免与项目 .jarvis 混在一起
$TargetDir = ".jarvis_config"

Write-ColorOutput "========================================" "Blue"
Write-ColorOutput "  Jarvis 全局配置同步工具 (PowerShell)" "Blue"
Write-ColorOutput "========================================" "Blue"
Write-Host ""

# 检查源目录
if (-not (Test-Path $SourceDir -PathType Container)) {
    Write-ColorOutput "错误: 源目录不存在: $SourceDir" "Red"
    Write-Host "请确保 Jarvis 已正确安装并运行过"
    exit 1
}

# 检查目标目录
if (-not (Test-Path $TargetDir -PathType Container)) {
    Write-ColorOutput "警告: 目标目录不存在: $TargetDir" "Yellow"
    Write-Host "正在创建目录..."
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    Write-ColorOutput "目录已创建" "Green"
}

# 显示同步信息
Write-ColorOutput "同步信息:" "Yellow"
Write-Host "  源目录: $SourceDir"
Write-Host "  目标目录: $TargetDir"
Write-Host ""

# 定义要同步的内容
$SyncItems = @(
    @{ Name = "config.yaml"; Desc = "全局配置" },
    @{ Name = "memory"; Desc = "记忆存储" },
    @{ Name = "methodologies"; Desc = "方法论" },
    @{ Name = "rules"; Desc = "规则" },
    @{ Name = "tools"; Desc = "自定义工具" }
)

Write-ColorOutput "将要同步以下内容:" "Yellow"
foreach ($item in $SyncItems) {
    $srcPath = Join-Path $SourceDir $item.Name
    if (Test-Path $srcPath) {
        Write-ColorOutput "  [OK] $($item.Desc)" "Green"
    } else {
        Write-ColorOutput "  [--] $($item.Desc) (不存在，将跳过)" "Yellow"
    }
}
Write-Host ""

# 确认操作
if (-not $Force) {
    $response = Read-Host "是否继续同步? [y/N]"
    if ($response -notmatch "^[yY]$") {
        Write-Host "已取消同步"
        exit 0
    }
}

Write-Host "开始同步..."
Write-Host ""

# 创建目录结构
$requiredDirs = @("memory", "methodologies", "rules", "tools")
foreach ($dir in $requiredDirs) {
    $targetPath = Join-Path $TargetDir $dir
    if (-not (Test-Path $targetPath)) {
        New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
    }
}

# 同步函数
function Sync-Item {
    param(
        [string]$Src,
        [string]$Dst,
        [string]$Name
    )
    
    if (-not (Test-Path $Src)) {
        Write-ColorOutput "跳过: $Name (源不存在)" "Yellow"
        return
    }
    
    if (Test-Path $Src -PathType Container) {
        # 目录同步
        $items = Get-ChildItem $Src -Force | Where-Object { $_.Name -ne '__pycache__' }
        if ($items) {
            Copy-Item -Path "$Src\*" -Destination $Dst -Recurse -Force -ErrorAction SilentlyContinue
            # 移除 __pycache__ 目录
            Get-ChildItem $Dst -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Write-ColorOutput "已同步目录: $Name" "Green"
        } else {
            Write-ColorOutput "目录为空: $Name" "Yellow"
        }
    } else {
        # 文件同步
        Copy-Item -Path $Src -Destination $Dst -Force
        Write-ColorOutput "已同步文件: $Name" "Green"
    }
}

# 执行同步
Write-ColorOutput "开始同步..." "Blue"
Write-Host ""

# 同步配置文件
$configSrc = Join-Path $SourceDir "config.yaml"
$configDst = Join-Path $TargetDir "config.yaml"
Sync-Item -Src $configSrc -Dst $configDst -Name "config.yaml"

# 同步记忆目录
$memorySrc = Join-Path $SourceDir "memory"
if (Test-Path $memorySrc -PathType Container) {
    $subDirs = Get-ChildItem $memorySrc -Directory
    foreach ($subDir in $subDirs) {
        $targetSubDir = Join-Path $TargetDir "memory\$($subDir.Name)"
        if (-not (Test-Path $targetSubDir)) {
            New-Item -ItemType Directory -Path $targetSubDir -Force | Out-Null
        }
        Sync-Item -Src $subDir.FullName -Dst "$targetSubDir\" -Name "memory/$($subDir.Name)"
    }
    
    # 同步 memory 目录下的直接文件
    $memoryFiles = Get-ChildItem $memorySrc -File -Filter "*.json"
    foreach ($file in $memoryFiles) {
        $targetPath = Join-Path (Join-Path $TargetDir "memory") $file.Name
        Copy-Item -Path $file.FullName -Destination $targetPath -Force
        Write-ColorOutput "已同步文件: memory/$($file.Name)" "Green"
    }
}

# 同步方法论
Sync-Item -Src (Join-Path $SourceDir "methodologies") -Dst (Join-Path $TargetDir "methodologies\") -Name "methodologies"

# 同步规则
Sync-Item -Src (Join-Path $SourceDir "rules") -Dst (Join-Path $TargetDir "rules\") -Name "rules"

# 同步工具
Sync-Item -Src (Join-Path $SourceDir "tools") -Dst (Join-Path $TargetDir "tools\") -Name "tools"

Write-Host ""
Write-ColorOutput "========================================" "Blue"
Write-ColorOutput "同步完成!" "Green"
Write-ColorOutput "========================================" "Blue"
Write-Host ""
Write-Host "配置已同步到: $(Get-Location)\$TargetDir"
Write-Host ""
Write-Host "提示:"
Write-Host "  - 如果需要恢复，请使用反向同步"
Write-Host "  - 或直接将 $TargetDir 目录复制到其他电脑的 ~\.jarvis\"
