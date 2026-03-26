# 同步迁移版本，确保本地和服务器一致
# 使用方法: .\scripts\sync-migration-versions.ps1

$ErrorActionPreference = "Continue"

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "同步迁移版本（本地 ↔ 服务器）" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查服务器当前版本
Write-Host "[1/8] 检查服务器当前迁移版本..." -ForegroundColor Yellow
$serverVersion = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c 'SELECT version_num FROM alembic_version;'" 2>&1
$serverVersion = $serverVersion.Trim()
Write-Host "服务器版本: $serverVersion" -ForegroundColor Gray

# 步骤2: 检查服务器heads
Write-Host ""
Write-Host "[2/8] 检查服务器迁移heads..." -ForegroundColor Yellow
$serverHeadsCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic heads' 2>&1"
$serverHeads = ssh "${ServerUser}@${ServerIP}" $serverHeadsCmd
Write-Host "服务器heads:" -ForegroundColor Gray
Write-Host $serverHeads -ForegroundColor Gray

# 解析heads
$serverHeadLines = $serverHeads -split "`n" | Where-Object { $_.Trim() -match '^[a-f0-9]+$|^[0-9]+$|^[a-f0-9]+_[a-z_]+$' }
$serverHeadCount = ($serverHeadLines | Measure-Object).Count

# 步骤3: 检查本地heads（通过查看迁移文件）
Write-Host ""
Write-Host "[3/8] 检查本地迁移文件..." -ForegroundColor Yellow
$localMigrationFiles = Get-ChildItem -Path "database\src\migrations\versions" -Filter "*.py" | Where-Object { $_.Name -match '^\d{3}_|^[a-f0-9]+_' } | Sort-Object Name
Write-Host "本地迁移文件数量: $($localMigrationFiles.Count)" -ForegroundColor Gray

# 检查028文件是否存在
$migration028 = $localMigrationFiles | Where-Object { $_.Name -match '028_' }
if ($migration028) {
    Write-Host "[OK] 本地存在028迁移文件: $($migration028.Name)" -ForegroundColor Green
} else {
    Write-Host "[错误] 本地不存在028迁移文件" -ForegroundColor Red
    exit 1
}

