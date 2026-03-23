# 快速同步脚本 - 将修改的文件同步到服务器
# 使用方法: .\sync.ps1 或 sync.bat
# 
# 这是 sync-to-server.ps1 的快捷方式，自动检测并上传修改的文件
# 
# 如果遇到执行策略错误，请使用以下方法之一：
# 1. 使用 sync.bat（推荐）
# 2. 临时允许执行：powershell -ExecutionPolicy Bypass -File .\sync.ps1
# 3. 修改执行策略：Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 获取脚本所在目录（项目根目录）
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# 主脚本路径
$MainScript = Join-Path $ScriptRoot "scripts\deployment\sync-to-server.ps1"

# 检查主脚本是否存在
if (-not (Test-Path $MainScript)) {
    Write-Host "错误: 找不到主脚本 $MainScript" -ForegroundColor Red
    exit 1
}

# 调用主脚本，传递所有参数
& $MainScript @args

