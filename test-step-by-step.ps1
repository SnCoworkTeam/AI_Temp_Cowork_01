# 分步骤测试项目管理功能
$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目管理功能分步测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 测试1: 项目列表查询（不需要认证）
Write-Host "测试1: 项目列表查询" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects"
    Write-Host "✅ 成功" -ForegroundColor Green
    Write-Host "  项目总数: $($response.total)" -ForegroundColor White
    Write-Host "  返回项目数: $($response.items.Count)" -ForegroundColor White
    
    if ($response.items.Count -gt 0) {
        $firstProject = $response.items[0]
        Write-Host "  示例项目: $($firstProject.name) ($($firstProject.project_code))" -ForegroundColor White
        $sampleProjectId = $firstProject.id
    }
} catch {
    Write-Host "❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
    $sampleProjectId = $null
}

Write-Host ""

# 测试2: 项目详情查询
if ($sampleProjectId) {
    Write-Host "测试2: 项目详情查询" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    try {
        $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/projects/$sampleProjectId"
        Write-Host "✅ 成功" -ForegroundColor Green
        Write-Host "  项目名称: $($response.name)" -ForegroundColor White
        Write-Host "  项目编码: $($response.project_code)" -ForegroundColor White
        Write-Host "  项目状态: $($response.status)" -ForegroundColor White
        Write-Host "  进度: $($response.progress_percent)%" -ForegroundColor White
    } catch {
        Write-Host "❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

# 测试3: 周报列表查询
Write-Host "测试3: 周报列表查询" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/weekly-reports"
    Write-Host "✅ 成功" -ForegroundColor Green
    Write-Host "  周报总数: $($response.total)" -ForegroundColor White
    Write-Host "  返回周报数: $($response.items.Count)" -ForegroundColor White
} catch {
    Write-Host "❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 测试4: 月报列表查询
Write-Host "测试4: 月报列表查询" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Method GET -Uri "$BASE_URL/monthly-reports"
    Write-Host "✅ 成功" -ForegroundColor Green
    Write-Host "  月报总数: $($response.total)" -ForegroundColor White
    Write-Host "  返回月报数: $($response.items.Count)" -ForegroundColor White
} catch {
    Write-Host "❌ 失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 测试5: 需要认证的功能
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "需要认证的功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$TOKEN = Read-Host "请输入认证Token（或按Enter跳过需要认证的测试）"

if ($TOKEN) {
    $HEADERS = @{
        "Authorization" = "Bearer $TOKEN"
        "Content-Type" = "application/json"
    }
    
    # 测试5: 创建项目
    Write-Host "测试5: 创建项目" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    $projectCode = "TEST-$(Get-Date -Format 'yyyyMMddHHmmss')"
    $createData = @{
        project_code = $projectCode
        name = "测试项目 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        description = "自动化测试创建的项目"
        status = "planning"
        priority = "medium"
        start_date = (Get-Date).ToString("yyyy-MM-dd")
        end_date = (Get-Date).AddMonths(3).ToString("yyyy-MM-dd")
        budget = 100000.00
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Method POST -Uri "$BASE_URL/projects" -Headers $HEADERS -Body $createData
        Write-Host "✅ 创建成功" -ForegroundColor Green
        Write-Host "  项目ID: $($response.id)" -ForegroundColor White
        Write-Host "  项目编码: $($response.project_code)" -ForegroundColor White
        $testProjectId = $response.id
        
        # 测试6: 更新项目
        Write-Host ""
        Write-Host "测试6: 更新项目" -ForegroundColor Yellow
        Write-Host "----------------------------------------" -ForegroundColor Gray
        $updateData = @{
            name = "测试项目 - 已更新 $(Get-Date -Format 'HH:mm:ss')"
            status = "active"
            progress_percent = 25.5
        } | ConvertTo-Json
        
        try {
            $updateResponse = Invoke-RestMethod -Method PUT -Uri "$BASE_URL/projects/$testProjectId" -Headers $HEADERS -Body $updateData
            Write-Host "✅ 更新成功" -ForegroundColor Green
            Write-Host "  更新后名称: $($updateResponse.name)" -ForegroundColor White
            Write-Host "  更新后状态: $($updateResponse.status)" -ForegroundColor White
        } catch {
            Write-Host "❌ 更新失败: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        # 测试7: 创建周报
        Write-Host ""
        Write-Host "测试7: 创建周报" -ForegroundColor Yellow
        Write-Host "----------------------------------------" -ForegroundColor Gray
        $weeklyData = @{
            project_id = $testProjectId
            report_date = (Get-Date).ToString("yyyy-MM-dd")
            content_plan = "本周计划"
            content_achievement = "本周成果"
            next_week_plan = "下周计划"
        } | ConvertTo-Json
        
        try {
            $weeklyResponse = Invoke-RestMethod -Method POST -Uri "$BASE_URL/weekly-reports" -Headers $HEADERS -Body $weeklyData
            Write-Host "✅ 创建成功" -ForegroundColor Green
            Write-Host "  周报ID: $($weeklyResponse.id)" -ForegroundColor White
        } catch {
            Write-Host "❌ 创建失败: $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response) {
                $statusCode = $_.Exception.Response.StatusCode.value__
                Write-Host "  HTTP状态码: $statusCode" -ForegroundColor Red
            }
        }
        
        # 测试8: 创建月报
        Write-Host ""
        Write-Host "测试8: 创建月报" -ForegroundColor Yellow
        Write-Host "----------------------------------------" -ForegroundColor Gray
        $monthlyData = @{
            project_id = $testProjectId
            report_month = (Get-Date).ToString("yyyy-MM")
            summary = "月度总结"
            achievements = "月度成果"
            challenges = "挑战问题"
        } | ConvertTo-Json
        
        try {
            $monthlyResponse = Invoke-RestMethod -Method POST -Uri "$BASE_URL/monthly-reports" -Headers $HEADERS -Body $monthlyData
            Write-Host "✅ 创建成功" -ForegroundColor Green
            Write-Host "  月报ID: $($monthlyResponse.id)" -ForegroundColor White
        } catch {
            Write-Host "❌ 创建失败: $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response) {
                $statusCode = $_.Exception.Response.StatusCode.value__
                Write-Host "  HTTP状态码: $statusCode" -ForegroundColor Red
            }
        }
        
        # 测试9: 删除项目（可选）
        Write-Host ""
        Write-Host "测试9: 删除项目" -ForegroundColor Yellow
        Write-Host "----------------------------------------" -ForegroundColor Gray
        Write-Host "⚠️  警告: 删除操作不可逆" -ForegroundColor Red
        $confirm = Read-Host "是否删除测试项目? (yes/no)"
        if ($confirm -eq "yes") {
            try {
                $deleteResponse = Invoke-RestMethod -Method DELETE -Uri "$BASE_URL/projects/$testProjectId" -Headers $HEADERS
                Write-Host "✅ 删除成功" -ForegroundColor Green
            } catch {
                Write-Host "❌ 删除失败: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "⏭️  跳过删除" -ForegroundColor Yellow
            Write-Host "  测试项目ID: $testProjectId (请手动删除)" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ 创建失败: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.value__
            Write-Host "  HTTP状态码: $statusCode" -ForegroundColor Red
            try {
                $errorStream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorBody = $reader.ReadToEnd()
                Write-Host "  错误详情: $errorBody" -ForegroundColor Red
            } catch {
                # 忽略读取错误
            }
        }
    }
} else {
    Write-Host "⏭️  跳过需要认证的测试" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

