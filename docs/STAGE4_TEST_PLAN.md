# 阶段4测试计划

## 📋 测试信息

**测试日期**: 2025-11-28  
**阶段**: 阶段4（智能化提升与用户体验优化）  
**测试范围**: 所有阶段4功能模块

---

## 🎯 测试目标

验证阶段4的所有功能模块是否正常工作，包括：
1. 智能推荐与决策支持系统
2. 自然语言交互能力
3. 知识图谱可视化与交互
4. 智能化运维与监控

---

## 📊 测试用例

### 任务1: 智能推荐与决策支持系统

#### 1.1 实体推荐测试

**测试用例1.1.1**: 推荐相关实体
- **端点**: `GET /api/recommendation/entities/{entity_id}/related`
- **测试数据**: entity_id=1001, limit=5
- **预期结果**: 返回相关实体列表，包含推荐分数

**测试用例1.1.2**: 推荐相似实体
- **端点**: `GET /api/recommendation/entities/{entity_id}/similar`
- **测试数据**: entity_id=1001, limit=5
- **预期结果**: 返回相似实体列表，包含相似度分数

**测试用例1.1.3**: 推荐缓存统计
- **端点**: `GET /api/recommendation/cache/stats`
- **预期结果**: 返回缓存统计信息

---

#### 1.2 决策支持测试

**测试用例1.2.1**: 分析实体影响范围
- **端点**: `POST /api/recommendation/decision/analyze-impact`
- **测试数据**: entity_id=1001, analysis_type="direct"
- **预期结果**: 返回影响分析结果

**测试用例1.2.2**: 查找实体间最优路径
- **端点**: `POST /api/recommendation/decision/find-path`
- **测试数据**: source_entity_id=1001, target_entity_id=1002
- **预期结果**: 返回路径分析结果

**测试用例1.2.3**: 获取实体洞察
- **端点**: `GET /api/recommendation/decision/insights/{entity_id}`
- **测试数据**: entity_id=1001
- **预期结果**: 返回实体洞察信息和建议

---

### 任务2: 自然语言交互能力

#### 2.1 自然语言查询测试

**测试用例2.1.1**: 解析自然语言查询
- **端点**: `POST /api/nl-query/parse`
- **测试数据**: query="查找物料相关的实体"
- **预期结果**: 返回解析后的查询结构

**测试用例2.1.2**: 执行自然语言查询
- **端点**: `POST /api/nl-query/query`
- **测试数据**: query="显示与客户相关的所有实体"
- **预期结果**: 返回查询结果和自然语言解释

---

#### 2.2 智能助手测试

**测试用例2.2.1**: 智能助手对话
- **端点**: `POST /api/assistant/chat`
- **测试数据**: message="如何使用推荐功能？"
- **预期结果**: 返回助手响应和建议操作

**测试用例2.2.2**: 回答问题
- **端点**: `POST /api/assistant/answer`
- **测试数据**: question="什么是业务实体？"
- **预期结果**: 返回答案和相关信息

---

### 任务3: 知识图谱可视化与交互

#### 3.1 图谱可视化测试

**测试用例3.1.1**: 获取图谱可视化数据
- **端点**: `GET /api/knowledge-graph/viz/graph-data`
- **测试数据**: max_nodes=100, max_edges=200
- **预期结果**: 返回节点和边数据，格式适合可视化

**测试用例3.1.2**: 获取子图可视化数据
- **端点**: `GET /api/knowledge-graph/viz/subgraph-data/{node_id}`
- **测试数据**: node_id="node-1", max_depth=2
- **预期结果**: 返回子图节点和边数据

**测试用例3.1.3**: 获取路径可视化数据
- **端点**: `POST /api/knowledge-graph/viz/path-visualization`
- **测试数据**: source_id="node-1", target_id="node-2"
- **预期结果**: 返回路径上的节点和边数据

**测试用例3.1.4**: 导出图谱数据
- **端点**: `GET /api/knowledge-graph/viz/export?format=json`
- **预期结果**: 返回JSON格式的图谱数据

---

### 任务4: 智能化运维与监控

#### 4.1 智能化监控测试

**测试用例4.1.1**: 分析性能数据
- **端点**: `POST /api/intelligent-monitoring/analyze-performance`
- **测试数据**: 模拟性能指标数据
- **预期结果**: 返回性能分析结果和优化建议

**测试用例4.1.2**: 预测潜在问题
- **端点**: `POST /api/intelligent-monitoring/predict-issues`
- **测试数据**: 历史性能数据
- **预期结果**: 返回问题预测结果

---

#### 4.2 智能质量检测测试

**测试用例4.2.1**: 检测数据质量问题
- **端点**: `GET /api/intelligent-quality/detect-issues`
- **测试数据**: entity_id=1001（可选）
- **预期结果**: 返回质量问题列表

**测试用例4.2.2**: 计算实体质量分数
- **端点**: `GET /api/intelligent-quality/quality-score/{entity_id}`
- **测试数据**: entity_id=1001
- **预期结果**: 返回质量分数和等级

---

## ✅ 测试执行

开始执行测试...

---

**测试计划生成时间**: 2025-11-28  
**状态**: 🟡 **准备执行**




