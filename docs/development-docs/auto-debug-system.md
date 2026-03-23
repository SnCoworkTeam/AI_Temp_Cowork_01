# 自动化调试系统文档

## 概述

自动化调试系统是平台的核心功能模块，提供智能错误分析、自动修复策略、调试协调、测试验证、部署管理和监控集成等完整功能。

## 系统架构

自动化调试系统位于 `src/auto_debug/` 目录，包含以下核心模块：

```
src/auto_debug/
├── __init__.py                    # 模块导出
├── platform_error_analyzer.py   # 平台错误分析器
├── platform_fix_strategies.py    # 修复策略管理
├── debug_orchestrator.py         # 调试协调器
├── platform_test_validator.py    # 测试验证器
├── platform_deployment.py        # 部署管理器
└── platform_monitor.py           # 平台监控器
```

## 核心模块

### 1. 平台错误分析器 (PlatformErrorAnalyzer)

**功能**：智能分析平台特有错误，识别错误模式，定位根因。

**主要特性**：
- 平台特有错误模式识别（MCP工具、工作流引擎、认证、知识库、前端UI）
- 上下文感知分析（业务场景、数据流、服务调用链）
- 智能根因定位（代码、配置、数据、环境、交互错误）

**使用示例**：
```python
from src.auto_debug import get_error_analyzer, analyze_error

# 获取分析器实例
analyzer = get_error_analyzer()

# 分析错误
analysis = await analyze_error(
    error_message="MCP tool execution timeout",
    error_traceback="...",
    context={"service": "mcp-gateway", "tool": "sap_query"}
)

# 查看分析结果
print(f"错误类别: {analysis.error_category}")
print(f"根因: {analysis.root_cause}")
print(f"置信度: {analysis.confidence}")
```

### 2. 修复策略管理 (PlatformFixStrategyManager)

**功能**：管理平台特有的修复策略库，自动选择和组合修复策略。

**修复策略类型**：
- **MCP工具修复**：重试、参数验证、备用工具切换
- **工作流引擎修复**：状态恢复、节点重试、依赖检测、版本回滚
- **知识库修复**：索引重建、文档重解析、搜索优化、缓存清理
- **前端UI修复**：API重试、状态同步、错误边界、本地存储清理

**使用示例**：
```python
from src.auto_debug import get_fix_strategy_manager, apply_fix

# 获取策略管理器
manager = get_fix_strategy_manager()

# 应用修复
result = await apply_fix(
    error_category="mcp_tool",
    error_type="timeout",
    context={"tool_name": "sap_query"}
)

if result.success:
    print(f"修复成功: {result.message}")
else:
    print(f"修复失败: {result.error}")
```

### 3. 调试协调器 (DebugOrchestrator)

**功能**：协调整个自动化调试过程，管理调试任务，提供决策支持。

**主要功能**：
- 调试任务管理（接收错误报告、分配任务、跟踪进度）
- 修复决策引擎（评估可行性、计算风险、选择策略、生成计划）
- 人工决策接口（识别决策点、提供信息、支持审批）
- 平台集成接口（监控、API调用、日志、配置更新）

**使用示例**：
```python
from src.auto_debug import get_debug_orchestrator, submit_error_for_debugging

# 获取协调器
orchestrator = get_debug_orchestrator()

# 提交错误报告
task = await submit_error_for_debugging(
    error_message="Workflow execution failed",
    error_traceback="...",
    context={"workflow_id": "wf-123"}
)

# 检查任务状态
status = await orchestrator.get_task_status(task.task_id)
print(f"任务状态: {status.status}")

# 获取修复计划
if status.status == "analysis_complete":
    plan = await orchestrator.get_fix_plan(task.task_id)
    print(f"修复策略: {plan.strategy}")
    print(f"风险评估: {plan.risk_level}")
```

### 4. 测试验证器 (PlatformTestValidator)

**功能**：验证平台修复效果的测试框架。

**测试类型**：
- **平台功能测试**：MCP工具、工作流执行、知识库搜索、用户认证
- **集成场景测试**：端到端流程、服务调用链、数据一致性、性能回归
- **修复专项测试**：针对修复代码的测试、边界条件、错误重现、并发场景
- **平台健康检查**：服务健康、数据库连接、外部依赖、资源使用

**使用示例**：
```python
from src.auto_debug import get_test_validator

# 获取验证器
validator = get_test_validator()

# 运行功能测试
result = await validator.run_functional_tests(
    services=["mcp-gateway", "workflow-engine"],
    test_scenarios=["mcp_tool_functionality", "workflow_execution"]
)

print(f"测试通过率: {result.pass_rate}%")
print(f"总测试数: {result.total_tests}")
print(f"失败测试: {result.failed_tests}")
```

### 5. 部署管理器 (PlatformDeploymentManager)

**功能**：智能管理平台部署，支持渐进式部署和自动回滚。

**主要功能**：
- 渐进式部署策略（按重要性顺序、分批部署、回滚预案）
- 配置管理（环境验证、依赖管理、密钥管理、变更追踪）
- 部署健康监控（实时监控、启动检查、性能基线、用户影响）
- 紧急响应机制（自动回滚、服务降级、故障隔离、告警升级）

**使用示例**：
```python
from src.auto_debug import get_deployment_manager

# 获取部署管理器
manager = get_deployment_manager()

# 创建部署计划
plan = await manager.create_deployment_plan(
    version="v1.2.0",
    services=["mcp-gateway", "workflow-engine"],
    deployment_strategy="gradual"
)

# 执行部署
result = await manager.execute_deployment(plan.plan_id, dry_run=False)

# 监控部署过程
monitoring = await manager.monitor_deployment(plan.plan_id, duration=300)
```

### 6. 平台监控器 (PlatformMonitor)

