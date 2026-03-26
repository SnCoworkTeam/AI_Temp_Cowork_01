# 项目计划功能测试脚本
# 测试所有CRUD接口和树形结构API

$ErrorActionPreference = "Stop"

# 配置
$API_BASE = "http://43.143.139.197:8080"
$USERNAME = "admin"
$PASSWORD = "admin123456"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "项目计划功能测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. 登录获取Token
Write-Host "1. 登录获取Token..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $USERNAME
        password = $PASSWORD
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "$API_BASE/api/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody

    $token = $loginResponse.access_token
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    Write-Host "   ✅ 登录成功" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 登录失败: $_" -ForegroundColor Red
    exit 1
}

# 2. 获取项目列表（用于测试）
Write-Host "`n2. 获取项目列表..." -ForegroundColor Yellow
try {
    $projectsResponse = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects?limit=1" `
        -Method GET `
        -Headers $headers

    if ($projectsResponse.items.Count -eq 0) {
        Write-Host "   ⚠️  没有可用项目，请先创建项目" -ForegroundColor Yellow
        exit 0
    }

    $projectId = $projectsResponse.items[0].id
    Write-Host "   ✅ 找到项目: $($projectsResponse.items[0].name) (ID: $projectId)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 获取项目列表失败: $_" -ForegroundColor Red
    exit 1
}

# 3. 测试模板管理API
Write-Host "`n3. 测试模板管理API..." -ForegroundColor Yellow
try {
    # 3.1 获取模板列表
    Write-Host "   3.1 获取模板列表..." -ForegroundColor Cyan
    $templatesResponse = Invoke-RestMethod -Uri "$API_BASE/api/v1/project-templates" `
        -Method GET `
        -Headers $headers
    Write-Host "      ✅ 获取模板列表成功，共 $($templatesResponse.total) 个模板" -ForegroundColor Green

    # 3.2 如果有模板，获取模板详情
    if ($templatesResponse.items.Count -gt 0) {
        $templateId = $templatesResponse.items[0].id
        Write-Host "   3.2 获取模板详情 (ID: $templateId)..." -ForegroundColor Cyan
        $templateResponse = Invoke-RestMethod -Uri "$API_BASE/api/v1/project-templates/$templateId" `
            -Method GET `
            -Headers $headers
        Write-Host "      ✅ 获取模板详情成功: $($templateResponse.name)" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ 模板管理API测试失败: $_" -ForegroundColor Red
}

# 4. 测试项目计划CRUD
Write-Host "`n4. 测试项目计划CRUD..." -ForegroundColor Yellow

# 4.1 获取计划列表
Write-Host "   4.1 获取计划列表..." -ForegroundColor Cyan
try {
    $plansResponse = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId/plans" `
        -Method GET `
        -Headers $headers
    Write-Host "      ✅ 获取计划列表成功，共 $($plansResponse.total) 个计划" -ForegroundColor Green
} catch {
    Write-Host "      ❌ 获取计划列表失败: $_" -ForegroundColor Red
}

# 4.2 创建计划
Write-Host "   4.2 创建计划..." -ForegroundColor Cyan
$newPlanId = $null
try {
    $planBody = @{
        name = "测试计划 $(Get-Date -Format 'yyyyMMddHHmmss')"
        description = "这是一个测试计划"
        version = "1.0"
        start_date = "2025-01-01"
        end_date = "2025-12-31"
    } | ConvertTo-Json

    $createResponse = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId/plans" `
        -Method POST `
        -ContentType "application/json" `
        -Headers $headers `
        -Body $planBody

    $newPlanId = $createResponse.id
    Write-Host "      ✅ 创建计划成功 (ID: $newPlanId)" -ForegroundColor Green
} catch {
    Write-Host "      ❌ 创建计划失败: $_" -ForegroundColor Red
}

# 4.3 获取计划详情
if ($newPlanId) {
    Write-Host "   4.3 获取计划详情 (ID: $newPlanId)..." -ForegroundColor Cyan
    try {
        $planResponse = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId/plans/$newPlanId" `
            -Method GET `
            -Headers $headers
        Write-Host "      ✅ 获取计划详情成功: $($planResponse.name)" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ 获取计划详情失败: $_" -ForegroundColor Red
    }

    # 4.4 更新计划
    Write-Host "   4.4 更新计划 (ID: $newPlanId)..." -ForegroundColor Cyan
    try {
        $updateBody = @{
            name = "更新后的测试计划"
            description = "这是更新后的描述"
        } | ConvertTo-Json

        $updateResponse = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId/plans/$newPlanId" `
            -Method PUT `
            -ContentType "application/json" `
            -Headers $headers `
            -Body $updateBody
        Write-Host "      ✅ 更新计划成功" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ 更新计划失败: $_" -ForegroundColor Red
    }

    # 4.5 测试树形结构API
    Write-Host "   4.5 获取计划树形结构 (ID: $newPlanId)..." -ForegroundColor Cyan
    try {
        $treeResponse = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId/plans/$newPlanId/tree" `
            -Method GET `
            -Headers $headers
        Write-Host "      ✅ 获取树形结构成功，共 $($treeResponse.tree.Count) 个阶段节点" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ 获取树形结构失败: $_" -ForegroundColor Red
    }

    # 4.6 测试任务操作（需要先有阶段和任务分类）
    Write-Host "   4.6 测试任务操作..." -ForegroundColor Cyan
    Write-Host "      ⚠️  需要先创建阶段和任务分类，跳过" -ForegroundColor Yellow

    # 4.7 删除计划
    Write-Host "   4.7 删除计划 (ID: $newPlanId)..." -ForegroundColor Cyan
    try {
        Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId/plans/$newPlanId" `
            -Method DELETE `
            -Headers $headers | Out-Null
        Write-Host "      ✅ 删除计划成功" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ 删除计划失败: $_" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

