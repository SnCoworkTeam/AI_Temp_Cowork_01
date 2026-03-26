# 上传同步包到服务器

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerHost = "root@43.143.139.197",
    
    [string]$ServerPath = "/opt/enterprise-ai-platform/backups",
    
    [string]$PackagePath = ""
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传同步包到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 如果没有指定包路径，查找最新的
if ([string]::IsNullOrEmpty($PackagePath)) {
    $Package = Get-ChildItem -Path "backups\sync" -Filter "metadata_knowledge_sync_*.tar.gz" | 
        Sort-Object LastWriteTime -Descending | 
        Select-Object -First 1
    
    if (-not $Package) {
        Write-Host "[错误] 未找到同步包" -ForegroundColor Red
        Write-Host "请先运行同步脚本创建同步包" -ForegroundColor Yellow
        exit 1
    }
    
    $PackagePath = $Package.FullName
}

if (-not (Test-Path $PackagePath)) {
    Write-Host "[错误] 同步包不存在: $PackagePath" -ForegroundColor Red
    exit 1
}

$PackageInfo = Get-Item $PackagePath
Write-Host "[信息] 同步包: $($PackageInfo.Name)" -ForegroundColor Cyan
Write-Host "  大小: $([math]::Round($PackageInfo.Length/1MB,2)) MB" -ForegroundColor Gray
Write-Host "  路径: $PackagePath" -ForegroundColor Gray
Write-Host ""

Write-Host "[上传] 上传到服务器..." -ForegroundColor Cyan
Write-Host "  目标: $ServerHost`:$ServerPath" -ForegroundColor Yellow
Write-Host ""

# 测试SSH连接
Write-Host "[检查] 测试SSH连接..." -ForegroundColor Cyan
try {
    $sshTest = ssh -o ConnectTimeout=5 -o BatchMode=yes $ServerHost "echo 'SSH连接成功'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] SSH连接正常" -ForegroundColor Green
    } else {
        Write-Host "  [警告] SSH连接测试失败，但继续尝试上传" -ForegroundColor Yellow
        Write-Host "  如果上传失败，请检查SSH密钥配置" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [警告] SSH连接测试失败: $_" -ForegroundColor Yellow
}

Write-Host ""

# 创建服务器目录（如果不存在）
Write-Host "[准备] 确保服务器目录存在..." -ForegroundColor Cyan
ssh $ServerHost "mkdir -p $ServerPath" 2>&1 | Out-Null

# 上传文件
Write-Host "[上传] 开始上传..." -ForegroundColor Cyan
$RemotePath = "$ServerHost`:$ServerPath/$($PackageInfo.Name)"

try {
    scp $PackagePath $RemotePath 2>&1 | ForEach-Object {
        if ($_ -match "Permission denied" -or $_ -match "denied") {
            Write-Host "  [错误] SSH权限被拒绝" -ForegroundColor Red
            Write-Host "  请检查:" -ForegroundColor Yellow
            Write-Host "    1. SSH密钥是否已配置" -ForegroundColor Yellow
            Write-Host "    2. 服务器用户是否有权限" -ForegroundColor Yellow
            Write-Host "    3. 尝试手动上传:" -ForegroundColor Yellow
            Write-Host "       scp $PackagePath $RemotePath" -ForegroundColor Cyan
        } elseif ($_ -match "100%") {
            Write-Host "  $_" -ForegroundColor Green
        } else {
            Write-Host "  $_" -ForegroundColor Gray
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[成功] 上传完成！" -ForegroundColor Green
        Write-Host "  服务器路径: $ServerPath/$($PackageInfo.Name)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "下一步: 在服务器上运行恢复脚本" -ForegroundColor Yellow
        Write-Host "  .\scripts\restore_metadata_knowledge_from_sync.ps1 -SyncPackage `"$ServerPath/$($PackageInfo.Name)`"" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[失败] 上传失败 (退出码: $LASTEXITCODE)" -ForegroundColor Red
        Write-Host ""
        Write-Host "手动上传命令:" -ForegroundColor Yellow
        Write-Host "  scp `"$PackagePath`" $RemotePath" -ForegroundColor Cyan
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "[错误] 上传过程出错: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""


