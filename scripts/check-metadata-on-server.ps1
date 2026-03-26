# 检查服务器43上的元数据文件状态
# 对比本地和服务器上的元数据相关文件

$ErrorActionPreference = "Continue"

$SERVER = "ubuntu@43.143.139.197"
$PROJECT_DIR = "/opt/enterprise-ai-platform"
$SSH_KEY = "enterprise_ai_platform.pem"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "检查服务器43上的元数据文件" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查SSH密钥
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "[错误] SSH密钥文件不存在: $SSH_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "[本地] 检查本地元数据文件..." -ForegroundColor Yellow
$localMetadataFiles = Get-ChildItem -Path . -Recurse -Include "*metadata*" -File -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notmatch '\.git|__pycache__|\.pyc|node_modules|\.next|\.venv|venv|backups' } |
    ForEach-Object { $_.FullName.Replace((Get-Location).Path + '\', '').Replace('\', '/') } | Sort-Object

Write-Host "本地元数据相关文件数: $($localMetadataFiles.Count)" -ForegroundColor Green
Write-Host ""

# 检查本地Git状态
Write-Host "[本地] Git最新提交:" -ForegroundColor Yellow
git log -1 --oneline
Write-Host ""

# 检查服务器状态
Write-Host "[服务器] 连接中..." -ForegroundColor Yellow
Write-Host ""

$checkCmd = "cd $PROJECT_DIR && echo '=== Server Git Status ===' && git log -1 --oneline 2>&1 && echo '' && echo '=== Server Git Branch ===' && git branch --show-current 2>&1 && echo '' && echo '=== Check metadata-service ===' && if [ -d metadata-service ]; then echo 'metadata-service exists'; find metadata-service -type f 2>/dev/null | wc -l | xargs echo 'File count:'; ls -la metadata-service/src/models/*.py 2>&1 | head -5; else echo 'metadata-service NOT exists'; fi && echo '' && echo '=== Check sap-metadata-agent ===' && if [ -d sap-metadata-agent ]; then echo 'sap-metadata-agent exists'; find sap-metadata-agent -type f 2>/dev/null | wc -l | xargs echo 'File count:'; else echo 'sap-metadata-agent NOT exists'; fi && echo '' && echo '=== Check shared_libs metadata_models.py ===' && if [ -f shared_libs/src/models/metadata_models.py ]; then echo 'metadata_models.py exists'; ls -lh shared_libs/src/models/metadata_models.py; else echo 'metadata_models.py NOT exists'; fi && echo '' && echo '=== Check knowledge-base document_metadata.py ===' && if [ -f knowledge-base/src/models/document_metadata.py ]; then echo 'document_metadata.py exists'; ls -lh knowledge-base/src/models/document_metadata.py; else echo 'document_metadata.py NOT exists'; fi"

try {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SERVER $checkCmd
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "检查完成" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "[错误] 无法连接到服务器" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "1. 服务器是否可访问 (ping 43.143.139.197)" -ForegroundColor Yellow
    Write-Host "2. SSH密钥文件是否正确" -ForegroundColor Yellow
    Write-Host "3. 服务器用户名是否正确" -ForegroundColor Yellow
    exit 1
}




