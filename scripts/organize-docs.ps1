# 文档整理脚本
# 将根目录下的md文档整理到对应的服务目录

Write-Host "开始整理文档..." -ForegroundColor Green

# 定义文档分类规则
$docMapping = @{
    # Agent相关文档 -> agent-service
    "AGENT_*" = "agent-service"
    "MCP_AGENT_*" = "agent-service"
    "MCP_TOOL_AGENT_*" = "agent-service"
    "METADATA_AGENT_*" = "agent-service"
    
    # API Gateway相关文档 -> api-gateway
    "API_GATEWAY_*" = "api-gateway"
    "API_ROUTE_*" = "api-gateway"
    "INTELLIGENT_ROUTING_*" = "api-gateway"
    
    # MCP Gateway相关文档 -> mcp-gateway
    "EMAIL_*" = "mcp-gateway"
    "SAP_ERP_*" = "mcp-gateway"
    "SAP_RFC_*" = "mcp-gateway"
    "DOCKER_PYRFC_*" = "mcp-gateway"
    
    # Workflow相关文档 -> workflow-engine
    "DYNAMIC_WORKFLOW_*" = "workflow-engine"
    "WORKFLOW_*" = "workflow-engine"
    
    # Knowledge Base相关文档 -> knowledge-base
    "KNOWLEDGE_BASE_*" = "knowledge-base"
    "DOCUMENT_*" = "knowledge-base"
    
    # Metadata相关文档 -> metadata-service
    "METADATA_*" = "metadata-service"
    "ENTITY_*" = "metadata-service"
    "ONTOLOGY_*" = "metadata-service"
    
    # SAP相关文档 -> sap-metadata-agent
    "SAP_*" = "sap-metadata-agent"
    
    # Chat相关文档 -> chat-service
    "CHAT_*" = "chat-service"
    "CONVERSATION_*" = "chat-service"
    "MESSAGE_*" = "chat-service"
    
    # DAG相关文档 -> dag-orchestrator
    "DAG_*" = "dag-orchestrator"
    
    # Auth相关文档 -> auth-service
    "AUTH_*" = "auth-service"
    
    # 架构文档 -> docs/architecture-docs
    "ARCHITECTURE_*" = "docs/architecture-docs"
    "COMPREHENSIVE_ARCHITECTURE_*" = "docs/architecture-docs"
    "FINAL_ARCHITECTURE_*" = "docs/architecture-docs"
    "LAYERED_*" = "docs/architecture-docs"
    "UNIFIED_*" = "docs/architecture-docs"
    
    # 部署文档 -> docs/deployment
    "DEPLOYMENT_*" = "docs/deployment"
    "DOCKER_*" = "docs/deployment"
    "BUILD_*" = "docs/deployment"
    
    # 阶段文档 -> docs/stages
    "STAGE*" = "docs/stages"
    "STAGES_*" = "docs/stages"
    
    # 数据相关文档 -> docs/data
    "DATA_*" = "docs/data"
    
    # 实施文档 -> docs/implementation
    "IMPLEMENTATION_*" = "docs/implementation"
    "ENHANCEMENT_*" = "docs/implementation"
}

# 获取根目录下所有md文件
$mdFiles = Get-ChildItem -Path . -Filter "*.md" -File | Where-Object { 
    $_.Name -notmatch "^README" -and 
    $_.Name -notmatch "^PROJECT_CHARTER" -and
    $_.Name -notmatch "^CHANGELOG" -and
    $_.DirectoryName -eq $PWD.Path
}

$movedCount = 0
$skippedCount = 0

foreach ($file in $mdFiles) {
    $fileName = $file.Name
    $targetDir = $null
    
    # 查找匹配的规则
    foreach ($pattern in $docMapping.Keys) {
        if ($fileName -like $pattern) {
            $targetDir = $docMapping[$pattern]
            break
        }
    }
    
    if ($targetDir -and (Test-Path $targetDir)) {
        $targetPath = Join-Path $targetDir $fileName
        if (-not (Test-Path $targetPath)) {
            Move-Item -Path $file.FullName -Destination $targetPath -Force
            Write-Host "移动: $fileName -> $targetDir/" -ForegroundColor Yellow
            $movedCount++
        } else {
            Write-Host "跳过: $fileName (目标文件已存在)" -ForegroundColor Gray
            $skippedCount++
        }
    } else {
        # 如果没有匹配的规则，移动到docs目录
        $docsDir = "docs"
        if (-not (Test-Path $docsDir)) {
            New-Item -ItemType Directory -Path $docsDir | Out-Null
        }
        $targetPath = Join-Path $docsDir $fileName
        if (-not (Test-Path $targetPath)) {
            Move-Item -Path $file.FullName -Destination $targetPath -Force
            Write-Host "移动: $fileName -> docs/ (默认位置)" -ForegroundColor Cyan
            $movedCount++
        } else {
            Write-Host "跳过: $fileName (目标文件已存在)" -ForegroundColor Gray
            $skippedCount++
        }
    }
}

Write-Host "`n整理完成!" -ForegroundColor Green
Write-Host "移动文件数: $movedCount" -ForegroundColor Green
Write-Host "跳过文件数: $skippedCount" -ForegroundColor Gray

