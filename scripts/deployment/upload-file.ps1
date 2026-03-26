# 可靠的文件上传脚本
# 使用分块传输避免大文件导致卡住

param(
    [string]$LocalFile,
    [string]$RemotePath,
    [string]$ConfigFile = "remote.ssh",
    [int]$ChunkSize = 1000  # 每次传输1000行
)

$ErrorActionPreference = "Stop"

# 获取项目根目录
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$ConfigPath = Join-Path $ProjectRoot $ConfigFile

if (-not (Test-Path $ConfigPath)) {
    $ConfigPath = Join-Path (Split-Path $ProjectRoot) $ConfigFile
}

if (-not (Test-Path $LocalFile)) {
    throw "Local file not found: $LocalFile"
}

Write-Host "Uploading: $LocalFile -> $RemotePath" -ForegroundColor Cyan

# 读取文件内容
$content = Get-Content $LocalFile -Raw -Encoding UTF8
$lines = Get-Content $LocalFile -Encoding UTF8

# 清理旧连接
$controlDir = Join-Path $env:USERPROFILE ".ssh"
if (Test-Path $controlDir) {
    Get-ChildItem -Path $controlDir -Filter "control-*" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    }
}

# 使用临时文件传输
$tempFile = [System.IO.Path]::GetTempFileName()
try {
    # 写入临时文件
    $content | Out-File -FilePath $tempFile -Encoding UTF8 -NoNewline
    
    # 使用scp传输（如果可用）或使用cat
    $remoteDir = Split-Path -Parent $RemotePath
    $remoteFile = Split-Path -Leaf $RemotePath
    
    # 先创建目录
    ssh -F $ConfigPath -o ConnectTimeout=10 enterprise-ai-server "mkdir -p $remoteDir" 2>&1 | Out-Null
    
    # 使用base64编码传输（分块）
    $b64Content = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))
    
    # 分块传输（避免命令过长）
    $chunks = @()
    for ($i = 0; $i -lt $b64Content.Length; $i += 5000) {
        $chunk = $b64Content.Substring($i, [Math]::Min(5000, $b64Content.Length - $i))
        $chunks += $chunk
    }
    
    # 先清空远程文件
    ssh -F $ConfigPath -o ConnectTimeout=10 enterprise-ai-server "> $RemotePath" 2>&1 | Out-Null
    
    # 逐块传输并追加
    foreach ($chunk in $chunks) {
        $cmd = "echo '$chunk' | base64 -d >> $RemotePath"
        ssh -F $ConfigPath -o ConnectTimeout=10 enterprise-ai-server $cmd 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to upload chunk"
        }
    }
    
    Write-Host "Upload completed" -ForegroundColor Green
} finally {
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
    }
}

