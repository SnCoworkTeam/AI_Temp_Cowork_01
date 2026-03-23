# 解决迁移版本冲突并执行迁移
# 使用方法: .\scripts\resolve-migration-conflicts.ps1

$ErrorActionPreference = "Continue"

$ServerIP = "43.143.139.197"
$ServerUser = "root"
$ServerPath = "/opt/enterprise-ai-platform"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "解决迁移版本冲突并执行迁移" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查服务器当前状态
Write-Host "[1/7] 检查服务器当前迁移状态..." -ForegroundColor Yellow
$currentVersion = ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c 'SELECT version_num FROM alembic_version;'"
$currentVersion = $currentVersion.Trim()
Write-Host "当前数据库版本: $currentVersion" -ForegroundColor Gray

# 检查是否有多个heads
Write-Host ""
Write-Host "[2/7] 检查迁移heads..." -ForegroundColor Yellow
$headsOutput = ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic heads' 2>&1"
Write-Host $headsOutput -ForegroundColor Gray

# 检查heads输出
$headsList = ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic heads 2>&1'"
$headsList = $headsList.Trim()

# 计算heads数量（每行一个head）
$headLines = $headsList -split "`n" | Where-Object { $_.Trim() -match '^[a-f0-9]+$|^[0-9]+$|^[a-f0-9]+_[a-z_]+$' }
$headCount = ($headLines | Measure-Object).Count

if ($headCount -gt 1) {
    Write-Host "[警告] 检测到 $headCount 个heads，需要合并" -ForegroundColor Yellow
    Write-Host "Heads列表:" -ForegroundColor Gray
    $headLines | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    
    # 创建合并迁移
    Write-Host ""
    Write-Host "[3/7] 创建合并迁移..." -ForegroundColor Yellow
    $mergeResult = ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic merge -m \"merge_heads_for_028\" heads' 2>&1"
    Write-Host $mergeResult -ForegroundColor Gray
    
    if ($LASTEXITCODE -eq 0 -or $mergeResult -match "already exists" -or $mergeResult -match "Created new revision") {
        Write-Host "[OK] 合并迁移处理完成" -ForegroundColor Green
    } else {
        Write-Host "[警告] 合并可能失败，但继续尝试迁移..." -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] 没有检测到多个heads (当前heads: $headsList)" -ForegroundColor Green
}

# 步骤4: 检查字段是否已存在
Write-Host ""
Write-Host "[4/7] 检查字段是否已存在..." -ForegroundColor Yellow
$fieldCheck = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';\"" | Out-String
$fieldCheck = $fieldCheck.Trim()

if ([int]$fieldCheck -gt 0) {
    Write-Host "[警告] 字段已存在，检查索引..." -ForegroundColor Yellow
    
    # 检查索引
    $indexCheck = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c \"SELECT COUNT(*) FROM pg_indexes WHERE indexname = 'idx_data_assets_business_domain';\"" | Out-String
    $indexCheck = $indexCheck.Trim()
    
    if ([int]$indexCheck -gt 0) {
        Write-Host "[信息] 字段和索引都已存在，只需更新alembic版本" -ForegroundColor Cyan
        
        # 更新alembic版本到028
        Write-Host ""
        Write-Host "[5/7] 更新alembic版本..." -ForegroundColor Yellow
        ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c \"UPDATE alembic_version SET version_num = '028';\""
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Alembic版本已更新为028" -ForegroundColor Green
            Write-Host ""
            Write-Host "==========================================" -ForegroundColor Cyan
            Write-Host "迁移完成！" -ForegroundColor Green
            Write-Host "==========================================" -ForegroundColor Cyan
            exit 0
        } else {
            Write-Host "[错误] 更新版本失败" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[信息] 字段存在但索引缺失，需要创建索引" -ForegroundColor Yellow
        Write-Host "执行迁移以创建索引..." -ForegroundColor Gray
    }
} else {
    Write-Host "[OK] 字段不存在，需要执行完整迁移" -ForegroundColor Green
}

# 步骤5: 上传修复后的迁移文件
Write-Host ""
Write-Host "[5/7] 上传迁移文件..." -ForegroundColor Yellow

$files = @(
    "database\src\migrations\versions\028_add_classification_dimensions.py"
)

foreach ($file in $files) {
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
        }
    }
}

# 步骤6: 执行迁移
Write-Host ""
Write-Host "[6/7] 执行数据库迁移..." -ForegroundColor Yellow
Write-Host "这可能需要一些时间..." -ForegroundColor Gray

$migrationResult = ssh "${ServerUser}@${ServerIP}" "cd $ServerPath && docker-compose run --rm -e DB_HOST=postgres -e DB_PORT=5432 -e DB_USER=ai_user -e DB_PASSWORD=ai_password -e DB_NAME=ai_platform metadata-service sh -c 'cd /database/src/migrations && alembic upgrade head' 2>&1"

Write-Host $migrationResult -ForegroundColor Gray

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] 数据库迁移成功完成！" -ForegroundColor Green
    
    # 步骤7: 验证迁移结果
    Write-Host ""
    Write-Host "[7/7] 验证迁移结果..." -ForegroundColor Yellow
    $newVersion = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c 'SELECT version_num FROM alembic_version;'"
    $newVersion = $newVersion.Trim()
    Write-Host "新版本: $newVersion" -ForegroundColor Gray
    
    # 验证字段
    $fieldVerify = ssh "${ServerUser}@${ServerIP}" "docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -t -A -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions';\"" | Out-String
    $fieldVerify = $fieldVerify.Trim()
    
    if ([int]$fieldVerify -gt 0) {
        Write-Host "[OK] 字段验证通过" -ForegroundColor Green
    } else {
        Write-Host "[警告] 字段验证失败" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "[错误] 数据库迁移失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "请查看错误信息，或参考 docs/deployment/migration-troubleshooting.md 进行手动修复" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "迁移完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 重启服务: ssh ${ServerUser}@${ServerIP} 'cd $ServerPath && docker-compose restart metadata-service web-ui'" -ForegroundColor Gray
Write-Host "2. 测试迁移API: curl -X GET http://${ServerIP}:8005/api/classification/migration/preview?limit=10" -ForegroundColor Gray
Write-Host "3. 访问前端: http://${ServerIP}:3000/admin/metadata" -ForegroundColor Gray
Write-Host ""








