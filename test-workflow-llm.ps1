# 测试工作流 LLM 节点是否调用 DeepSeek API

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试工作流 LLM 节点 DeepSeek API 调用" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$workflowId = "39b49ff2-c628-4bb1-8b8a-8480c980ff52"
$baseUrl = "http://localhost:8002"

Write-Host "1. 获取工作流定义..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/workflows/$workflowId" -Method Get
    $workflow = $response.workflow
    
    Write-Host "   工作流名称: $($workflow.name)" -ForegroundColor Green
    Write-Host "   节点数量: $($workflow.nodes.Count)" -ForegroundColor Green
    
    # 查找 LLM 节点
    $llmNodes = $workflow.nodes | Where-Object { $_.node_type -eq 'llm' }
    if ($llmNodes) {
        Write-Host "`n   找到 $($llmNodes.Count) 个 LLM 节点:" -ForegroundColor Green
        foreach ($node in $llmNodes) {
            Write-Host "   - 节点名称: $($node.name)" -ForegroundColor White
            Write-Host "     模型: $($node.config.model)" -ForegroundColor White
            Write-Host "     Base URL: $($node.config.base_url)" -ForegroundColor White
            Write-Host "     Prompt Template: $($node.config.prompt_template)" -ForegroundColor White
        }
    } else {
        Write-Host "   ⚠ 未找到 LLM 节点" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ 获取工作流失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n2. 执行工作流..." -ForegroundColor Yellow
$inputData = @{
    input_data = @{
        input = "请帮我写一首关于春天的诗"
    }
} | ConvertTo-Json -Depth 10

Write-Host "   Input data: $inputData" -ForegroundColor Gray

try {
    $execResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/workflows/$workflowId/execute" `
        -Method Post `
        -ContentType "application/json" `
        -Body $inputData
    
    Write-Host "`n   执行结果:" -ForegroundColor Green
    Write-Host "   执行ID: $($execResponse.execution_id)" -ForegroundColor White
    Write-Host "   状态: $($execResponse.status)" -ForegroundColor White
    Write-Host "   执行时间: $($execResponse.execution_time) 秒" -ForegroundColor White
    
    if ($execResponse.result) {
        Write-Host "`n   结果内容:" -ForegroundColor Green
        $resultJson = $execResponse.result | ConvertTo-Json -Depth 10
        Write-Host $resultJson -ForegroundColor Gray
    }
    
    if ($execResponse.node_results) {
        Write-Host "`n   节点执行结果:" -ForegroundColor Green
        foreach ($nodeName in $execResponse.node_results.PSObject.Properties.Name) {
            $nodeResult = $execResponse.node_results.$nodeName
            Write-Host "   - $nodeName :" -ForegroundColor Cyan
            if ($nodeResult.output) {
                Write-Host "     输出: $($nodeResult.output | ConvertTo-Json -Compress)" -ForegroundColor White
            }
            if ($nodeResult.error) {
                Write-Host "     错误: $($nodeResult.error)" -ForegroundColor Red
            }
        }
    }
    
} catch {
    Write-Host "   ❌ 执行失败: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   响应: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`n3. 查看工作流引擎日志..." -ForegroundColor Yellow
Write-Host "   运行以下命令查看详细日志:" -ForegroundColor Gray
Write-Host "   docker-compose logs --tail=100 workflow-engine | Select-String -Pattern 'LLM|deepseek|model'" -ForegroundColor Gray

