# 智能体元数据同步验证

## 验证步骤

### 1. 检查智能体注册日志
```bash
docker-compose logs agent-service | grep -i "Synced agent metadata"
```

### 2. 检查metadata-service中的AI模型
```bash
curl "http://localhost:8080/api/metadata/ai-models?tags=agent" | jq '.data[] | {id, name, display_name}'
```

### 3. 检查metadata-service中的业务实体
```bash
curl "http://localhost:8080/api/metadata/business-entities?tags=agent" | jq '.data[] | {id, name, display_name}'
```

### 4. 检查智能体注册表
```bash
curl "http://localhost:8080/api/v1/agents/registry/agents"
```

## 预期结果

### 应该同步的15个智能体

1. metadata_agent - 元数据智能体
2. mcp_tool_agent - MCP工具智能体
3. workflow_agent - 工作流智能体
4. knowledge_base_agent - 知识库智能体
5. data_query_agent - 数据查询智能体
6. data_clean_agent - 数据清洗智能体
7. data_validation_agent - 数据验证智能体
8. data_enrich_agent - 数据增强智能体
9. analysis_agent - 分析智能体
10. insight_agent - 洞察智能体
11. quality_check_agent - 质量检查智能体
12. content_agent - 内容智能体
13. format_agent - 格式化智能体
14. result_synthesis_agent - 结果合成智能体

### 验证指标

- ✅ 智能体注册到本地AgentRegistry
- ✅ 智能体元数据同步到metadata-service（AI模型）
- ✅ 智能体元数据同步到metadata-service（业务实体）
- ✅ 前端可以获取智能体列表

