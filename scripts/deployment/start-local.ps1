Param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$webUiPath = Join-Path $root "web-ui"
$composeArgs = "-f `"$root\docker-compose.yml`" -f `"$root\docker-compose.local.yml`""
$envPath = Join-Path $root ".env"
$envExamplePath = Join-Path $root ".env.example"

Write-Host "[1/5] Checking legacy container..." -ForegroundColor Cyan
$oldContainer = "ai_template_lyb_20260305"
$legacyName = "AI_TEMP_COWORK-MAIN-legacy"
$existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $oldContainer }
if ($existing) {
    $legacyExists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $legacyName }
    if (-not $legacyExists) {
        docker rename $oldContainer $legacyName
        Write-Host "Renamed legacy container to: $legacyName" -ForegroundColor Yellow
    } else {
        Write-Host "Legacy container exists but target legacy name already exists. Skip rename." -ForegroundColor Yellow
    }
}

Write-Host "[2/5] Starting backend docker services..." -ForegroundColor Cyan
if ((-not (Test-Path $envPath)) -and (Test-Path $envExamplePath)) {
    Copy-Item $envExamplePath $envPath
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}
Invoke-Expression "docker compose $composeArgs up -d --build"

Write-Host "[3/5] Checking main backend container..." -ForegroundColor Cyan
docker ps --filter "name=AI_TEMP_COWORK-MAIN" --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"

if ($SkipFrontend) {
    Write-Host "[4/5] Frontend start skipped by parameter." -ForegroundColor Yellow
    exit 0
}

Write-Host "[4/5] Preparing frontend local config..." -ForegroundColor Cyan
$envLocal = Join-Path $webUiPath ".env.local"
$envExample = Join-Path $webUiPath ".env.local.example"
if ((Test-Path $envExample) -and -not (Test-Path $envLocal)) {
    Copy-Item $envExample $envLocal
}

# 强制修正认证服务直连地址，避免 Next 代理转发到 api-gateway 的 /api/auth 导致登录异常
try {
    if (Test-Path $envLocal) {
        $lines = Get-Content $envLocal
        $lines = $lines | ForEach-Object { $_ }
        $lines = $lines -replace '^NEXT_PUBLIC_AUTH_SERVICE_URL=.*$', 'NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8003'
        Set-Content $envLocal $lines -Encoding UTF8
        Write-Host "已更新 web-ui/.env.local 的 NEXT_PUBLIC_AUTH_SERVICE_URL=localhost:8003" -ForegroundColor Yellow
    }
} catch {
    Write-Host "未能自动修正 .env.local（可手动改为 http://localhost:8003）" -ForegroundColor Yellow
}

Write-Host "[5/5] Starting frontend node service (new window)..." -ForegroundColor Cyan

# 确保 3000 端口空闲，否则 Next.js 会自动切到 3001
$frontPort = 3000
try {
    $pids = Get-NetTCPConnection -LocalPort $frontPort -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    if ($pids) {
        foreach ($pid in $pids) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
        Write-Host "已释放端口 3000，避免切换到 3001" -ForegroundColor Yellow
    }
} catch {
    # 不影响主流程：如果是权限/系统限制导致释放失败，仍会尝试启动
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$webUiPath`"; if (!(Test-Path node_modules)) { npm install --legacy-peer-deps }; npm run dev"

Write-Host "Deployment completed: backend in docker, frontend started in new window." -ForegroundColor Green
