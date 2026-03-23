# 基于元数据的意图识别 - 快速启动指南

## 一、系统要求

- ✅ metadata-service 运行中
- ✅ agent-service 运行中
- ✅ knowledge-base 运行中（用于语义搜索）
- ✅ Redis 运行中（用于缓存）

## 二、快速启动

### 2.1 启动服务

确保所有服务已启动：
```bash
docker-compose up -d
```

### 2.2 服务元数据向量化（一次性，可选）

如果需要使用语义服务发现功能，需要先运行向量化脚本：

```bash
# 进入metadata-service容器
docker exec -it enterprise-ai-metadata-service bash

# 运行向量化脚本
python src/scripts/vectorize_services.py
```

**注意**：如果knowledge-base的API有变化，可能需要调整脚本中的API调用。

### 2.3 验证功能

#### 测试元数据查询API
```bash
curl -X POST http://localhost:8005/api/v1/metadata/realtime-query \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "查询SAP销售订单",
    "context": {
      "user_id": "test_user"
    }
  }'
```

#### 测试意图识别
在AI聊天界面输入：
- "查询SAP销售订单"
- "分析9月份的销售数据"
- "创建一个工作流"

系统会自动：
1. 查询相关元数据
2. 构建增强的提示词
3. 进行意图识别
4. 使用元数据指导路由决策

## 三、功能说明

### 3.1 自动功能

以下功能已自动集成，无需额外配置：

1. **元数据增强的意图识别**
   - 每次对话自动查询元数据
   - 自动构建增强提示词
   - 提高意图识别准确率

2. **元数据驱动的路由决策**
   - 根据元数据推荐服务
   - 优化执行策略选择
   - 提高执行成功率

3. **缓存机制**
   - 自动缓存查询结果
   - 5分钟TTL
   - 提高响应速度

### 3.2 可选功能

以下功能需要额外配置：

1. **语义服务发现**
   - 需要运行向量化脚本
   - 需要knowledge-base支持

2. **知识图谱查询**
   - 需要创建service_relations表（可选）
   - 支持多跳关系查询

3. **用户行为模式分析**
   - 需要agent-service提供执行历史API
   - 或使用共享数据库

## 四、监控和调试

### 4.1 查看日志

```bash
# metadata-service日志
docker logs -f enterprise-ai-metadata-service

# agent-service日志
docker logs -f enterprise-ai-agent-service
```

### 4.2 关键日志信息

查找以下日志：
- `Metadata query completed` - 元数据查询完成
- `Built metadata-enhanced system prompt` - 提示词构建成功
- `Enhanced routing decision with metadata` - 路由决策增强成功
- `Using cached metadata` - 使用缓存

### 4.3 性能监控

关注以下指标：
- 元数据查询延迟（应<200ms）
- 意图识别延迟（应<1s）
- 缓存命中率

## 五、故障排查

### 5.1 元数据查询失败

**症状**：日志显示"Failed to get metadata"

**解决方案**：
1. 检查metadata-service是否运行
2. 检查网络连接
3. 系统会自动降级，使用默认提示词

### 5.2 语义搜索失败

**症状**：semantic_services为空

**解决方案**：
1. 检查knowledge-base是否运行
2. 确认已运行向量化脚本
3. 检查knowledge-base API路径

### 5.3 缓存不工作

**症状**：每次查询都重新执行

**解决方案**：
1. 检查Redis是否运行
2. 检查Redis连接配置
3. 系统会自动降级，不使用缓存

## 六、性能优化建议

### 6.1 缓存优化

根据实际使用情况调整缓存TTL：
- `metadata-service/src/core/realtime_metadata_engine.py`: `self.cache_ttl`
- 默认5分钟，可根据需要调整

### 6.2 查询优化

调整查询限制：
- `limit_per_type`: 每种类型的返回数量（默认5）
- 可根据需要增加或减少

### 6.3 超时优化

调整超时时间：
- `query_timeout`: 元数据查询超时（默认3秒）
- 可根据网络情况调整

## 七、下一步

1. **监控系统性能**
   - 观察元数据查询延迟
   - 观察意图识别准确率
   - 观察系统响应时间

2. **收集用户反馈**
   - 意图识别是否更准确
   - 服务推荐是否更相关
   - 执行成功率是否提升

3. **持续优化**
   - 根据实际使用情况调整参数
   - 优化推荐算法
   - 完善降级策略

---

**文档版本**：v1.0  
**最后更新**：2024-12-19