**功能**：与现有监控系统深度集成，提供智能告警和性能分析。

**主要功能**：
- 监控数据收集（Prometheus、Grafana、Loki、Sentry）
- 智能告警处理（告警规则、相关性分析、自动分类路由、响应建议）
- 性能基线管理（基线建立、异常检测、趋势预测、容量规划）
- 用户体验监控（操作成功率、响应时间、错误率、满意度）

**使用示例**：
```python
from src.auto_debug import get_platform_monitor

# 获取监控器
monitor = get_platform_monitor({
    "prometheus_url": "http://localhost:9090",
    "grafana_url": "http://localhost:3000",
    "loki_url": "http://localhost:3100"
})

# 收集Prometheus指标
metrics = await monitor.collect_prometheus_metrics(
    query='http_request_duration_seconds{service="mcp-gateway"}'
)

# 评估告警
alerts = await monitor.evaluate_alerts({
    "service": "mcp-gateway",
    "error_rate": 6.5,
    "avg_response_time": 1200
})

# 建立性能基线
baseline = await monitor.establish_performance_baseline(
    metric_name="response_time",
    service="mcp-gateway",
    duration_days=7
)
```

## 配置管理

### 配置文件位置

- `config/platform_integration.yaml` - 平台集成配置
- `config/debug_workflows.yaml` - 调试工作流配置
- `config/decision_rules.yaml` - 决策规则配置

### 配置示例

```yaml
# config/platform_integration.yaml
service_monitoring:
  mcp-gateway:
    base_url: "${MCP_GATEWAY_URL:-http://localhost:8001}"
    endpoints:
      health_check:
        path: "/api/health"
        method: "GET"
```

## 工作流程

### 完整调试流程

1. **错误检测** → 监控告警触发 → 错误日志分析 → 影响范围评估 → 调试任务创建
2. **分析诊断** → 错误根因分析 → 相关上下文收集 → 修复方案生成 → 风险评估计算
3. **修复执行** → 修复方案审批 → 代码/配置修改 → 测试验证执行 → 部署发布管理
4. **效果验证** → 监控指标对比 → 用户反馈收集 → 业务影响评估 → 经验总结记录

详细流程配置见 `config/debug_workflows.yaml`。

## 决策规则

### 自动执行场景

- 低风险配置修改
- 已知错误模式的标准修复
- 非业务时间的紧急修复
- 测试环境的全权修复

### 需要人工决策场景

- 涉及用户数据的修改
- 核心业务流程的变更
- 架构级别的调整
- 安全相关的修复
- 性能敏感的操作

详细规则见 `config/decision_rules.yaml`。

## 前端界面

### 决策面板

位置：`web-ui/src/app/admin/auto-debug/decision-panel.tsx`

**功能**：
- 决策信息展示（错误分析、修复方案对比、风险评估、影响范围可视化）
- 决策建议生成（AI推荐、利弊分析、历史案例、专家建议）
- 快速审批流程（一键批准、分级审批、审批记录、紧急通道）
- 决策效果追踪（结果记录、反馈收集、质量评估、优化建议）

## 集成指南

### 在服务中使用

```python
# 在服务中集成错误分析
from src.auto_debug import get_error_analyzer

analyzer = get_error_analyzer()

try:
    # 业务逻辑
    result = await some_operation()
except Exception as e:
    # 自动分析错误
    analysis = await analyzer.analyze_error(
        error_message=str(e),
        error_traceback=traceback.format_exc(),
        context={"service": "my-service"}
    )
    
    # 根据分析结果采取行动
    if analysis.confidence > 0.8:
        # 高置信度，可以自动修复
        from src.auto_debug import apply_fix
        fix_result = await apply_fix(
            error_category=analysis.error_category,
            error_type=analysis.error_type,
            context=analysis.context
        )
```

### 监控集成

```python
# 在服务中集成监控
from src.auto_debug import get_platform_monitor

monitor = get_platform_monitor()

# 跟踪用户操作
await monitor.track_user_operation_success(
    service="my-service",
    operation="api_call",
    success=True,
    response_time=250
)

# 获取用户体验摘要
summary = await monitor.get_user_experience_summary(
    service="my-service",
    hours=24
)
```

## 测试

### 运行测试

```bash
# 运行自动化调试系统测试
pytest tests/test_auto_debug/ -v

# 运行特定模块测试
pytest tests/test_auto_debug/test_error_analyzer.py -v
```

### 测试覆盖率

目标覆盖率 >= 85%

```bash
# 检查覆盖率
pytest tests/test_auto_debug/ --cov=src/auto_debug --cov-report=html
```

## 最佳实践

1. **错误分析**：优先使用平台错误分析器，而不是直接处理错误
2. **修复策略**：使用修复策略管理器，而不是硬编码修复逻辑
3. **测试验证**：修复后必须运行测试验证器确保效果
4. **监控集成**：使用平台监控器收集和分析指标
5. **决策支持**：利用决策面板进行人工决策，避免盲目批准

## 故障排查

### 常见问题

**Q: 错误分析置信度低怎么办？**
A: 检查是否提供了足够的上下文信息，考虑增加更多相关日志和数据。

**Q: 修复策略执行失败？**
A: 检查修复策略配置，确保服务端点和权限正确配置。

**Q: 测试验证失败？**
A: 检查测试环境配置，确保依赖服务正常运行。

## 更新日志

- **v1.0.0** (2024-01-20): 初始版本，包含所有核心模块

## 相关文档

- [平台集成配置](../config/platform_integration.yaml)
- [调试工作流配置](../config/debug_workflows.yaml)
- [决策规则配置](../config/decision_rules.yaml)
- [架构文档](../architecture-docs/system-overview/system-architecture.md)

