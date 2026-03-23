# 提示词统一管理 - 服务器上传脚本
# 适用于Windows PowerShell

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  提示词统一管理 - 服务器上传" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 服务器配置
$APP_SERVER = "43.143.139.197"
$APP_SERVER_KEY = ".\enterprise_ai_platform.pem"
$APP_SERVER_USER = "ubuntu"
$SERVER_PATH = "/opt/enterprise-ai-platform"

# 检查密钥文件
if (-not (Test-Path $APP_SERVER_KEY)) {
    Write-Host "[错误] 未找到密钥文件: $APP_SERVER_KEY" -ForegroundColor Red
    Write-Host "请确保密钥文件在项目根目录" -ForegroundColor Yellow
    exit 1
}

Write-Host "[配置] 服务器: ${APP_SERVER_USER}@${APP_SERVER}" -ForegroundColor Cyan
Write-Host "[配置] 密钥文件: $APP_SERVER_KEY" -ForegroundColor Cyan
Write-Host "[配置] 目标路径: ${SERVER_PATH}" -ForegroundColor Cyan
Write-Host ""

# 需要上传的文件列表（提示词相关）
$filesToUpload = @(
    # 配置文件
    "agent-service/config/prompt_templates.yaml",
    
    # 核心文件
    "agent-service/src/core/prompt_utils.py",
    "agent-service/src/core/prompt_engine/template_manager.py",
    "agent-service/src/models/prompt_models.py",
    
    # 智能体文件
    "agent-service/src/core/agents/metadata_agent.py",
    "agent-service/src/core/agents/data_query_agent.py",
    "agent-service/src/core/agents/result_synthesis_agent.py",
    "agent-service/src/core/agents/format_agent.py",
    "agent-service/src/core/agents/data_clean_agent.py",
    "agent-service/src/core/agents/data_enrich_agent.py",
    "agent-service/src/core/agents/data_validation_agent.py",
    "agent-service/src/core/agents/analysis_agent.py",
    "agent-service/src/core/agents/insight_agent.py",
    "agent-service/src/core/agents/content_agent.py",
    "agent-service/src/core/agents/quality_check_agent.py",
    "agent-service/src/core/agents/knowledge_base_agent.py",
    "agent-service/src/core/agents/workflow_agent.py",
    "agent-service/src/core/agents/learning_workflow_designer.py",
    "agent-service/src/core/agents/mcp_tool_agent.py",
    "agent-service/src/core/agents/sap_odata_agent.py",
    
    # 工作流设计器
    "agent-service/src/core/dynamic_workflow_designer.py"
)

# 检查SSH连接
Write-Host "[检查] SSH连接..." -ForegroundColor Cyan
$sshTest = ssh -i $APP_SERVER_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=no "${APP_SERVER_USER}@${APP_SERVER}" "echo 'SSH连接成功'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] SSH连接失败" -ForegroundColor Red
    Write-Host $sshTest -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] SSH连接成功" -ForegroundColor Green
Write-Host ""

# 上传文件
Write-Host "[上传] 开始上传文件..." -ForegroundColor Cyan
$uploadCount = 0
$failCount = 0

foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        $remoteDir = "${SERVER_PATH}/$(Split-Path $file -Parent)"
        $remoteFile = "${SERVER_PATH}/$file"
        
        Write-Host "  上传: $file" -ForegroundColor Gray
        
        # 确保远程目录存在
        ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "${APP_SERVER_USER}@${APP_SERVER}" "mkdir -p $remoteDir" | Out-Null
        
        # 上传文件
        scp -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "$file" "${APP_SERVER_USER}@${APP_SERVER}:$remoteFile" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    [OK] $file" -ForegroundColor Green
            $uploadCount++
        } else {
            Write-Host "    [失败] $file" -ForegroundColor Red
            $failCount++
        }
    } else {
        Write-Host "  [警告] 文件不存在: $file" -ForegroundColor Yellow
        $failCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  上传完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  成功: $uploadCount" -ForegroundColor Green
Write-Host "  失败: $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "[下一步] 重启agent-service服务..." -ForegroundColor Cyan
    $restartCmd = "cd $SERVER_PATH; docker compose restart agent-service"
    Write-Host "  执行命令: ssh -i $APP_SERVER_KEY ${APP_SERVER_USER}@${APP_SERVER} `"$restartCmd`"" -ForegroundColor Yellow
    Write-Host ""
    
    # 询问是否立即重启
    $restart = Read-Host "是否立即重启agent-service服务? (Y/N)"
    if ($restart -eq "Y" -or $restart -eq "y") {
        Write-Host "[重启] 正在重启agent-service..." -ForegroundColor Cyan
        $restartResult = ssh -i $APP_SERVER_KEY -o StrictHostKeyChecking=no "${APP_SERVER_USER}@${APP_SERVER}" $restartCmd 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] agent-service已重启" -ForegroundColor Green
        } else {
            Write-Host "[警告] 重启可能失败，请手动检查" -ForegroundColor Yellow
            Write-Host $restartResult -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Green
