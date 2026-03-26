#!/usr/bin/env pwsh
# Neo4j数据上传脚本 - 将本地Neo4j数据上传到服务器
# 使用方法: .\scripts\deployment\upload-neo4j-data-to-server.ps1

param(
    [string]$ServerIP = "43.143.90.179",
    [string]$ServerUser = "root",
    [string]$KeyPath = "",
    [string]$RemotePath = "/opt/enterprise-ai-platform",
    [string]$BackupFile = "",
    [switch]$ExportFirst = $true
)

$ErrorActionPreference = "Stop"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "📤 Neo4j数据上传到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "服务器: $ServerUser@$ServerIP" -ForegroundColor Yellow
Write-Host "远程路径: $RemotePath" -ForegroundColor Yellow
Write-Host ""

# 检查密钥文件
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ([string]::IsNullOrEmpty($KeyPath)) {
    $KeyPath = Join-Path $ProjectRoot "enterprise_ai_platform.pem"
    if (-not (Test-Path $KeyPath)) {
        $KeyPath = Join-Path $env:USERPROFILE ".ssh\enterprise_ai_platform.pem"
    }
}

if (-not (Test-Path $KeyPath)) {
    Write-Host "⚠️  未找到SSH密钥文件，将使用密码登录" -ForegroundColor Yellow
    $UsePassword = $true
} else {
    $UsePassword = $false
}

# 构建SSH和SCP命令
if ($UsePassword) {
    $sshCmd = "ssh -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"
    $scpCmd = "scp -o StrictHostKeyChecking=no"
} else {
    $sshCmd = "ssh -i `"$KeyPath`" -o StrictHostKeyChecking=no $ServerUser@${ServerIP}"
    $scpCmd = "scp -i `"$KeyPath`" -o StrictHostKeyChecking=no"
}

# 如果指定了导出，先导出数据
if ($ExportFirst -and [string]::IsNullOrEmpty($BackupFile)) {
    Write-Host "[1/4] 导出本地Neo4j数据..." -ForegroundColor Cyan
    $exportScript = Join-Path $PSScriptRoot "export-neo4j-data.ps1"
    if (Test-Path $exportScript) {
        & $exportScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ 数据导出失败" -ForegroundColor Red
            exit 1
        }
        
        # 查找最新的备份文件
        $backupDir = Join-Path $ProjectRoot "backups\neo4j"
        if (Test-Path $backupDir) {
            $latestBackup = Get-ChildItem -Path $backupDir -Filter "neo4j_backup_*.tar.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if (-not $latestBackup) {
                $latestBackup = Get-ChildItem -Path $backupDir -Filter "neo4j_backup_*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            }
            if ($latestBackup) {
                $BackupFile = $latestBackup.FullName
                Write-Host "✅ 找到最新备份文件: $BackupFile" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "⚠️  导出脚本未找到，跳过导出步骤" -ForegroundColor Yellow
    }
}

# 检查备份文件
if ([string]::IsNullOrEmpty($BackupFile) -or -not (Test-Path $BackupFile)) {
    Write-Host "❌ 未找到备份文件" -ForegroundColor Red
    Write-Host "请提供备份文件路径，或使用 -ExportFirst 参数先导出数据" -ForegroundColor Yellow
    exit 1
}

$BackupFile = Resolve-Path $BackupFile
$BackupFileName = Split-Path $BackupFile -Leaf
Write-Host "`n[2/4] 准备上传备份文件..." -ForegroundColor Cyan
Write-Host "备份文件: $BackupFile" -ForegroundColor Gray
$fileSize = [math]::Round((Get-Item $BackupFile).Length / 1MB, 2)
Write-Host "文件大小: $fileSize MB" -ForegroundColor Gray

# 检查服务器连接
Write-Host "`n[3/4] 检查服务器连接..." -ForegroundColor Cyan
try {
    $testResult = Invoke-Expression "$sshCmd 'echo Connection test successful'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "SSH连接失败"
    }
    Write-Host "✅ 服务器连接成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 服务器连接失败: $_" -ForegroundColor Red
    exit 1
}

# 创建远程备份目录
Write-Host "`n[4/4] 上传备份文件到服务器..." -ForegroundColor Cyan
$remoteBackupDir = "$RemotePath/neo4j/backups"
$createDir = "mkdir -p $remoteBackupDir"
Invoke-Expression "$sshCmd `"$createDir`"" | Out-Null

# 上传文件
Write-Host "正在上传文件（这可能需要一些时间）..." -ForegroundColor Yellow
$remoteBackupPath = "$remoteBackupDir/$BackupFileName"
Invoke-Expression "$scpCmd `"$BackupFile`" $ServerUser@${ServerIP}:$remoteBackupPath" | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 备份文件上传成功" -ForegroundColor Green
    Write-Host "   远程路径: $remoteBackupPath" -ForegroundColor Gray
} else {
    Write-Host "❌ 备份文件上传失败" -ForegroundColor Red
    exit 1
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🎉 Neo4j数据上传完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "下一步：在服务器上运行恢复脚本导入数据" -ForegroundColor Yellow
Write-Host "  恢复脚本: restore-neo4j-data-on-server.ps1" -ForegroundColor Gray
Write-Host ""

