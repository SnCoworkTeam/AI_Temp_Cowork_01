# 基于元数据的意图识别 - 实施任务清单

## 阶段1：快速实现（1-2周）⭐ 优先

### 1.1 实时元数据查询引擎

#### 任务1.1.1：创建RealtimeMetadataEngine类
- [ ] 文件：`metadata-service/src/core/realtime_metadata_engine.py`
- [ ] 功能：
  - [ ] 并行查询数据资产、AI模型、业务实体、工作流
  - [ ] 聚合查询结果
  - [ ] 实现缓存机制（Redis）
  - [ ] 超时控制（默认3秒）
- [ ] 测试：
  - [ ] 单元测试
  - [ ] 集成测试
  - [ ] 性能测试（延迟<200ms）

#### 任务1.1.2：创建API端点
- [ ] 文件：`metadata-service/src/api/realtime_metadata.py`
- [ ] 端点：`POST /api/v1/metadata/realtime-query`
- [ ] 功能：
  - [ ] 接收用户输入和上下文
  - [ ] 调用RealtimeMetadataEngine
  - [ ] 返回聚合的元数据
- [ ] 测试：
  - [ ] API测试
  - [ ] 错误处理测试

#### 任务1.1.3：集成到主路由
- [ ] 文件：`metadata-service/src/main.py`
- [ ] 功能：
  - [ ] 注册新路由
  - [ ] 添加API文档

---

### 1.2 元数据增强的提示词

#### 任务1.2.1：创建MetadataEnhancedPromptBuilder类
- [ ] 文件：`agent-service/src/core/metadata_enhanced_prompt.py`
- [ ] 功能：
  - [ ] 查询相关元数据（调用metadata-service）
  - [ ] 格式化元数据为提示词片段
  - [ ] 构建增强的系统提示
  - [ ] 集成到现有PromptEngine
- [ ] 依赖：
  - [ ] metadata_client（已存在，需增强）
- [ ] 测试：
  - [ ] 单元测试
  - [ ] 提示词质量测试

#### 任务1.2.2：增强metadata_client
- [ ] 文件：`agent-service/src/services/metadata_client.py`
- [ ] 功能：
  - [ ] 添加`get_realtime_metadata`方法
  - [ ] 实现缓存（内存+Redis）
  - [ ] 错误处理和降级
- [ ] 测试：
  - [ ] 客户端测试
  - [ ] 缓存测试

#### 任务1.2.3：集成到ConversationAgent
- [ ] 文件：`agent-service/src/core/conversation_agent.py`
- [ ] 功能：
  - [ ] 在`understand_conversation`中调用MetadataEnhancedPromptBuilder
  - [ ] 使用元数据增强的提示词进行意图分析
  - [ ] 保持向后兼容（降级策略）
- [ ] 测试：
  - [ ] 意图识别准确率测试
  - [ ] 性能测试

---

### 1.3 测试和文档

#### 任务1.3.1：集成测试
- [ ] 创建测试场景：
  - [ ] SAP查询意图识别
  - [ ] 工作流任务识别
  - [ ] 复杂分析任务识别
- [ ] 验证：
  - [ ] 元数据查询正常
  - [ ] 提示词增强生效
  - [ ] 意图识别准确率提升

#### 任务1.3.2：性能测试
- [ ] 测试指标：
  - [ ] 元数据查询延迟（目标<200ms）
  - [ ] 意图识别延迟（目标<1s）
  - [ ] 系统响应时间（目标<2s）
- [ ] 优化：
  - [ ] 缓存优化
  - [ ] 查询优化

#### 任务1.3.3：文档更新
- [ ] API文档
- [ ] 架构文档
- [ ] 使用指南

---

## 阶段2：核心能力（2-4周）

### 2.1 语义服务发现

#### 任务2.1.1：服务元数据向量化脚本
- [ ] 文件：`metadata-service/src/scripts/vectorize_services.py`
- [ ] 功能：
  - [ ] 读取所有服务元数据（数据资产、AI模型、工作流）
  - [ ] 生成向量（使用knowledge-base的embedding）
  - [ ] 存储到knowledge-base向量库
  - [ ] 创建索引
- [ ] 运行：
  - [ ] 一次性执行脚本
  - [ ] 验证向量化结果

#### 任务2.1.2：创建SemanticServiceDiscovery类
- [ ] 文件：`metadata-service/src/core/semantic_service_discovery.py`
- [ ] 功能：
  - [ ] 对用户输入进行向量化
  - [ ] 在向量库中搜索相似服务
  - [ ] 返回匹配结果（带相似度分数）
- [ ] 依赖：
  - [ ] knowledge-base客户端
- [ ] 测试：
  - [ ] 语义搜索准确性测试
  - [ ] 性能测试

#### 任务2.1.3：集成到RealtimeMetadataEngine
- [ ] 文件：`metadata-service/src/core/realtime_metadata_engine.py`
- [ ] 功能：
  - [ ] 在并行查询中包含语义服务发现
  - [ ] 合并文本搜索和语义搜索结果
  - [ ] 排序和去重
- [ ] 测试：
  - [ ] 集成测试
  - [ ] 结果质量测试

---

### 2.2 元数据驱动的执行编排

#### 任务2.2.1：创建MetadataDrivenExecutor类
- [ ] 文件：`agent-service/src/core/metadata_driven_executor.py`
- [ ] 功能：
  - [ ] 使用元数据指导路由决策
  - [ ] 服务推荐
  - [ ] 执行优化
