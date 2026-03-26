# 在Docker容器内构建语义索引的PowerShell脚本

$CONTAINER_NAME = "enterprise-ai-sap-metadata-agent"
$SCRIPT_PATH = "/app/build_semantic_in_docker.py"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "在Docker容器内构建语义索引" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查容器是否运行
$containerRunning = docker ps --format "{{.Names}}" | Select-String -Pattern "^${CONTAINER_NAME}$"

if (-not $containerRunning) {
    Write-Host "❌ 容器 ${CONTAINER_NAME} 未运行" -ForegroundColor Red
    Write-Host "请先启动容器: docker-compose up -d sap-metadata-agent" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 容器 ${CONTAINER_NAME} 正在运行" -ForegroundColor Green
Write-Host ""

# 构建参数
$batchSize = $args[0]
$resume = $args -contains "--resume"
$noResume = $args -contains "--no-resume"

# 构建docker exec命令
$dockerArgs = @(
    "exec",
    "-it",
    $CONTAINER_NAME,
    "python",
    $SCRIPT_PATH
)

if ($batchSize) {
    $dockerArgs += "--batch-size"
    $dockerArgs += $batchSize
}

if ($resume) {
    $dockerArgs += "--resume"
}

if ($noResume) {
    $dockerArgs += "--no-resume"
}

# 执行构建
Write-Host "开始构建语义索引..." -ForegroundColor Cyan
Write-Host ""

docker $dockerArgs

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ 语义索引构建完成！" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 语义索引构建失败（退出码: $exitCode）" -ForegroundColor Red
}

exit $exitCode


