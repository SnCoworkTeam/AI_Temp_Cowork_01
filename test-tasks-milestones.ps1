# 测试任务管理和里程碑管理的增删改查功能
$API_URL = "http://43.143.139.197:8080"
$BASE_URL = "$API_URL/api/v1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "任务管理和里程碑管理功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 登录获取Token
Write-Host "正在登录..." -ForegroundColor Yellow
$loginBody = @{
    username = "admin"
    password = "admin123456"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Method POST -Uri "$API_URL/api/auth/login" -Body $loginBody -ContentType "application/json"
    
    if ($loginResponse.access_token) {
        $TOKEN = $loginResponse.access_token
        Write-Host "✅ 登录成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 登录失败: 未返回token" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 登录失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$HEADERS = @{
    "Authorization" = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

Write-Host ""

# 测试结果统计
$testResults = @{
    passed = 0
    failed = 0
    errors = @()
}

function Test-API {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )
    
    Write-Host "测试: $Name" -ForegroundColor Cyan
    Write-Host "  $Method $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Method = $Method
            Uri = $Url
            Headers = $Headers
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        
        Write-Host "  ✅ 成功" -ForegroundColor Green
        $script:testResults.passed++
        return $response
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        
        Write-Host "  ❌ 失败 (HTTP $statusCode)" -ForegroundColor Red
        Write-Host "     错误: $errorMessage" -ForegroundColor Red
        
        # 尝试获取详细错误
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            $reader.Close()
            $errorStream.Close()
            
            try {
                $errorJson = $errorBody | ConvertFrom-Json
                if ($errorJson.detail) {
                    Write-Host "     详情: $($errorJson.detail)" -ForegroundColor Red
                    $script:testResults.errors += "${Name}: $($errorJson.detail)"
                } else {
                    $script:testResults.errors += "${Name}: $errorBody"
                }
            } catch {
                $script:testResults.errors += "${Name}: $errorBody"
            }
        } catch {
            $script:testResults.errors += "${Name}: $errorMessage"
        }
        
        $script:testResults.failed++
        return $null
    }
}

# 先获取一个项目ID用于测试
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤1: 获取测试项目" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectList = Test-API -Name "获取项目列表" -Method "GET" -Url "$BASE_URL/projects?limit=1" -Headers $HEADERS
$TEST_PROJECT_ID = $null
if ($projectList -and $projectList.items.Count -gt 0) {
    $TEST_PROJECT_ID = $projectList.items[0].id
    Write-Host "  使用项目: $($projectList.items[0].name) ($TEST_PROJECT_ID)" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  没有可用项目，将跳过需要项目ID的测试" -ForegroundColor Yellow
}

Write-Host ""

# 测试任务管理
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤2: 测试任务管理" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 2.1 获取任务列表
$taskList = Test-API -Name "获取任务列表" -Method "GET" -Url "$BASE_URL/tasks" -Headers $HEADERS
if ($taskList) {
    Write-Host "  任务总数: $($taskList.total)" -ForegroundColor Gray
}

# 2.2 按项目ID获取任务列表
if ($TEST_PROJECT_ID) {
    Write-Host ""
    $projectTasks = Test-API -Name "获取项目任务列表" -Method "GET" -Url "$BASE_URL/tasks?project_id=$TEST_PROJECT_ID" -Headers $HEADERS
    if ($projectTasks) {
        Write-Host "  该项目任务数: $($projectTasks.total)" -ForegroundColor Gray
    }
}