# 步骤4: 解决版本冲突
if ($serverHeadCount -gt 1) {
    Write-Host ""
    Write-Host "[4/8] 检测到 $serverHeadCount 个heads，需要合并..." -ForegroundColor Yellow
    Write-Host "Heads列表:" -ForegroundColor Gray
    $serverHeadLines | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    
    # 创建合并迁移
    Write-Host ""
    Write-Host "创建合并迁移..." -ForegroundColor Yellow
    $mergeCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c `"cd /database/src/migrations && alembic merge -m 'merge_heads_before_028' heads`" 2>&1"
    $mergeResult = ssh "${ServerUser}@${ServerIP}" $mergeCmd
    Write-Host $mergeResult -ForegroundColor Gray
    
    if ($LASTEXITCODE -eq 0 -or $mergeResult -match "already exists" -or $mergeResult -match "Created new revision") {
        Write-Host "[OK] 合并迁移处理完成" -ForegroundColor Green
    } else {
        Write-Host "[警告] 合并可能失败，继续..." -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "[4/8] [OK] 没有版本冲突 (heads: $serverHeadCount)" -ForegroundColor Green
}

# 步骤5: 检查服务器上028迁移文件的down_revision
Write-Host ""
Write-Host "[5/8] 检查服务器上028迁移文件的父版本..." -ForegroundColor Yellow
$server028File = ssh "${ServerUser}@${ServerIP}" "cat $ServerPath/database/src/migrations/versions/028_add_classification_dimensions.py 2>/dev/null | grep 'down_revision' | head -1"
if ($server028File) {
    Write-Host "服务器028文件down_revision: $server028File" -ForegroundColor Gray
} else {
    Write-Host "[信息] 服务器上不存在028文件，需要上传" -ForegroundColor Yellow
}

# 检查当前数据库版本是否与028的down_revision匹配
$local028Content = Get-Content "database\src\migrations\versions\028_add_classification_dimensions.py" -Raw
$downRevisionPattern = "down_revision\s*=\s*['`"](\w+)['`"]"
if ($local028Content -match $downRevisionPattern) {
    $expectedParent = $matches[1]
    Write-Host "本地028期望的父版本: $expectedParent" -ForegroundColor Gray
    
    # 如果服务器版本不匹配，需要先升级到匹配的版本
    if ($serverVersion -ne $expectedParent -and $serverVersion -ne "028") {
        Write-Host "[警告] 服务器版本($serverVersion)与期望的父版本($expectedParent)不匹配" -ForegroundColor Yellow
        Write-Host "需要先升级到 $expectedParent 或创建合并迁移" -ForegroundColor Yellow
    }
}

# 步骤6: 上传所有必要的迁移文件
Write-Host ""
Write-Host "[6/8] 上传迁移文件到服务器..." -ForegroundColor Yellow

$filesToUpload = @(
    "database\src\migrations\versions\028_add_classification_dimensions.py"
)

foreach ($file in $filesToUpload) {
    $localPath = Join-Path $PWD $file
    if (Test-Path $localPath) {
        $remotePath = "$ServerPath/$($file.Replace('\', '/'))"
        $remoteDir = Split-Path $remotePath -Parent
        
        # 确保远程目录存在
        ssh "${ServerUser}@${ServerIP}" "mkdir -p `"$remoteDir`"" | Out-Null
        
        Write-Host "  上传: $file" -ForegroundColor Gray
        scp -q $localPath "${ServerUser}@${ServerIP}:$remotePath" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $file" -ForegroundColor Green
        } else {
            Write-Host "  [错误] $file 上传失败" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  [错误] 本地文件不存在: $file" -ForegroundColor Red
        exit 1
    }
}

# 步骤7: 检查字段是否已存在
Write-Host ""
Write-Host "[7/8] 检查数据库字段状态..." -ForegroundColor Yellow
$fieldCheck = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';\"" 2>&1
$fieldCheck = $fieldCheck.Trim()

if ([int]$fieldCheck -gt 0) {
    Write-Host "[信息] 字段已存在，检查是否需要更新版本号" -ForegroundColor Cyan
    
    # 如果字段存在但版本不是028，更新版本号
    if ($serverVersion -ne "028") {
        Write-Host "更新alembic版本号为028..." -ForegroundColor Yellow
        ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \"UPDATE alembic_version SET version_num = '028';\"" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] 版本号已更新为028" -ForegroundColor Green
        }
    } else {
        Write-Host "[OK] 版本号已经是028" -ForegroundColor Green
    }
} else {
    Write-Host "[信息] 字段不存在，需要执行迁移" -ForegroundColor Yellow
}

# 步骤8: 执行迁移
Write-Host ""
Write-Host "[8/8] 执行数据库迁移..." -ForegroundColor Yellow
Write-Host "这可能需要一些时间，请耐心等待..." -ForegroundColor Gray

$migrationCmd = "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head' 2>&1"
$migrationResult = ssh "${ServerUser}@${ServerIP}" $migrationCmd

Write-Host $migrationResult -ForegroundColor Gray

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] 数据库迁移执行完成！" -ForegroundColor Green
    
    # 验证最终版本
    Write-Host ""
    Write-Host "验证最终状态..." -ForegroundColor Yellow
    $finalVersion = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c 'SELECT version_num FROM alembic_version;'" 2>&1
    $finalVersion = $finalVersion.Trim()
    Write-Host "最终数据库版本: $finalVersion" -ForegroundColor Gray
    
    # 验证字段
    $fieldVerify = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';\"" 2>&1
    $fieldVerify = $fieldVerify.Trim()
    
    if ([int]$fieldVerify -gt 0) {
        Write-Host "[OK] 字段验证通过" -ForegroundColor Green
    } else {
        Write-Host "[警告] 字段验证失败" -ForegroundColor Yellow
    }
    
    # 验证heads
    $finalHeads = ssh "${ServerUser}@${ServerIP}" $serverHeadsCmd
    $finalHeadLines = $finalHeads -split "`n" | Where-Object { $_.Trim() -match '^[a-f0-9]+$|^[0-9]+$|^[a-f0-9]+_[a-z_]+$' }
    $finalHeadCount = ($finalHeadLines | Measure-Object).Count
    
    Write-Host "最终heads数量: $finalHeadCount" -ForegroundColor Gray
    if ($finalHeadCount -eq 1) {
        Write-Host "[OK] 版本冲突已解决，只有一个head" -ForegroundColor Green
    } else {
        Write-Host "[警告] 仍有 $finalHeadCount 个heads" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "版本同步完成！" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "服务器版本: $finalVersion" -ForegroundColor Gray
    Write-Host "本地期望版本: 028" -ForegroundColor Gray
    if ($finalVersion -eq "028") {
        Write-Host "[✓] 版本已同步" -ForegroundColor Green
    } else {
        Write-Host "[!] 版本不一致，请检查" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "下一步：" -ForegroundColor Yellow
    Write-Host "1. 重启服务: ssh ${ServerUser}@${ServerIP} 'cd $ServerPath && docker-compose restart metadata-service web-ui'" -ForegroundColor Gray
    Write-Host "2. 测试API: curl -X GET http://${ServerIP}:8005/api/classification/migration/preview?limit=10" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[错误] 数据库迁移失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "错误信息:" -ForegroundColor Yellow
    Write-Host $migrationResult -ForegroundColor Red
    Write-Host ""
    Write-Host "请参考 docs/deployment/migration-troubleshooting.md 进行手动修复" -ForegroundColor Yellow
    exit 1
}








