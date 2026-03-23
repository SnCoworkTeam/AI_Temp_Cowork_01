# 分类体系迁移测试脚本 (PowerShell版本)
# 使用方法: .\scripts\test-classification-migration.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "分类体系迁移测试脚本" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 配置变量
$API_URL = "http://localhost:8000"
$DB_NAME = "luminaos"
$DB_USER = "postgres"

# 函数：打印信息
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 函数：检查服务
function Test-Service {
    Write-Info "检查 Metadata Service 状态..."
    
    try {
        $response = Invoke-WebRequest -Uri "$API_URL/api/health" -Method GET -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Info "Metadata Service 运行正常"
            return $true
        }
    }
    catch {
        Write-Error "Metadata Service 未运行或无法访问: $($_.Exception.Message)"
        return $false
    }
}

# 函数：预览迁移
function Test-PreviewMigration {
    Write-Info "预览迁移结果（试运行）..."
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migration/preview?limit=10" -Method GET
        if ($response.status -eq "success") {
            Write-Info "预览成功"
            $response | ConvertTo-Json -Depth 10
            return $true
        }
        else {
            Write-Error "预览失败"
            return $false
        }
    }
    catch {
        Write-Error "预览失败: $($_.Exception.Message)"
        return $false
    }
}

# 函数：执行试运行迁移
function Test-DryRunMigration {
    Write-Info "执行试运行迁移..."
    
    $body = @{
        dry_run = $true
        batch_size = 10
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migrate" -Method POST -Body $body -ContentType "application/json"
        if ($response.status -eq "success") {
            Write-Info "试运行成功"
            Write-Info "统计信息:"
            $response.stats | ConvertTo-Json -Depth 5
            return $true
        }
        else {
            Write-Error "试运行失败"
            return $false
        }
    }
    catch {
        Write-Error "试运行失败: $($_.Exception.Message)"
        return $false
    }
}

# 函数：执行实际迁移
function Start-ActualMigration {
    Write-Warn "即将执行实际数据迁移，这将更新数据库！"
    $confirm = Read-Host "确认继续？(yes/no)"
    
    if ($confirm -ne "yes") {
        Write-Info "已取消迁移"
        return $false
    }
    
    Write-Info "执行实际数据迁移..."
    
    $body = @{
        dry_run = $false
        batch_size = 100
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/classification/migrate" -Method POST -Body $body -ContentType "application/json"
        if ($response.status -eq "success") {
            Write-Info "数据迁移成功"
            Write-Info "统计信息:"
            $response.stats | ConvertTo-Json -Depth 5
            return $true
        }
        else {
            Write-Error "数据迁移失败"
            return $false
        }
    }
    catch {
        Write-Error "数据迁移失败: $($_.Exception.Message)"
        return $false
    }
}

# 函数：测试API
function Test-ClassificationAPI {
    Write-Info "测试分类维度查询API..."
    
    $tests = @(
        @{ name = "业务领域查询"; url = "$API_URL/api/data-assets?business_domain=finance&limit=1" }
        @{ name = "技术来源查询"; url = "$API_URL/api/data-assets?technical_source=sap&limit=1" }
        @{ name = "生命周期查询"; url = "$API_URL/api/data-assets?lifecycle_stage=production&limit=1" }
        @{ name = "标签查询"; url = "$API_URL/api/data-assets?standardized_tag=biz:critical&limit=1" }
    )
    
    $allPassed = $true
    foreach ($test in $tests) {
        try {
            $response = Invoke-WebRequest -Uri $test.url -Method GET -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Info "$($test.name) - 通过"
            }
            else {
                Write-Warn "$($test.name) - 失败 (状态码: $($response.StatusCode))"
                $allPassed = $false
            }
        }
        catch {
            Write-Warn "$($test.name) - 失败: $($_.Exception.Message)"
            $allPassed = $false
        }
    }
    
    return $allPassed
}

# 主函数
function Main {
    Write-Info "开始测试流程..."
    
    # 检查服务
    if (-not (Test-Service)) {
        Write-Error "请先启动 Metadata Service"
        exit 1
    }
    
    # 预览迁移
    if (-not (Test-PreviewMigration)) {
        Write-Warn "预览失败，但继续执行"
    }
    
    # 试运行迁移
    if (-not (Test-DryRunMigration)) {
        Write-Warn "试运行失败，请检查日志"
        $continue = Read-Host "是否继续执行实际迁移？(yes/no)"
        if ($continue -ne "yes") {
            Write-Info "已取消实际迁移"
            exit 0
        }
    }
    
    # 执行实际迁移
    if (-not (Start-ActualMigration)) {
        Write-Error "实际迁移失败"
        exit 1
    }
    
    # 测试API
    Test-ClassificationAPI
    
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Info "测试完成！"
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Info "下一步："
    Write-Info "1. 访问前端页面验证: http://localhost:3000/admin/metadata"
    Write-Info "2. 检查分类维度是否正确显示"
    Write-Info "3. 测试维度查询功能"
}

# 执行主函数
Main








