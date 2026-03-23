# DeepSeek API 测试脚本
# 使用方法: .\test_deepseek.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "DeepSeek API 测试脚本" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 从.env文件读取配置（如果存在）
$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    Write-Host "`n读取.env文件..." -ForegroundColor Yellow
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            if ($key -and $value) {
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
                Write-Host "  ✓ $key = $($value.Substring(0, [Math]::Min(20, $value.Length)))..." -ForegroundColor Green
            }
        }
    }
}

# 检查必要的环境变量
$apiKey = $env:OPENAI_API_KEY
$baseUrl = $env:LLM_BASE_URL
$model = $env:LLM_MODEL

if (-not $apiKey) {
    Write-Host "`n⚠ 警告: OPENAI_API_KEY 未设置" -ForegroundColor Yellow
    Write-Host "   请设置环境变量:" -ForegroundColor Yellow
    Write-Host "   `$env:OPENAI_API_KEY = 'your-deepseek-api-key'" -ForegroundColor White
    Write-Host "   `$env:LLM_BASE_URL = 'https://api.deepseek.com/v1'" -ForegroundColor White
    Write-Host "   `$env:LLM_MODEL = 'deepseek-chat'" -ForegroundColor White
    exit 1
}

if (-not $baseUrl) {
    $env:LLM_BASE_URL = "https://api.deepseek.com/v1"
    Write-Host "`n✓ 设置默认 LLM_BASE_URL: $env:LLM_BASE_URL" -ForegroundColor Green
}

if (-not $model) {
    $env:LLM_MODEL = "deepseek-chat"
    Write-Host "✓ 设置默认 LLM_MODEL: $env:LLM_MODEL" -ForegroundColor Green
}

Write-Host "`n当前配置:" -ForegroundColor Cyan
Write-Host "  OPENAI_API_KEY: $($apiKey.Substring(0, [Math]::Min(10, $apiKey.Length)))..." -ForegroundColor White
Write-Host "  LLM_BASE_URL: $env:LLM_BASE_URL" -ForegroundColor White
Write-Host "  LLM_MODEL: $env:LLM_MODEL" -ForegroundColor White

Write-Host "`n运行测试..." -ForegroundColor Cyan
python test_llm_api.py

