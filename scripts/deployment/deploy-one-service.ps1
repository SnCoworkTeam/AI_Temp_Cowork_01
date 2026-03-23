# 单服务发布：通过 deployment-agent API 发布指定服务到目标服务器
# 用法: .\scripts\deployment\deploy-one-service.ps1 -ServiceName project-management
# 环境变量: $env:DEPLOYMENT_AGENT_URL 默认 http://localhost:8007

param(
    [Parameter(Mandatory = $true)]
    [string] $ServiceName
)

$baseUrl = if ($env:DEPLOYMENT_AGENT_URL) { $env:DEPLOYMENT_AGENT_URL } else { "http://localhost:8007" }
$uri = "$baseUrl/api/v1/deploy"
$body = @{ services = @($ServiceName); skip_data_sync = $true; skip_migration = $false } | ConvertTo-Json

Write-Host "正在发布服务: $ServiceName (deployment-agent: $baseUrl)" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json"
    Write-Host "请求已接受。" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "请求失败: $_" -ForegroundColor Red
    exit 1
}
