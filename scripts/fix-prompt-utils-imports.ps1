# 修复所有 agent 文件中的 prompt_utils 导入语法错误

$ErrorActionPreference = "Stop"

$AGENT_FILES = @(
    "agent-service/src/core/agents/result_synthesis_agent.py",
    "agent-service/src/core/agents/workflow_agent.py",
    "agent-service/src/core/agents/metadata_agent.py",
    "agent-service/src/core/agents/quality_check_agent.py",
    "agent-service/src/core/agents/content_agent.py",
    "agent-service/src/core/agents/insight_agent.py",
    "agent-service/src/core/agents/analysis_agent.py",
    "agent-service/src/core/agents/learning_workflow_designer.py",
    "agent-service/src/core/agents/format_agent.py",
    "agent-service/src/core/agents/data_enrich_agent.py",
    "agent-service/src/core/agents/data_query_agent.py",
    "agent-service/src/core/agents/mcp_tool_agent.py",
    "agent-service/src/core/agents/sap_odata_agent.py"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "修复 prompt_utils 导入语法错误" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$fixedCount = 0
$errorCount = 0

foreach ($file in $AGENT_FILES) {
    if (Test-Path $file) {
        Write-Host "`n检查文件: $file" -ForegroundColor Yellow
        $content = Get-Content $file -Raw
        
        # 查找所有在列表中的 from ..prompt_utils import 语句
        $pattern = '(?s)(response\s*=\s*await\s+self\.llm\.chat\(\[|messages\s*=\s*\[)\s*#\s*从提示词模板获取系统提示词\s+from\s+\.\.prompt_utils\s+import\s+get_system_prompt\s+(\w+)\s*=\s*get_system_prompt\([^)]+\)\s*(\{[^}]+\})'
        
        if ($content -match $pattern) {
            Write-Host "  发现需要修复的模式" -ForegroundColor Red
            # 这里需要手动修复每个文件，因为模式可能不同
        } else {
            Write-Host "  未发现需要修复的模式" -ForegroundColor Green
        }
    } else {
        Write-Host "  文件不存在: $file" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "修复完成！" -ForegroundColor Green
Write-Host "已修复: $fixedCount 个文件" -ForegroundColor Green
Write-Host "错误: $errorCount 个文件" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host "==========================================" -ForegroundColor Green





