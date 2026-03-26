# 代码健康度监控系统

## 概述

代码健康度监控系统用于持续跟踪和分析代码质量、性能和健康状况，帮助团队及时发现和解决问题。

## 目录结构

```
code-health/
├── quality-metrics/         # 质量指标
│   ├── coverage-trends/    # 覆盖率趋势
│   ├── complexity-trends/  # 复杂度趋势
│   ├── debt-tracking/      # 技术债务跟踪
│   └── bug-density/        # 缺陷密度
├── performance-metrics/     # 性能指标
│   ├── build-times/        # 构建时间
│   ├── test-times/         # 测试时间
│   ├── startup-times/      # 启动时间
│   └── memory-usage/       # 内存使用
└── improvement-plans/      # 改进计划
    ├── refactoring-tasks/  # 重构任务
    ├── optimization-plans/ # 优化计划
    ├── debt-repayment/     # 债务偿还
    └── capability-growth/  # 能力成长
```

## 监控指标

### 质量指标
1. **代码覆盖率**: 单元测试、集成测试覆盖率
2. **复杂度**: 循环复杂度、认知复杂度
3. **重复代码**: 代码重复率
4. **技术债务**: 技术债务量和趋势
5. **缺陷密度**: Bug数量和修复率

### 性能指标
1. **构建时间**: 编译和构建耗时
2. **测试时间**: 测试执行耗时
3. **启动时间**: 服务启动耗时
4. **内存使用**: 运行时内存占用
5. **响应时间**: API响应时间

## 告警机制

### 告警类型
- **质量指标下降**: 覆盖率下降、复杂度上升
- **技术债务累积**: 技术债务超过阈值
- **性能回归**: 性能指标下降
- **安全漏洞**: 发现安全漏洞

### 告警级别
- **Critical**: 需要立即处理
- **High**: 需要优先处理
- **Medium**: 需要计划处理
- **Low**: 可以后续处理

## 使用方法

### 收集指标
```bash
# 收集所有指标
./scripts/code-health/collect-metrics.sh

# 收集质量指标
./scripts/code-health/collect-quality-metrics.sh

# 收集性能指标
./scripts/code-health/collect-performance-metrics.sh
```

### 生成报告
```bash
# 生成健康度报告
./scripts/code-health/generate-report.sh

# 生成趋势分析
./scripts/code-health/generate-trends.sh
```

### 检查告警
```bash
# 检查告警
./scripts/code-health/check-alerts.sh
```

## 相关文档

- [质量指标说明](./quality-metrics/README.md)
- [性能指标说明](./performance-metrics/README.md)
- [改进计划](./improvement-plans/README.md)









