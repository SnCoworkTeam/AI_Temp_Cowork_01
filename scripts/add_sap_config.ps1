# PowerShell脚本：添加SAP配置到配置中心

$CONFIG_CENTER_URL = if ($env:CONFIG_CENTER_URL) { $env:CONFIG_CENTER_URL } else { "http://localhost:8090" }
$ENVIRONMENT = if ($env:ENVIRONMENT) { $env:ENVIRONMENT } else { "default" }

Write-Host "正在添加SAP配置到配置中心..." -ForegroundColor Cyan
Write-Host "配置中心URL: $CONFIG_CENTER_URL"
Write-Host "环境: $ENVIRONMENT"
Write-Host ""

# 检查必需参数
if (-not $env:SAP_BASE_URL -or -not $env:SAP_USERNAME -or -not $env:SAP_PASSWORD) {
    Write-Host "错误: 请设置以下环境变量:" -ForegroundColor Red
    Write-Host "  SAP_BASE_URL - SAP系统的基础URL"
    Write-Host "  SAP_USERNAME - SAP用户名"
    Write-Host "  SAP_PASSWORD - SAP密码"
    Write-Host ""
    Write-Host "可选参数:"
    Write-Host "  SAP_CLIENT - SAP客户端编号 (默认: 100)"
    Write-Host "  SAP_LANGUAGE - SAP系统语言 (默认: EN)"
    Write-Host ""
    Write-Host "示例 (PowerShell):"
    Write-Host "  `$env:SAP_BASE_URL='https://your-sap-system.com'"
    Write-Host "  `$env:SAP_USERNAME='your_username'"
    Write-Host "  `$env:SAP_PASSWORD='your_password'"
    Write-Host "  .\scripts\add_sap_config.ps1"
    exit 1
}

# 设置默认值
$SAP_CLIENT = if ($env:SAP_CLIENT) { $env:SAP_CLIENT } else { "100" }
$SAP_LANGUAGE = if ($env:SAP_LANGUAGE) { $env:SAP_LANGUAGE } else { "EN" }
$SAP_TIMEOUT = if ($env:SAP_TIMEOUT) { $env:SAP_TIMEOUT } else { "300000" }
$SAP_MAX_RETRIES = if ($env:SAP_MAX_RETRIES) { $env:SAP_MAX_RETRIES } else { "3" }
$SAP_PAGE_SIZE = if ($env:SAP_PAGE_SIZE) { $env:SAP_PAGE_SIZE } else { "1000" }
$SAP_MAX_RECORDS = if ($env:SAP_MAX_RECORDS) { $env:SAP_MAX_RECORDS } else { "10000" }

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
        
        Write-Host "✅ 配置已添加: $Key (版本: $($response.version))" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ 添加配置失败 $Key : $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "   响应: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
        return $false
    }
}

# 添加所有SAP配置
$successCount = 0
$failCount = 0

Write-Host "开始添加配置..." -ForegroundColor Cyan
Write-Host ""

if (Add-Config "sap.base_url" $env:SAP_BASE_URL "SAP系统的基础URL") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.username" $env:SAP_USERNAME "SAP用户名") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.password" $env:SAP_PASSWORD "SAP密码") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.client" $SAP_CLIENT "SAP客户端编号") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.language" $SAP_LANGUAGE "SAP系统语言") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.timeout" $SAP_TIMEOUT "SAP请求超时时间（毫秒）") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.max_retries" $SAP_MAX_RETRIES "SAP请求最大重试次数") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.page_size" $SAP_PAGE_SIZE "SAP查询分页大小") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.max_records" $SAP_MAX_RECORDS "SAP查询最大记录数") { $successCount++ } else { $failCount++ }

Write-Host ""
Write-Host "完成: 成功 $successCount 个, 失败 $failCount 个" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })

if ($successCount -gt 0) {
    Write-Host ""
    Write-Host "✅ SAP配置已添加到配置中心" -ForegroundColor Green
    Write-Host "   请重启 sap-mcp-server 服务以使配置生效:" -ForegroundColor Cyan
    Write-Host "   docker-compose restart sap-mcp-server" -ForegroundColor White
}
