- [ ] 集成：
  - [ ] 集成到OrchestrationEngine
  - [ ] 替换或增强现有路由逻辑
- [ ] 测试：
  - [ ] 路由决策准确性测试
  - [ ] 执行成功率测试

#### 任务2.2.2：增强TaskClassifier
- [ ] 文件：`agent-service/src/core/task_classifier.py`
- [ ] 功能：
  - [ ] 使用元数据信息进行分类
  - [ ] 服务匹配算法
  - [ ] 置信度计算
- [ ] 测试：
  - [ ] 分类准确性测试

---

## 阶段3：高级能力（4-8周，可选）

### 3.1 元数据知识图谱

#### 任务3.1.1：设计关系模型
- [ ] 文件：`metadata-service/src/models/metadata_graph.py`
- [ ] 功能：
  - [ ] 定义服务关系表（service_relations）
  - [ ] 定义意图-服务关系
  - [ ] 定义用户-服务关系
- [ ] 数据库迁移：
  - [ ] 创建表结构
  - [ ] 迁移现有数据

#### 任务3.1.2：实现MetadataGraph类
- [ ] 文件：`metadata-service/src/core/metadata_graph.py`
- [ ] 功能：
  - [ ] 递归查询（PostgreSQL CTE）
  - [ ] 多跳关系查询
  - [ ] 关系推荐
- [ ] 测试：
  - [ ] 查询准确性测试
  - [ ] 性能测试

#### 任务3.1.3：集成到RealtimeMetadataEngine
- [ ] 文件：`metadata-service/src/core/realtime_metadata_engine.py`
- [ ] 功能：
  - [ ] 在查询中包含关系信息
  - [ ] 推荐相关服务
- [ ] 测试：
  - [ ] 集成测试

---

### 3.2 用户行为模式分析

#### 任务3.2.1：创建UserPatternAnalyzer类
- [ ] 文件：`metadata-service/src/core/user_pattern_analyzer.py`
- [ ] 功能：
  - [ ] 从执行历史提取模式
  - [ ] 分析用户偏好
  - [ ] 生成推荐
- [ ] 数据源：
  - [ ] agent-service执行历史
  - [ ] 对话元数据
- [ ] 测试：
  - [ ] 模式识别准确性测试

#### 任务3.2.2：实现推荐算法
- [ ] 文件：`metadata-service/src/core/recommendation_engine.py`
- [ ] 功能：
  - [ ] 基于用户历史推荐服务
  - [ ] 基于相似用户推荐
  - [ ] 基于内容推荐
- [ ] 测试：
  - [ ] 推荐准确性测试

---

## 通用任务

### 监控和日志
- [ ] 添加性能监控
  - [ ] 元数据查询延迟
  - [ ] 意图识别延迟
  - [ ] 系统响应时间
- [ ] 添加日志
  - [ ] 关键操作日志
  - [ ] 错误日志
  - [ ] 性能日志

### 配置管理
- [ ] 环境变量配置
  - [ ] 缓存TTL
  - [ ] 查询超时
  - [ ] 向量搜索参数
- [ ] 配置文件
  - [ ] 默认配置
  - [ ] 生产配置

### 错误处理
- [ ] 降级策略
  - [ ] 元数据查询失败时的处理
  - [ ] 向量搜索失败时的处理
- [ ] 错误恢复
  - [ ] 重试机制
  - [ ] 超时处理

---

## 验收标准

### 阶段1验收标准
- [x] 实时元数据查询引擎正常工作
- [x] 元数据增强提示词生效
- [x] 意图识别准确率提升≥5%
- [x] 系统响应时间<2s（P95）

### 阶段2验收标准
- [ ] 语义服务发现准确率≥80%
- [ ] 元数据驱动执行成功率提升≥5%
- [ ] 服务推荐准确率≥70%

### 阶段3验收标准（可选）
- [ ] 知识图谱查询正常工作
- [ ] 用户行为模式分析准确率≥75%
- [ ] 推荐系统准确率≥70%

---

## 时间估算

| 阶段 | 任务 | 估算时间 |
|------|------|----------|
| 阶段1 | 实时元数据查询引擎 | 3-5天 |
| 阶段1 | 元数据增强提示词 | 3-5天 |
| 阶段1 | 测试和文档 | 2-3天 |
| **阶段1总计** | | **8-13天** |
| 阶段2 | 语义服务发现 | 5-7天 |
| 阶段2 | 元数据驱动执行 | 5-7天 |
| 阶段2 | 测试和优化 | 3-5天 |
| **阶段2总计** | | **13-19天** |
| 阶段3 | 知识图谱 | 7-10天 |
| 阶段3 | 用户行为分析 | 5-7天 |
| 阶段3 | 测试和优化 | 3-5天 |
| **阶段3总计** | | **15-22天** |

**总计**：36-54天（约5-8周）

---

## 依赖关系

```
阶段1
  ├─ 实时元数据查询引擎
  │   └─ metadata-service API
  │
  └─ 元数据增强提示词
      ├─ metadata_client
      └─ PromptEngine

阶段2
  ├─ 语义服务发现
  │   ├─ knowledge-base (向量搜索)
  │   └─ 服务元数据向量化 (一次性)
  │
  └─ 元数据驱动执行
      ├─ 阶段1成果
      └─ OrchestrationEngine

阶段3 (可选)
  ├─ 知识图谱
  │   └─ PostgreSQL递归查询
  │
  └─ 用户行为分析
      └─ 执行历史数据
```

---

**最后更新**：2024-12-19


