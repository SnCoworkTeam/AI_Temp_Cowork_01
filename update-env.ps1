# 更新.env文件脚本
# 自动添加缺失的配置项（如果.env文件存在）

$envFile = ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "❌ .env 文件不存在！" -ForegroundColor Red
    Write-Host "请先创建 .env 文件: cp env.example .env" -ForegroundColor Yellow
    exit 1
}

Write-Host "更新 .env 文件..." -ForegroundColor Cyan

$envContent = Get-Content $envFile -Raw
$updated = $false

# 需要添加的配置项
$configsToAdd = @{
    "METADATA_SERVICE_PORT" = "8005"
    "NEXT_PUBLIC_METADATA_SERVICE_URL" = "http://localhost:8005"
    "METADATA_SERVICE_URL" = "http://metadata-service:8005"
}

# 检查并添加缺失的配置
foreach ($key in $configsToAdd.Keys) {
    if ($envContent -notmatch "$key\s*=") {
        Write-Host "添加配置: $key=$($configsToAdd[$key])" -ForegroundColor Yellow
        
        # 找到合适的位置插入（在Knowledge Base配置之后）
        if ($envContent -match "(KNOWLEDGE_BASE_PORT.*?CHUNK_OVERLAP=\d+)") {
            $envContent = $envContent -replace "($matches[1])", "$matches[1]`n`n# Metadata Service配置`n$key=$($configsToAdd[$key])"
        } elseif ($envContent -match "(AUTH_SERVICE_PORT=\d+)") {
            $envContent = $envContent -replace "($matches[1])", "$matches[1]`n`n# Metadata Service配置`n$key=$($configsToAdd[$key])"
        } else {
            # 如果找不到合适位置，添加到文件末尾
            $envContent += "`n# Metadata Service配置`n$key=$($configsToAdd[$key])"
        }
        $updated = $true
    } else {
        Write-Host "✅ $key 已存在" -ForegroundColor Green
    }
}

# 更新数据库配置（如果需要）
if ($envContent -match "DB_NAME\s*=\s*ai_platform") {
    Write-Host "更新 DB_NAME 为 enterprise_ai_platform" -ForegroundColor Yellow
    $envContent = $envContent -replace "DB_NAME\s*=\s*ai_platform", "DB_NAME=enterprise_ai_platform"
    $updated = $true
}

if ($envContent -match "DB_USER\s*=\s*ai_user") {
    Write-Host "更新 DB_USER 为 postgres" -ForegroundColor Yellow
    $envContent = $envContent -replace "DB_USER\s*=\s*ai_user", "DB_USER=postgres"
    $updated = $true
}

# 更新前端URL配置
if ($envContent -notmatch "NEXT_PUBLIC_METADATA_SERVICE_URL") {
    if ($envContent -match "(NEXT_PUBLIC_KNOWLEDGE_BASE_URL.*?)") {
        $envContent = $envContent -replace "($matches[1])", "$matches[1]`nNEXT_PUBLIC_METADATA_SERVICE_URL=http://localhost:8005"
        $updated = $true
    }
}

# 更新服务间通信URL
if ($envContent -notmatch "METADATA_SERVICE_URL") {
    if ($envContent -match "(KNOWLEDGE_BASE_URL.*?)") {
        $envContent = $envContent -replace "($matches[1])", "$matches[1]`nMETADATA_SERVICE_URL=http://metadata-service:8005"
        $updated = $true
    }
}

if ($updated) {
    # 备份原文件
    $backupFile = "$envFile.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item $envFile $backupFile
    Write-Host "已备份原文件到: $backupFile" -ForegroundColor Cyan
    
    # 写入更新后的内容
    Set-Content -Path $envFile -Value $envContent -NoNewline
    Write-Host "✅ .env 文件已更新！" -ForegroundColor Green
} else {
    Write-Host "✅ .env 文件已包含所有必要配置，无需更新" -ForegroundColor Green
}

Write-Host "`n建议运行以下命令验证配置:" -ForegroundColor Cyan
Write-Host "  .\check-env.ps1" -ForegroundColor Yellow

