# 反馈处理脚本

## 脚本说明

### submit-feature-request.sh
提交功能请求。

**使用方法**:
```bash
./scripts/feedback/submit-feature-request.sh "功能描述"
```

### submit-bug-report.sh
提交缺陷报告。

**使用方法**:
```bash
./scripts/feedback/submit-bug-report.sh "缺陷描述"
```

### collect-code-review-feedback.sh
收集代码审查反馈。

**使用方法**:
```bash
./scripts/feedback/collect-code-review-feedback.sh PR编号 审查人
```

### collect-retrospective.sh
收集迭代回顾。

**使用方法**:
```bash
./scripts/feedback/collect-retrospective.sh 开始日期 结束日期
```

### analyze-performance-data.sh
分析性能数据。

**使用方法**:
```bash
./scripts/feedback/analyze-performance-data.sh
```

### analyze-errors.sh
分析错误日志。

**使用方法**:
```bash
./scripts/feedback/analyze-errors.sh
```

### process-feedback.sh
处理反馈队列。

**使用方法**:
```bash
./scripts/feedback/process-feedback.sh
```

### generate-feedback-report.sh
生成反馈报告。

**使用方法**:
```bash
./scripts/feedback/generate-feedback-report.sh
```

### auto-classify-feedback.py
自动分类和路由反馈。

**使用方法**:
```bash
python3 scripts/feedback/auto-classify-feedback.py
```

## 典型工作流

### 处理用户反馈
```bash
# 提交功能请求
./scripts/feedback/submit-feature-request.sh "新功能描述"

# 自动分类
python3 scripts/feedback/auto-classify-feedback.py

# 处理反馈
./scripts/feedback/process-feedback.sh

# 生成报告
./scripts/feedback/generate-feedback-report.sh
```

### 收集开发反馈
```bash
# 收集代码审查反馈
./scripts/feedback/collect-code-review-feedback.sh 123 张三

# 收集迭代回顾
./scripts/feedback/collect-retrospective.sh 2024-01-01 2024-01-14
```

### 分析系统反馈
```bash
# 分析性能数据
./scripts/feedback/analyze-performance-data.sh

# 分析错误日志
./scripts/feedback/analyze-errors.sh
```









