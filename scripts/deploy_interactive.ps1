# 交互式部署脚本
# 提示用户输入服务器信息并执行部署

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Neo4j数据库架构优化 - 服务器部署" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# 获取服务器信息
$ServerHost = Read-Host "请输入服务器IP地址或域名"
if ([string]::IsNullOrWhiteSpace($ServerHost)) {
    Write-Host "错误: 服务器地址不能为空" -ForegroundColor Red
    exit 1
}

$ServerUser = Read-Host "请输入SSH用户名 (默认: root)"
if ([string]::IsNullOrWhiteSpace($ServerUser)) {
    $ServerUser = "root"
}

$ServerPath = Read-Host "请输入服务器上的项目路径 (默认: /opt/enterprise-ai-platform)"
if ([string]::IsNullOrWhiteSpace($ServerPath)) {
    $ServerPath = "/opt/enterprise-ai-platform"
}

Write-Host ""
Write-Host "部署配置:" -ForegroundColor Yellow
Write-Host "  服务器: ${ServerUser}@${ServerHost}"
Write-Host "  路径: ${ServerPath}"
Write-Host ""

# 确认
$confirm = Read-Host "确认开始部署? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "部署已取消" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "开始部署..." -ForegroundColor Green
Write-Host ""

# 执行部署脚本
& ".\scripts\deploy_all_to_server.ps1" -ServerHost $ServerHost -ServerUser $ServerUser -ServerPath $ServerPath



