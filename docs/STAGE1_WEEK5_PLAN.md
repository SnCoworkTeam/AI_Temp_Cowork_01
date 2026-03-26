# 阶段一第5周工作计划：统一意图服务完善和API集成

**周次**: 第5周  
**目标**: 完善统一意图服务，创建API接口，完成性能优化  
**时间**: 2025-12-02 开始  
**状态**: 进行中

---

## 📋 本周目标

1. **完善统一意图服务**
   - 增强活动能力映射
   - 实现执行建议构建
   - 完善响应格式

2. **创建API接口**
   - 创建统一意图API
   - 实现同步/异步接口
   - 实现错误处理

3. **性能优化**
   - 优化缓存策略
   - 实现批量查询
   - 性能监控

4. **测试和验证**
   - 创建API测试
   - 创建集成测试
   - 验证性能指标

---

## 🎯 具体任务

### 任务1: 完善统一意图服务

**目标**: 增强统一意图服务，添加能力映射和执行建议

**交付物**:
- 增强的`unified_intent_service.py`
- 活动能力映射功能
- 执行建议构建功能

**验收标准**:
- 可以获取活动的能力单元
- 可以构建执行建议
- 响应格式完整

### 任务2: 创建API接口

**目标**: 为统一意图服务创建RESTful API

**交付物**:
- `api/unified_intent_api.py` - API接口
- 意图理解接口
- 活动推荐接口
- 能力查询接口

**验收标准**:
- API响应时间 < 2秒
- API接口文档完整
- 错误处理完善

### 任务3: 性能优化

**目标**: 优化查询性能和可靠性

**交付物**:
- 优化的缓存策略
- 批量查询功能
- 性能监控

**验收标准**:
- API响应时间 p95 < 2秒
- 缓存命中率 > 60%
- 批量查询性能提升

### 任务4: 创建测试脚本

**目标**: 验证统一意图服务和API功能

**交付物**:
- `tests/test_stage1_week5.py` - 测试脚本
- API测试
- 集成测试
- 性能测试

**验收标准**:
- 所有测试用例通过
- API响应时间 < 2秒
- 功能完整性 > 90%

---

## 🏗️ 架构设计

### 统一意图API接口

```python
@router.post("/api/v1/intent/understand")
async def understand_intent(
    request: IntentRequest
) -> UnifiedIntentResponse:
    """理解意图（返回推荐）"""
    service = UnifiedIntentService()
    result = await service.understand_intent(
        request.user_input,
        request.context
    )
    return result

@router.get("/api/v1/intent/activities/{activity_id}/capabilities")
async def get_activity_capabilities(
    activity_id: str
) -> List[CapabilityUnit]:
    """获取活动的能力单元"""
    service = UnifiedIntentService()
    capabilities = await service.get_capabilities_for_activity(activity_id)
    return capabilities
```

### 增强的统一意图服务

```python
class UnifiedIntentService:
    """统一意图服务 - 增强版"""
    
    async def get_capabilities_for_activity(
        self,
        activity_id: str
    ) -> List[CapabilityUnit]:
        """获取活动的能力单元"""
        # 查询ActivityCapabilityMapping
        pass
    
    def _build_execution_suggestions(
        self,
        intent_analysis: UnifiedIntentResult
    ) -> List[ExecutionSuggestion]:
        """构建执行建议"""
        pass
```

---

## 📊 数据流程

```
用户请求
    ↓
API接口
    ↓
统一意图服务
    ↓
企业语义引擎
    ↓
活动能力映射
    ↓
执行建议构建
    ↓
返回响应
```

---

## 📝 实施步骤

### 第1天: 完善统一意图服务
- [ ] 添加活动能力映射功能
- [ ] 实现执行建议构建
- [ ] 完善响应格式

### 第2天: 创建API接口
- [ ] 创建RESTful API
- [ ] 实现意图理解接口
- [ ] 实现能力查询接口

### 第3天: 性能优化
- [ ] 优化缓存策略
- [ ] 实现批量查询
- [ ] 添加性能监控

### 第4天: API测试
- [ ] 创建API测试脚本
- [ ] 测试所有接口
- [ ] 验证错误处理

### 第5天: 集成测试和文档
- [ ] 运行完整测试
- [ ] 更新文档
- [ ] 性能报告

---

## ✅ 验收标准

1. **功能完整性**
   - ✅ 统一意图服务可以获取能力映射
   - ✅ 可以构建执行建议
   - ✅ API接口完整可用

2. **性能指标**
   - ✅ API响应时间 p95 < 2秒
   - ✅ 缓存命中率 > 60%
   - ✅ 功能完整性 > 90%

3. **测试通过**
   - ✅ 所有测试用例通过
   - ✅ 无严重错误
   - ✅ 性能指标达标

---

## 📚 相关文档

- `STAGE1_WEEK1_TEST_REPORT.md` - 第1周测试报告
- `STAGE1_WEEK2_TEST_REPORT.md` - 第2周测试报告
- `STAGE1_WEEK3_TEST_REPORT.md` - 第3周测试报告
- `STAGE1_WEEK4_TEST_REPORT.md` - 第4周测试报告
- `UNIFIED_INTENT_ARCHITECTURE_FINAL.md` - 统一意图架构文档

---

**创建时间**: 2025-12-02  
**状态**: 进行中




