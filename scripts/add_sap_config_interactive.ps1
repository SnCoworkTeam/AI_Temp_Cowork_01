# 交互式添加SAP配置到配置中心

$CONFIG_CENTER_URL = "http://localhost:8090"
$ENVIRONMENT = "default"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  添加SAP配置到配置中心" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 收集配置信息
Write-Host "请输入SAP配置信息（按Enter使用默认值）:" -ForegroundColor Yellow
Write-Host ""

$sapBaseUrl = Read-Host "SAP系统基础URL (必需)"
if ([string]::IsNullOrWhiteSpace($sapBaseUrl)) {
    Write-Host "错误: SAP系统基础URL是必需的" -ForegroundColor Red
    exit 1
}

$sapUsername = Read-Host "SAP用户名 (必需)"
if ([string]::IsNullOrWhiteSpace($sapUsername)) {
    Write-Host "错误: SAP用户名是必需的" -ForegroundColor Red
    exit 1
}

$sapPassword = Read-Host "SAP密码 (必需)" -AsSecureString
$sapPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sapPassword)
)

$sapClient = Read-Host "SAP客户端编号 [默认: 100]"
if ([string]::IsNullOrWhiteSpace($sapClient)) {
    $sapClient = "100"
}

$sapLanguage = Read-Host "SAP系统语言 [默认: EN]"
if ([string]::IsNullOrWhiteSpace($sapLanguage)) {
    $sapLanguage = "EN"
}

$sapTimeout = Read-Host "SAP请求超时时间(毫秒) [默认: 300000]"
if ([string]::IsNullOrWhiteSpace($sapTimeout)) {
    $sapTimeout = "300000"
}

$sapMaxRetries = Read-Host "SAP最大重试次数 [默认: 3]"
if ([string]::IsNullOrWhiteSpace($sapMaxRetries)) {
    $sapMaxRetries = "3"
}

$sapPageSize = Read-Host "SAP查询分页大小 [默认: 1000]"
if ([string]::IsNullOrWhiteSpace($sapPageSize)) {
    $sapPageSize = "1000"
}

$sapMaxRecords = Read-Host "SAP查询最大记录数 [默认: 10000]"
if ([string]::IsNullOrWhiteSpace($sapMaxRecords)) {
    $sapMaxRecords = "10000"
}

Write-Host ""
Write-Host "配置摘要:" -ForegroundColor Cyan
Write-Host "  SAP基础URL: $sapBaseUrl"
Write-Host "  SAP用户名: $sapUsername"
Write-Host "  SAP客户端: $sapClient"
Write-Host "  SAP语言: $sapLanguage"
Write-Host ""

$confirm = Read-Host "确认添加这些配置到配置中心? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
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
        return $false
    }
}

# 添加所有配置
Write-Host ""
Write-Host "正在添加配置..." -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

if (Add-Config "sap.base_url" $sapBaseUrl "SAP系统的基础URL") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.username" $sapUsername "SAP用户名") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.password" $sapPasswordPlain "SAP密码") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.client" $sapClient "SAP客户端编号") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.language" $sapLanguage "SAP系统语言") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.timeout" $sapTimeout "SAP请求超时时间（毫秒）") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.max_retries" $sapMaxRetries "SAP请求最大重试次数") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.page_size" $sapPageSize "SAP查询分页大小") { $successCount++ } else { $failCount++ }
if (Add-Config "sap.max_records" $sapMaxRecords "SAP查询最大记录数") { $successCount++ } else { $failCount++ }

Write-Host ""
Write-Host "完成: 成功 $successCount 个, 失败 $failCount 个" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })

if ($successCount -gt 0) {
    Write-Host ""
    Write-Host "✅ SAP配置已添加到配置中心" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Cyan
    Write-Host "  1. 重启 sap-mcp-server 服务:" -ForegroundColor White
    Write-Host "     docker-compose restart sap-mcp-server" -ForegroundColor Gray
    Write-Host "  2. 验证配置是否生效:" -ForegroundColor White
    Write-Host "     docker logs enterprise-ai-sap-mcp-server --tail 20" -ForegroundColor Gray
}
































