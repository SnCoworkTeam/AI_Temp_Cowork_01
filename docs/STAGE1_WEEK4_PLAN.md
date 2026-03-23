# 阶段一第4周工作计划：统一意图服务增强

**周次**: 第4周  
**目标**: 增强统一意图服务，集成企业语义引擎  
**时间**: 2025-12-02 开始  
**状态**: 进行中

---

## 📋 本周目标

1. **增强IntelligentRouter**
   - 集成企业语义引擎
   - 实现图谱导航能力
   - 实现基于图谱的意图增强

2. **创建统一意图服务**
   - 实现UnifiedIntentService类
   - 实现意图查询增强
   - 实现活动推荐集成

3. **性能优化**
   - 实现缓存机制
   - 实现超时和降级机制
   - 优化查询性能

4. **测试和验证**
   - 创建单元测试
   - 创建集成测试
   - 验证性能指标

---

## 🎯 具体任务

### 任务1: 增强IntelligentRouter

**目标**: 将企业语义引擎集成到IntelligentRouter

**交付物**:
- 增强的`intelligent_router.py`
- 图谱查询集成
- 意图增强功能

**验收标准**:
- IntelligentRouter可以查询企业语义引擎
- 意图分析结果包含图谱信息
- 响应时间 < 2秒

### 任务2: 创建统一意图服务

**目标**: 创建UnifiedIntentService作为图谱导航器

**交付物**:
- `services/unified_intent_service.py` - 统一意图服务
- 意图查询增强
- 活动推荐集成

**验收标准**:
- 可以基于图谱理解意图
- 可以推荐相关业务活动
- 可以返回增强的意图分析

### 任务3: 性能优化

**目标**: 优化查询性能和可靠性

**交付物**:
- 缓存机制实现
- 超时和降级机制
- 性能监控

**验收标准**:
- API响应时间 p95 < 2秒
- 缓存命中率 > 60%
- 超时和降级机制正常

### 任务4: 创建测试脚本

**目标**: 验证统一意图服务功能

**交付物**:
- `tests/test_stage1_week4.py` - 测试脚本
- 单元测试
- 集成测试
- 性能测试

**验收标准**:
- 所有测试用例通过
- API响应时间 < 2秒
- 意图识别准确率 > 80%

---

## 🏗️ 架构设计

### 统一意图服务架构

```python
class UnifiedIntentService:
    """统一意图服务 - 图谱导航器"""
    
    def __init__(self):
        self.semantic_engine = EnterpriseSemanticEngine()
        self.intelligent_router = IntelligentRouter()
        self.cache = {}
    
    async def understand_intent_with_graph(
        self,
        user_input: str,
        context: dict = None
    ) -> EnhancedIntentAnalysis:
        """基于图谱理解意图"""
        # 1. 基础意图识别（使用IntelligentRouter）
        base_intent = self.intelligent_router.analyze_intent(user_input, context)
        
        # 2. 查询企业语义引擎
        graph_results = self.semantic_engine.query_intent(user_input, context)
        
        # 3. 合并结果
        enhanced_intent = self._merge_intent_results(base_intent, graph_results)
        
        return enhanced_intent
    
    def _merge_intent_results(self, base_intent, graph_results):
        """合并基础意图和图谱结果"""
        pass
```

### 增强的IntelligentRouter

```python
class EnhancedIntelligentRouter(IntelligentRouter):
    """增强的智能路由器"""
    
    def __init__(self):
        super().__init__()
        self.semantic_engine = EnterpriseSemanticEngine()
    
    def analyze_intent_with_graph(self, user_input, context=None):
        """基于图谱的意图分析"""
        # 1. 基础意图识别
        base_intent = self.analyze_intent(user_input, context)
        
        # 2. 查询图谱
        graph_results = self.semantic_engine.query_intent(user_input, context)
        
        # 3. 增强意图分析
        enhanced_intent = self._enhance_with_graph(base_intent, graph_results)
        
        return enhanced_intent
```

---

## 📊 数据流程

```
用户输入
    ↓
IntelligentRouter (基础意图识别)
    ↓
企业语义引擎 (图谱查询)
    ↓
统一意图服务 (合并结果)
    ↓
增强的意图分析
    ↓
返回结果
```

---

## 📝 实施步骤

### 第1天: 增强IntelligentRouter
- [ ] 集成企业语义引擎
- [ ] 实现图谱查询功能
- [ ] 实现意图增强逻辑

### 第2天: 创建统一意图服务
- [ ] 创建UnifiedIntentService类
- [ ] 实现意图查询增强
- [ ] 实现结果合并逻辑

### 第3天: 性能优化
- [ ] 实现缓存机制
- [ ] 实现超时机制
- [ ] 实现降级机制

### 第4天: API集成
- [ ] 更新API Gateway
- [ ] 集成统一意图服务
- [ ] 测试API接口

### 第5天: 测试和文档
- [ ] 编写测试用例
- [ ] 运行完整测试
- [ ] 更新文档

---

## ✅ 验收标准

1. **功能完整性**
   - ✅ 统一意图服务可以查询图谱
   - ✅ 意图分析结果包含图谱信息
   - ✅ 活动推荐功能正常

2. **性能指标**
   - ✅ API响应时间 p95 < 2秒
   - ✅ 缓存命中率 > 60%
   - ✅ 意图识别准确率 > 80%

3. **测试通过**
   - ✅ 所有测试用例通过
   - ✅ 无严重错误
   - ✅ 性能指标达标

---

## 📚 相关文档

- `STAGE1_WEEK1_TEST_REPORT.md` - 第1周测试报告
- `STAGE1_WEEK2_TEST_REPORT.md` - 第2周测试报告
- `STAGE1_WEEK3_TEST_REPORT.md` - 第3周测试报告
- `UNIFIED_INTENT_ARCHITECTURE_FINAL.md` - 统一意图架构文档

---

**创建时间**: 2025-12-02  
**状态**: 进行中




