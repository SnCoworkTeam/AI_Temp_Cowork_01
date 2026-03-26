# LLM增强关系发现启用说明

## 问题分析

### 当前状态

1. **代码层面**：LLM增强关系发现已经实现，采用混合方案（规则引擎 + LLM增强）
2. **配置层面**：`metadata-service` 的 `docker-compose.yml` 中缺少LLM相关环境变量
3. **实际运行**：虽然代码默认启用LLM，但可能因为配置不完整而没有正常工作

### 混合方案工作原理

```python
# RelationshipDiscoveryService 采用两层发现策略：

# 第一层：规则引擎（快速、准确）
rule_relationships = self.rule_engine.discover_relationships(entities)
# - 基于parent_id的父子关系
# - 基于related_entities的关联关系
# - 基于命名规则的父子关系
# - 基于sap_module的同模块关系（限制为每个实体最多5个）

# 第二层：LLM增强（灵活、智能）
unprocessed_pairs = self._get_unprocessed_pairs(entities, rule_relationships)
# - 只处理规则引擎未识别的实体对
# - 只处理有描述或业务定义的实体对（LLM需要上下文）
llm_relationships = await self.llm_discovery.discover_relationships_batch(unprocessed_pairs)
```

### 为什么LLM增强可能没有启用

1. **环境变量缺失**：`metadata-service` 的 `docker-compose.yml` 中没有配置 `LLM_BASE_URL` 和 `LLM_RELATIONSHIP_DISCOVERY_ENABLED`
2. **实体对过滤**：`_get_unprocessed_pairs` 只返回有描述或业务定义的实体对，如果实体缺少这些字段，LLM不会被调用
3. **API调用失败**：如果LLM API调用失败，可能没有记录错误日志

## 解决方案

### 1. 更新docker-compose.yml配置

已在 `docker-compose.yml` 中为 `metadata-service` 添加LLM环境变量：

```yaml
metadata-service:
  environment:
    # ... 其他配置 ...
    # LLM配置（用于关系发现增强）
    - LLM_BASE_URL=${LLM_BASE_URL:-https://api.deepseek.com}
    - OPENAI_API_KEY=${OPENAI_API_KEY:-}
    - LLM_RELATIONSHIP_DISCOVERY_ENABLED=${LLM_RELATIONSHIP_DISCOVERY_ENABLED:-true}
```

### 2. 重启metadata-service

```bash
docker-compose restart metadata-service
```

### 3. 验证LLM增强是否启用

```bash
# 检查环境变量
docker-compose exec metadata-service env | grep LLM

# 检查服务状态
docker-compose logs --tail=50 metadata-service | grep -i "llm\|relationship"
```

### 4. 测试LLM增强关系发现

```bash
# 使用脚本测试
python scripts/test_llm_relationship_discovery.py

# 或直接调用API
curl -X POST http://localhost:8005/api/ontology/build \
  -H "Content-Type: application/json" \
  -d '{
    "use_llm": true,
    "force_rebuild": false,
    "priority_entities": null
  }'
```

## 预期效果

启用LLM增强后：

1. **规则引擎**：发现基础关系（parent_id、related_entities、命名规则、同模块关系）
2. **LLM增强**：发现复杂和隐含的关系（基于实体描述和业务定义）
3. **关系数量**：预计可增加50-200%的关系数量（取决于实体描述质量）

## 注意事项

1. **实体描述质量**：LLM增强需要实体有描述或业务定义，如果实体缺少这些字段，LLM不会被调用
2. **API调用成本**：LLM增强会调用外部API，可能产生费用，建议：
   - 使用批量处理（batch_size=10）
   - 只处理规则引擎未识别的实体对
   - 设置合理的超时时间（60秒）
3. **性能影响**：LLM增强会增加构建时间，建议：
   - 使用异步处理
   - 分批处理实体对
   - 设置合理的置信度阈值（0.7）

## 验证清单

- [x] 更新docker-compose.yml配置
- [ ] 重启metadata-service
- [ ] 验证环境变量
- [ ] 测试LLM增强关系发现
- [ ] 检查构建日志
- [ ] 验证关系数量是否增加

## 相关文件

- `metadata-service/src/services/relationship_discovery_service.py` - 关系发现服务（混合方案）
- `metadata-service/src/services/relationship_rule_engine.py` - 规则引擎
- `metadata-service/src/services/relationship_llm_discovery.py` - LLM增强服务
- `metadata-service/src/api/ontology.py` - 本体构建API
- `docker-compose.yml` - Docker Compose配置




