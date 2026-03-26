# 仅上传文件到服务器（不执行命令）
# 使用方法: .\scripts\upload-files-only.ps1

$ErrorActionPreference = "Continue"

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"
$SSHKey = "E:\enterprise-ai-platform\enterprise_ai_platform.pem"

if (-not (Test-Path $SSHKey)) {
    Write-Host "[错误] SSH密钥文件不存在: $SSHKey" -ForegroundColor Red
    exit 1
}

$SCPOptions = "-i `"$SSHKey`" -o StrictHostKeyChecking=no"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "上传迁移文件到服务器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 上传所有迁移文件
Write-Host "上传迁移文件..." -ForegroundColor Yellow
$migrationFiles = Get-ChildItem -Path "database\src\migrations\versions" -Filter "*.py" | Sort-Object Name

$uploaded = 0
foreach ($file in $migrationFiles) {
    $localPath = $file.FullName
    $remotePath = "$ServerPath/database/src/migrations/versions/$($file.Name)"
    
    Write-Host "  上传: $($file.Name)" -ForegroundColor Gray
    & scp $SCPOptions $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $uploaded++
        Write-Host "    [OK]" -ForegroundColor Green
    } else {
        Write-Host "    [失败]" -ForegroundColor Red
    }
}

Write-Host "[OK] 已上传 $uploaded/$($migrationFiles.Count) 个迁移文件" -ForegroundColor Green

# 上传Alembic配置文件
Write-Host ""
Write-Host "上传Alembic配置文件..." -ForegroundColor Yellow

$alembicFiles = @(
    "database\src\migrations\alembic.ini",
    "database\src\migrations\env.py"
)

foreach ($file in $alembicFiles) {
    $localPath = Join-Path $PWD $file
    if (Test-Path $localPath) {
        $remotePath = "$ServerPath/database/src/migrations/$((Split-Path $file -Leaf))"
        & scp $SCPOptions $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $file" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "文件上传完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：请SSH到服务器手动执行部署命令" -ForegroundColor Yellow
Write-Host "ssh -i `"$SSHKey`" root@${ServerIP}" -ForegroundColor Gray
Write-Host ""








