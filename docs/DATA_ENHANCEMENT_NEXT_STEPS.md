# 数据完善下一步工作

## 当前状态

- ✅ 服务已重启，LLM配置已加载
- ✅ 更新了8个实体的模块信息
- ⚠️ LLM API调用失败（已修复API格式，需要重启服务验证）

## 立即行动项

### 1. 验证LLM API修复（优先级：高）

重启服务后，测试LLM API是否正常工作：

```bash
# 重启服务
docker-compose restart metadata-service

# 等待服务启动
sleep 10

# 检查服务状态
docker-compose ps | grep metadata-service

# 测试LLM API（可选，如果需要）
# 可以通过构建知识图谱来测试
```

### 2. 继续完善实体数据（优先级：高）

#### 2.1 补充更多模块信息

**目标**: 让至少50%的实体有模块信息

**方法**:
- 运行 `scripts/enhance_entity_data.py` 脚本（已创建）
- 或手动分析实体描述，补充模块信息

**当前进度**: 8/1000 (0.8%)

#### 2.2 补充parent_id字段

**目标**: 让至少20%的实体有parent_id

**方法**:
- 分析实体名称模式
- 识别业务层次结构
- 使用脚本自动匹配

#### 2.3 补充related_entities字段

**目标**: 让至少30%的实体有related_entities

**方法**:
- 分析业务关系
- 基于数据流识别关联
- 使用LLM分析（如果API修复成功）

### 3. 重新构建知识图谱

#### 3.1 使用规则引擎构建（不依赖LLM）

```bash
curl -X POST http://localhost:8005/api/ontology/build \
  -H "Content-Type: application/json" \
  -d '{
    "use_llm": false,
    "force_rebuild": false
  }'
```

#### 3.2 使用LLM增强构建（如果API修复成功）

```bash
curl -X POST http://localhost:8005/api/ontology/build \
  -H "Content-Type: application/json" \
  -d '{
    "use_llm": true,
    "force_rebuild": false
  }'
```

## 预期效果

如果完成数据完善：
- 500个实体有模块信息 → 约2500条同模块关系
- 200个实体有parent_id → 200条父子关系
- 300个实体有related_entities → 900条关联关系

**总计**: 约3600条潜在关系，实际可创建2000-3000条边

## 时间估算

- 补充模块信息（50%实体）: 2-4小时
- 补充parent_id（20%实体）: 1-2小时
- 补充related_entities（30%实体）: 2-3小时
- 重新构建知识图谱: 10-30分钟

**总计**: 约1天工作量




