# 代码健康度监控脚本

## 脚本说明

### collect-metrics.sh
收集所有代码健康度指标。

**使用方法**:
```bash
./scripts/code-health/collect-metrics.sh
```

### collect-quality-metrics.sh
收集质量指标（覆盖率、复杂度、技术债务、缺陷密度）。

**使用方法**:
```bash
./scripts/code-health/collect-quality-metrics.sh
```

### collect-performance-metrics.sh
收集性能指标（构建时间、测试时间、启动时间、内存使用）。

**使用方法**:
```bash
./scripts/code-health/collect-performance-metrics.sh
```

### generate-report.sh
生成代码健康度报告。

**使用方法**:
```bash
./scripts/code-health/generate-report.sh
```

### generate-trends.sh
生成趋势分析。

**使用方法**:
```bash
./scripts/code-health/generate-trends.sh
```

### check-alerts.sh
检查代码健康度告警。

**使用方法**:
```bash
./scripts/code-health/check-alerts.sh
```

### generate-summary.sh
生成代码健康度汇总。

**使用方法**:
```bash
./scripts/code-health/generate-summary.sh
```

## 典型工作流

### 每日监控
```bash
# 收集指标
./scripts/code-health/collect-metrics.sh

# 检查告警
./scripts/code-health/check-alerts.sh

# 生成报告
./scripts/code-health/generate-report.sh
```

### 每周分析
```bash
# 生成趋势分析
./scripts/code-health/generate-trends.sh

# 生成汇总
./scripts/code-health/generate-summary.sh
```

## 依赖工具

### 必需工具
- pytest + pytest-cov (覆盖率)
- radon (复杂度分析)
- git (版本控制)

### 可选工具
- pylint (代码质量)
- flake8 (代码风格)
- matplotlib (图表生成)

## 安装依赖

```bash
pip install -r scripts/code-health/requirements.txt
```