# 2.3 创建任务
if ($TEST_PROJECT_ID) {
    Write-Host ""
    $TEST_TASK_ID = $null
    $createTaskBody = @{
        project_id = $TEST_PROJECT_ID
        name = "测试任务 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        description = "这是一个测试任务"
        status = "pending"
        priority = "medium"
        start_date = (Get-Date).ToString("yyyy-MM-dd")
        due_date = (Get-Date).AddDays(7).ToString("yyyy-MM-dd")
        estimated_hours = 8.0
    }
    
    $createTaskResponse = Test-API -Name "创建任务" -Method "POST" -Url "$BASE_URL/tasks" -Headers $HEADERS -Body $createTaskBody
    if ($createTaskResponse) {
        $TEST_TASK_ID = $createTaskResponse.id
        Write-Host "  创建的任务ID: $TEST_TASK_ID" -ForegroundColor Gray
    }
    
    # 2.4 获取任务详情
    if ($TEST_TASK_ID) {
        Write-Host ""
        $taskDetail = Test-API -Name "获取任务详情" -Method "GET" -Url "$BASE_URL/tasks/$TEST_TASK_ID" -Headers $HEADERS
        if ($taskDetail) {
            Write-Host "  任务名称: $($taskDetail.name)" -ForegroundColor Gray
            Write-Host "  任务状态: $($taskDetail.status)" -ForegroundColor Gray
        }
        
        # 2.5 更新任务
        Write-Host ""
        $updateTaskBody = @{
            name = "测试任务 - 已更新 $(Get-Date -Format 'HH:mm:ss')"
            status = "in_progress"
            progress_percent = 50.0
        }
        
        $updateTaskResponse = Test-API -Name "更新任务" -Method "PUT" -Url "$BASE_URL/tasks/$TEST_TASK_ID" -Headers $HEADERS -Body $updateTaskBody
        if ($updateTaskResponse) {
            Write-Host "  更新后名称: $($updateTaskResponse.name)" -ForegroundColor Gray
            Write-Host "  更新后状态: $($updateTaskResponse.status)" -ForegroundColor Gray
            Write-Host "  更新后进度: $($updateTaskResponse.progress_percent)%" -ForegroundColor Gray
        }
        
        # 2.6 删除任务
        Write-Host ""
        Write-Host "⚠️  警告: 删除操作不可逆" -ForegroundColor Red
        $confirm = Read-Host "是否删除测试任务? (yes/no)"
        if ($confirm -eq "yes") {
            $deleteTaskResponse = Test-API -Name "删除任务" -Method "DELETE" -Url "$BASE_URL/tasks/$TEST_TASK_ID" -Headers $HEADERS
        } else {
            Write-Host "  ⏭️  跳过删除" -ForegroundColor Yellow
            Write-Host "  测试任务ID: $TEST_TASK_ID (请手动删除)" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

# 测试里程碑管理
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤3: 测试里程碑管理" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 3.1 获取里程碑列表
$milestoneList = Test-API -Name "获取里程碑列表" -Method "GET" -Url "$BASE_URL/milestones" -Headers $HEADERS
if ($milestoneList) {
    Write-Host "  里程碑总数: $($milestoneList.total)" -ForegroundColor Gray
}

# 3.2 按项目ID获取里程碑列表
if ($TEST_PROJECT_ID) {
    Write-Host ""
    $projectMilestones = Test-API -Name "获取项目里程碑列表" -Method "GET" -Url "$BASE_URL/milestones?project_id=$TEST_PROJECT_ID" -Headers $HEADERS
    if ($projectMilestones) {
        Write-Host "  该项目里程碑数: $($projectMilestones.total)" -ForegroundColor Gray
    }
}

# 3.3 创建里程碑
if ($TEST_PROJECT_ID) {
    Write-Host ""
    $TEST_MILESTONE_ID = $null
    $createMilestoneBody = @{
        project_id = $TEST_PROJECT_ID
        name = "测试里程碑 - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        description = "这是一个测试里程碑"
        status = "planned"
        target_date = (Get-Date).AddMonths(1).ToString("yyyy-MM-dd")
    }
    
    $createMilestoneResponse = Test-API -Name "创建里程碑" -Method "POST" -Url "$BASE_URL/milestones" -Headers $HEADERS -Body $createMilestoneBody
    if ($createMilestoneResponse) {
        $TEST_MILESTONE_ID = $createMilestoneResponse.id
        Write-Host "  创建的里程碑ID: $TEST_MILESTONE_ID" -ForegroundColor Gray
    }
    
    # 3.4 获取里程碑详情
    if ($TEST_MILESTONE_ID) {
        Write-Host ""
        $milestoneDetail = Test-API -Name "获取里程碑详情" -Method "GET" -Url "$BASE_URL/milestones/$TEST_MILESTONE_ID" -Headers $HEADERS
        if ($milestoneDetail) {
            Write-Host "  里程碑名称: $($milestoneDetail.name)" -ForegroundColor Gray
            Write-Host "  里程碑状态: $($milestoneDetail.status)" -ForegroundColor Gray
        }
        
        # 3.5 更新里程碑
        Write-Host ""
        $updateMilestoneBody = @{
            name = "测试里程碑 - 已更新 $(Get-Date -Format 'HH:mm:ss')"
            status = "in_progress"
        }
        
        $updateMilestoneResponse = Test-API -Name "更新里程碑" -Method "PUT" -Url "$BASE_URL/milestones/$TEST_MILESTONE_ID" -Headers $HEADERS -Body $updateMilestoneBody
        if ($updateMilestoneResponse) {
            Write-Host "  更新后名称: $($updateMilestoneResponse.name)" -ForegroundColor Gray
            Write-Host "  更新后状态: $($updateMilestoneResponse.status)" -ForegroundColor Gray
        }
        
        # 3.6 删除里程碑
        Write-Host ""
        Write-Host "⚠️  警告: 删除操作不可逆" -ForegroundColor Red
        $confirm = Read-Host "是否删除测试里程碑? (yes/no)"
        if ($confirm -eq "yes") {
            $deleteMilestoneResponse = Test-API -Name "删除里程碑" -Method "DELETE" -Url "$BASE_URL/milestones/$TEST_MILESTONE_ID" -Headers $HEADERS
        } else {
            Write-Host "  ⏭️  跳过删除" -ForegroundColor Yellow
            Write-Host "  测试里程碑ID: $TEST_MILESTONE_ID (请手动删除)" -ForegroundColor Yellow
        }
    }
}

# 测试结果汇总
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试结果汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 通过: $($testResults.passed)" -ForegroundColor Green
Write-Host "❌ 失败: $($testResults.failed)" -ForegroundColor Red
Write-Host ""

if ($testResults.errors.Count -gt 0) {
    Write-Host "错误详情:" -ForegroundColor Yellow
    foreach ($err in $testResults.errors) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    Write-Host ""
}

if ($testResults.failed -eq 0) {
    Write-Host "🎉 所有测试通过！" -ForegroundColor Green
} else {
    Write-Host "⚠️  有测试失败，请检查上述错误信息" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "注意: 如果创建/更新/删除功能返回404或405，说明这些API尚未实现" -ForegroundColor Yellow
}

Write-Host ""

