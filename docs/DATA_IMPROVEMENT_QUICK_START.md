# 数据完善快速操作指南

## 🚀 立即执行 - 构建知识图谱关系网络

### 问题现状

- ❌ **知识图谱边: 0条** - 这是最关键的问题
- ⚠️ **知识图谱节点: 5个** - 覆盖率只有0.18%（应该有2726+）
- ❌ **影响**: 推荐、分析、路径查找等功能无法工作

### 解决方案

**执行本体构建API，自动创建节点和发现关系**

---

## 📋 操作步骤

### 步骤1: 执行本体构建（最关键）🔥

```bash
# 执行本体构建API
curl -X POST http://localhost:8005/api/ontology/build \
  -H "Content-Type: application/json" \
  -d '{"use_llm": true}'
```

**预期时间**: 10-30分钟（取决于实体数量和LLM响应时间）

**预期结果**:
- ✅ 知识图谱节点: 从5个增加到2726+个
- ✅ 知识图谱边: 从0条增加到500+条
- ✅ 关系类型: 多样化（parent_of, related_to等）

---

### 步骤2: 监控构建进度

```bash
# 查看metadata-service日志
docker-compose logs -f metadata-service

# 或者查看最近100行日志
docker-compose logs --tail=100 metadata-service
```

**关注日志信息**:
- "Starting ontology build..."
- "Discovered X relationships"
- "Ontology build completed"

---

### 步骤3: 验证构建结果

```bash
# 1. 检查知识图谱统计
curl http://localhost:8005/api/knowledge-graph/stats

# 2. 检查节点数量（应该从5增加到2726+）
curl http://localhost:8005/api/knowledge-graph/nodes?limit=100

# 3. 检查边数量（应该从0增加到500+）
curl http://localhost:8005/api/knowledge-graph/edges?limit=100

# 4. 检查图谱可视化数据
curl http://localhost:8005/api/knowledge-graph/viz/graph-data?max_nodes=100
```

**验证标准**:
- ✅ 节点数量 > 2000
- ✅ 边数量 > 500
- ✅ 关系类型 > 3种

---

### 步骤4: 测试推荐功能

```bash
# 测试相关实体推荐（现在应该能返回结果了）
curl http://localhost:8005/api/recommendation/entities/2/related?limit=5

# 测试实体洞察
curl http://localhost:8005/api/recommendation/decision/insights/2
```

**预期结果**:
- ✅ 推荐功能返回相关实体
- ✅ 洞察功能返回关系信息

---

## 📊 后续完善步骤

### 步骤5: 数据质量评估

```bash
# 运行质量检测
curl http://localhost:8005/api/intelligent-quality/detect-issues

# 检查核心实体质量
curl http://localhost:8005/api/intelligent-quality/quality-score/2
```

### 步骤6: 批量注册实体

```bash
# 批量注册业务实体到统一标识系统
# 使用脚本批量注册所有实体
```

### 步骤7: 导入知识库文档

```bash
# 导入业务文档
POST /api/knowledge/documents
{
  "title": "文档标题",
  "content": "文档内容",
  "content_type": "sop"
}
```

---

## ⚠️ 注意事项

1. **本体构建需要时间**: 2726个实体可能需要10-30分钟
2. **LLM服务**: 如果LLM服务不可用，会降级到仅使用规则引擎
3. **数据库负载**: 大量数据写入可能影响数据库性能
4. **监控日志**: 建议监控服务日志，确保构建成功

---

## 🎯 成功标准

构建完成后，应该达到：

- ✅ 知识图谱节点: 2726+ 个
- ✅ 知识图谱边: 500+ 条
- ✅ 推荐功能: 能返回相关实体
- ✅ 分析功能: 能进行影响分析
- ✅ 可视化: 能显示关系网络

---

**操作指南生成时间**: 2025-11-28  
**优先级**: 🔥 **最高** - 立即执行




