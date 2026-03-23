# 从.env文件读取SAP配置并添加到配置中心

$CONFIG_CENTER_URL = "http://localhost:8090"
$ENVIRONMENT = "default"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  从.env文件读取SAP配置并添加到配置中心" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查.env文件是否存在
if (-not (Test-Path .env)) {
    Write-Host "错误: .env文件不存在" -ForegroundColor Red
    Write-Host "请确保.env文件在项目根目录" -ForegroundColor Yellow
    exit 1
}

# 读取.env文件
Write-Host "正在读取.env文件..." -ForegroundColor Cyan
$envContent = Get-Content .env

# 提取SAP配置
$sapConfigs = @{}
foreach ($line in $envContent) {
    # 跳过注释和空行
    if ($line -match "^\s*#" -or $line -match "^\s*$") {
        continue
    }
    
    # 匹配SAP相关配置
    if ($line -match "^SAP_") {
        $parts = $line -split "=", 2
        if ($parts.Length -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()
            # 移除引号
            $value = $value -replace '^["\']|["\']$', ''
            $sapConfigs[$key] = $value
        }
    }
}

# 检查必需配置
$requiredKeys = @("SAP_BASE_URL", "SAP_USERNAME", "SAP_PASSWORD")
$missingKeys = @()
foreach ($key in $requiredKeys) {
    if (-not $sapConfigs.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($sapConfigs[$key])) {
        $missingKeys += $key
    }
}

if ($missingKeys.Count -gt 0) {
    Write-Host "错误: .env文件中缺少以下必需配置:" -ForegroundColor Red
    foreach ($key in $missingKeys) {
        Write-Host "  - $key" -ForegroundColor Yellow
    }
    exit 1
}

# 显示找到的配置
Write-Host "找到以下SAP配置:" -ForegroundColor Green
foreach ($key in $sapConfigs.Keys) {
    $displayValue = if ($key -match "PASSWORD") { "***" } else { $sapConfigs[$key] }
    Write-Host "  $key = $displayValue" -ForegroundColor Gray
}
Write-Host ""

# 确认
$confirm = Read-Host "确认将这些配置添加到配置中心? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

# 映射配置键名（从环境变量格式转换为配置中心格式）
$configMapping = @{
    "SAP_BASE_URL" = "sap.base_url"
    "SAP_USERNAME" = "sap.username"
    "SAP_PASSWORD" = "sap.password"
    "SAP_CLIENT" = "sap.client"
    "SAP_LANGUAGE" = "sap.language"
    "SAP_TIMEOUT" = "sap.timeout"
    "SAP_MAX_RETRIES" = "sap.max_retries"
    "SAP_PAGE_SIZE" = "sap.page_size"
    "SAP_MAX_RECORDS" = "sap.max_records"
}

$descriptions = @{
    "sap.base_url" = "SAP系统的基础URL"
    "sap.username" = "SAP用户名"
    "sap.password" = "SAP密码"
    "sap.client" = "SAP客户端编号"
    "sap.language" = "SAP系统语言"
    "sap.timeout" = "SAP请求超时时间（毫秒）"
    "sap.max_retries" = "SAP请求最大重试次数"
    "sap.page_size" = "SAP查询分页大小"
    "sap.max_records" = "SAP查询最大记录数"
}

# 添加配置的函数
function Add-Config {
    param(
        [string]$Key,
        [string]$Value,
        [string]$Description
    )
    
    $body = @{
        key = $Key
        value = $Value
        description = $Description
        environment = $ENVIRONMENT
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$CONFIG_CENTER_URL/api/config" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -ErrorAction Stop
        
        Write-Host "✅ $Key" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ $Key : $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "   响应: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
        return $false
    }
}

# 添加所有配置
Write-Host ""
Write-Host "正在添加配置到配置中心..." -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($envKey in $sapConfigs.Keys) {
    if ($configMapping.ContainsKey($envKey)) {
        $configKey = $configMapping[$envKey]
        $value = $sapConfigs[$envKey]
        $description = $descriptions[$configKey]
        
        if (Add-Config $configKey $value $description) {
            $successCount++
        } else {
            $failCount++
        }
    }
}

# 添加默认值（如果.env中没有）
$defaultConfigs = @{
    "sap.client" = "100"
    "sap.language" = "EN"
    "sap.timeout" = "300000"
    "sap.max_retries" = "3"
    "sap.page_size" = "1000"
    "sap.max_records" = "10000"
}

foreach ($configKey in $defaultConfigs.Keys) {
    # 检查是否已经添加
    $envKey = ($configMapping.GetEnumerator() | Where-Object { $_.Value -eq $configKey }).Key
    if (-not $envKey -or -not $sapConfigs.ContainsKey($envKey)) {
        if (Add-Config $configKey $defaultConfigs[$configKey] $descriptions[$configKey]) {
            $successCount++
        } else {
            $failCount++
        }
    }
}

Write-Host ""
Write-Host "完成: 成功 $successCount 个, 失败 $failCount 个" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })

if ($successCount -gt 0) {
    Write-Host ""
    Write-Host "✅ SAP配置已从.env文件添加到配置中心" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Cyan
    Write-Host "  1. 重启 sap-mcp-server 服务:" -ForegroundColor White
    Write-Host "     docker-compose restart sap-mcp-server" -ForegroundColor Gray
    Write-Host "  2. 验证配置是否生效:" -ForegroundColor White
    Write-Host "     docker logs enterprise-ai-sap-mcp-server --tail 20" -ForegroundColor Gray
}
































