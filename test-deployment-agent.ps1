# 部署智能体服务测试脚本
# 测试完整部署流程（代码 + 数据 + Neo4j + 数据库迁移）

param(
    [switch]$SkipDataSync = $false,
    [switch]$SkipMigration = $false,
    [switch]$SkipNeo4j = $false,
    [switch]$AutoConfirm = $false  # 自动确认，跳过交互
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署智能体服务 - 完整部署测试" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查服务状态
Write-Host "[1/5] 检查部署智能体服务状态..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri http://localhost:8007/health -Method GET -TimeoutSec 5
    Write-Host "  ✅ 服务运行正常" -ForegroundColor Green
    Write-Host "  监控状态: $($status.agent.is_monitoring)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ 服务未运行，请先启动: docker-compose up -d deployment-agent" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. 触发完整部署
Write-Host "[2/5] 通过API触发完整部署..." -ForegroundColor Yellow
$body = @{
    skip_data_sync = $SkipDataSync
    skip_migration = $SkipMigration
    include_neo4j = -not $SkipNeo4j
} | ConvertTo-Json

try {
    $result = Invoke-RestMethod -Uri http://localhost:8007/api/v1/deploy-full `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 10
    
    Write-Host "  ✅ 部署任务已创建" -ForegroundColor Green
    Write-Host "  状态: $($result.status)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ 创建部署任务失败: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. 查找任务文件
Write-Host "[3/5] 查找部署任务文件..." -ForegroundColor Yellow
$taskFiles = Get-ChildItem -Path "deployment-agent\workdir" -Filter "*task*.json" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

if ($taskFiles.Count -eq 0) {
    Write-Host "  ⚠️  未找到任务文件" -ForegroundColor Yellow
} else {
    $latestTask = $taskFiles[0]
    Write-Host "  ✅ 找到任务文件: $($latestTask.Name)" -ForegroundColor Green
    
    $task = Get-Content $latestTask.FullName | ConvertFrom-Json
    Write-Host "  任务类型: $($task.type)" -ForegroundColor Gray
    Write-Host "  脚本: $($task.script)" -ForegroundColor Gray
    Write-Host "  服务: $($task.services -join ', ')" -ForegroundColor Gray
}
Write-Host ""

# 4. 执行部署任务
Write-Host "[4/5] 执行部署任务..." -ForegroundColor Yellow
Write-Host "  提示: 将执行完整同步脚本（代码 + 镜像 + 数据 + Neo4j + 迁移）" -ForegroundColor Gray
Write-Host ""

if (-not $AutoConfirm) {
    $confirm = Read-Host "是否继续执行部署？(Y/N)"
    if ($confirm -ne "Y" -and $confirm -ne "y") {
        Write-Host "  已取消部署" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "  自动确认，开始执行部署..." -ForegroundColor Cyan
}

Write-Host "  执行部署脚本..." -ForegroundColor Cyan
Write-Host ""

# 执行完整同步脚本
$deployParams = @{
    RemotePath = "/opt/enterprise-ai-platform"
}

if ($SkipDataSync) {
    $deployParams["SkipDataSync"] = $true
}

if ($SkipMigration) {
    $deployParams["SkipMigration"] = $true
}

try {
    & .\scripts\deployment\complete-sync.ps1 @deployParams
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  ✅ 部署执行完成" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  ⚠️  部署执行完成，但有警告（退出码: $LASTEXITCODE）" -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "  ❌ 部署执行失败: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 5. 验证部署结果
Write-Host "[5/5] 验证部署结果..." -ForegroundColor Yellow

# 检查部署历史
try {
    $history = Invoke-RestMethod -Uri http://localhost:8007/api/v1/history -Method GET -TimeoutSec 5
    Write-Host "  ✅ 部署历史记录: $($history.history.Count) 条" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  无法获取部署历史" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示:" -ForegroundColor Yellow
Write-Host "  - 查看服务日志: docker-compose logs -f deployment-agent" -ForegroundColor Gray
Write-Host "  - 查看部署历史: Invoke-RestMethod -Uri http://localhost:8007/api/v1/history" -ForegroundColor Gray
Write-Host "  - 查看任务文件: Get-ChildItem deployment-agent\workdir\*task*.json" -ForegroundColor Gray
Write-Host ""




