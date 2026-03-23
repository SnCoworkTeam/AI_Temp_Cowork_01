# 在Docker容器内运行语义索引构建的便捷脚本

$CONTAINER_NAME = "enterprise-ai-sap-metadata-agent"
$SCRIPT_PATH = "/app/scripts/build_semantic_in_docker.py"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "在Docker容器内构建语义索引" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查docker-compose是否可用
$dockerComposeAvailable = $false
try {
    $null = docker-compose --version 2>&1
    $dockerComposeAvailable = $true
} catch {
    try {
        $null = docker compose version 2>&1
        $dockerComposeAvailable = $true
    } catch {
        $dockerComposeAvailable = $false
    }
}

# 检查容器是否运行
$containerRunning = $false

if ($dockerComposeAvailable) {
    Write-Host "使用 docker-compose 检查容器状态..." -ForegroundColor Yellow
    try {
        $result = docker-compose ps sap-metadata-agent 2>&1
        if ($result -match "Up") {
            $containerRunning = $true
        }
    } catch {
        try {
            $result = docker compose ps sap-metadata-agent 2>&1
            if ($result -match "Up") {
                $containerRunning = $true
            }
        } catch {
            # 继续尝试其他方法
        }
    }
}

# 如果docker-compose检查失败，尝试直接使用docker ps
if (-not $containerRunning) {
    Write-Host "使用 docker ps 检查容器状态..." -ForegroundColor Yellow
    try {
        $containers = docker ps --format "{{.Names}}" 2>&1
        if ($containers -match $CONTAINER_NAME) {
            $containerRunning = $true
        }
    } catch {
        Write-Host "无法检查容器状态，尝试继续执行..." -ForegroundColor Yellow
    }
}

if (-not $containerRunning) {
    Write-Host "⚠️  容器可能未运行，尝试启动..." -ForegroundColor Yellow
    if ($dockerComposeAvailable) {
        try {
            docker-compose up -d sap-metadata-agent
            Start-Sleep -Seconds 5
        } catch {
            try {
                docker compose up -d sap-metadata-agent
                Start-Sleep -Seconds 5
            } catch {
                Write-Host "无法启动容器，请手动启动: docker-compose up -d sap-metadata-agent" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "请手动启动容器: docker-compose up -d sap-metadata-agent" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "开始构建语义索引..." -ForegroundColor Cyan
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

# 尝试执行
$success = $false
try {
    & docker $dockerArgs
    $success = $true
} catch {
    Write-Host "使用docker命令失败，尝试docker-compose exec..." -ForegroundColor Yellow
    try {
        if ($dockerComposeAvailable) {
            $composeArgs = @("exec", "-T", "sap-metadata-agent", "python", $SCRIPT_PATH)
            if ($batchSize) {
                $composeArgs += "--batch-size"
                $composeArgs += $batchSize
            }
            if ($resume) {
                $composeArgs += "--resume"
            }
            if ($noResume) {
                $composeArgs += "--no-resume"
            }
            docker-compose $composeArgs
            $success = $true
        }
    } catch {
        Write-Host "使用docker-compose exec也失败，尝试docker compose exec..." -ForegroundColor Yellow
        try {
            $composeArgs = @("compose", "exec", "-T", "sap-metadata-agent", "python", $SCRIPT_PATH)
            if ($batchSize) {
                $composeArgs += "--batch-size"
                $composeArgs += $batchSize
            }
            if ($resume) {
                $composeArgs += "--resume"
            }
            if ($noResume) {
                $composeArgs += "--no-resume"
            }
            docker $composeArgs
            $success = $true
        } catch {
            Write-Host "❌ 无法执行Docker命令" -ForegroundColor Red
            Write-Host "请检查:" -ForegroundColor Yellow
            Write-Host "  1. Docker是否已安装并运行" -ForegroundColor White
            Write-Host "  2. 容器是否已启动: docker-compose ps" -ForegroundColor White
            Write-Host "  3. 或者手动进入容器执行:" -ForegroundColor White
            Write-Host "     docker exec -it $CONTAINER_NAME bash" -ForegroundColor Cyan
            Write-Host "     python $SCRIPT_PATH --batch-size 50" -ForegroundColor Cyan
        }
    }
}

if ($success) {
    Write-Host ""
    Write-Host "✅ 命令执行完成" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 命令执行失败" -ForegroundColor Red
    exit 1
}


