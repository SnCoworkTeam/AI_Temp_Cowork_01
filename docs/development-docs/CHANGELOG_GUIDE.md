# 变更日志指南

本文档说明如何维护项目的变更日志（CHANGELOG.md），确保项目变更历史清晰可追溯。

## 变更日志格式

### 基本结构

```markdown
# 变更日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
### 变更
### 修复
### 移除

## [版本号] - YYYY-MM-DD

### 新增
- 功能描述

### 变更
- 变更描述

### 修复
- 修复描述

### 移除
- 移除描述

### 安全
- 安全修复描述
```

## 变更类型

### 新增 (Added)
- 新功能
- 新API端点
- 新配置项
- 新文档

**示例**：
```markdown
### 新增
- 添加自动化调试系统模块（auto_debug）
- 添加平台错误分析器（PlatformErrorAnalyzer）
- 添加修复策略管理器（PlatformFixStrategyManager）
- 添加决策面板前端组件
```

### 变更 (Changed)
- 现有功能的变更
- API行为的变更（向后兼容）
- 性能优化
- 用户体验改进

**示例**：
```markdown
### 变更
- 优化MCP工具执行性能，响应时间减少30%
- 改进工作流设计器用户体验
- 更新依赖库版本
```

### 废弃 (Deprecated)
- 即将移除的功能
- 即将废弃的API

**示例**：
```markdown
### 废弃
- 废弃 `/api/tools/legacy` 端点，将在v2.0.0移除
- 废弃 `old_workflow_engine` 配置项
```

### 移除 (Removed)
- 已移除的功能
- 已移除的API
- 已移除的配置项

**示例**：
```markdown
### 移除
- 移除 `/api/tools/legacy` 端点（已在v1.5.0废弃）
- 移除对Python 3.9的支持
```

### 修复 (Fixed)
- Bug修复
- 安全漏洞修复
- 性能问题修复

**示例**：
```markdown
### 修复
- 修复MCP工具超时处理问题
- 修复工作流状态持久化失败的问题
- 修复前端内存泄漏问题
```

### 安全 (Security)
- 安全漏洞修复
- 安全增强

**示例**：
```markdown
### 安全
- 修复JWT token验证漏洞
- 增强API速率限制
- 修复SQL注入风险
```

## 版本号规则

### 语义化版本

格式：`MAJOR.MINOR.PATCH`

- **MAJOR** (主版本号): 不兼容的API变更
- **MINOR** (次版本号): 向后兼容的功能添加
- **PATCH** (修订号): 向后兼容的问题修复

### 版本号示例

- `1.0.0` - 初始发布
- `1.0.1` - 修复bug
- `1.1.0` - 新增功能
- `2.0.0` - 破坏性变更

## 编写变更日志

### 在开发过程中

每次提交代码时，如果涉及重要变更，应该：

1. 在 `[未发布]` 部分添加变更说明
2. 使用清晰的描述
3. 关联Issue或PR编号

**示例**：
```markdown
## [未发布]

### 新增
- 添加自动化调试系统错误分析器 (#123)

### 修复
- 修复工作流执行超时问题 (#124)
```

### 发布新版本时

1. 将 `[未发布]` 的内容移到新版本号下
2. 更新发布日期
3. 清空 `[未发布]` 部分
4. 创建Git标签

**示例**：
```markdown
## [1.2.0] - 2024-01-20

### 新增
- 添加自动化调试系统模块
  - 平台错误分析器（PlatformErrorAnalyzer）
  - 修复策略管理器（PlatformFixStrategyManager）
  - 调试协调器（DebugOrchestrator）
  - 测试验证器（PlatformTestValidator）
  - 部署管理器（PlatformDeploymentManager）
  - 平台监控器（PlatformMonitor）
- 添加决策面板前端组件
- 添加配置文件：platform_integration.yaml, debug_workflows.yaml, decision_rules.yaml

### 变更
- 更新项目文档结构
- 优化README.md，添加auto_debug模块说明

### 修复
- 修复文档链接问题

## [未发布]
```

## 变更描述最佳实践

### 1. 使用现在时态
- ✅ "添加自动化调试系统"
- ❌ "已添加自动化调试系统"

### 2. 清晰简洁
- ✅ "修复MCP工具超时处理问题"
- ❌ "修复了一些问题"

### 3. 提供上下文
- ✅ "添加自动化调试系统错误分析器（支持MCP工具、工作流引擎、知识库错误识别）"
- ❌ "添加错误分析器"

### 4. 关联Issue/PR
- ✅ "修复工作流执行超时问题 (#124)"
- ❌ "修复工作流执行超时问题"

### 5. 分组相关变更
```markdown
### 新增
- 添加自动化调试系统
  - 平台错误分析器
  - 修复策略管理器
  - 调试协调器
```

## 自动化变更日志

### 从Git提交生成

可以使用工具从Git提交信息自动生成变更日志：

```bash
# 使用conventional-changelog
npm install -g conventional-changelog-cli
conventional-changelog -p angular -i CHANGELOG.md -s
```

### Git提交信息规范

使用约定式提交（Conventional Commits）：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档变更
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**：
```
feat(auto_debug): 添加平台错误分析器

添加PlatformErrorAnalyzer类，支持：
- MCP工具错误识别
- 工作流引擎错误识别
- 知识库错误识别

Closes #123
```

## 变更日志维护

### 定期更新

1. **开发过程中**: 每次重要变更更新 `[未发布]` 部分
2. **发布前**: 整理并格式化变更日志
3. **发布后**: 创建版本标签，更新变更日志

### 审查变更日志

在发布前：
- [ ] 所有重要变更已记录
- [ ] 变更描述清晰准确
- [ ] 版本号正确
- [ ] 日期正确
- [ ] 格式正确

## 变更日志示例

```markdown
# 变更日志

所有重要的项目变更都会记录在此文件中。

## [1.2.0] - 2024-01-20

### 新增
- 添加自动化调试系统模块（src/auto_debug/）
  - 平台错误分析器（PlatformErrorAnalyzer）
    - 支持MCP工具、工作流引擎、认证、知识库、前端UI错误识别
    - 上下文感知分析
    - 智能根因定位
  - 修复策略管理器（PlatformFixStrategyManager）
    - MCP工具修复策略
    - 工作流引擎修复策略
    - 知识库修复策略
    - 前端UI修复策略
  - 调试协调器（DebugOrchestrator）
    - 调试任务管理
    - 修复决策引擎
    - 人工决策接口
    - 平台集成接口
  - 测试验证器（PlatformTestValidator）
    - 平台功能测试
    - 集成场景测试
    - 修复专项测试
    - 平台健康检查
  - 部署管理器（PlatformDeploymentManager）
    - 渐进式部署策略
    - 配置管理
    - 部署健康监控
    - 紧急响应机制
  - 平台监控器（PlatformMonitor）
    - 监控数据收集（Prometheus、Grafana、Loki、Sentry）
    - 智能告警处理
    - 性能基线管理
    - 用户体验监控
- 添加决策面板前端组件（web-ui/src/app/admin/auto-debug/decision-panel.tsx）
- 添加配置文件：
  - config/platform_integration.yaml - 平台集成配置
  - config/debug_workflows.yaml - 调试工作流配置
  - config/decision_rules.yaml - 决策规则配置

### 变更
- 更新README.md，添加auto_debug模块说明
- 更新项目结构文档，反映最新目录结构
- 更新系统架构文档，添加自动化调试系统说明
- 优化文档索引，添加新文档链接

### 文档
- 添加自动化调试系统完整文档（docs/development-docs/auto-debug-system.md）
- 添加快速开始指南（docs/development-docs/QUICK_START.md）
- 添加项目迭代指南（docs/development-docs/ITERATION_GUIDE.md）
- 添加变更日志指南（docs/development-docs/CHANGELOG_GUIDE.md）

## [1.1.0] - 2024-01-15

### 新增
- 添加知识库服务（knowledge-base）
- 添加数据库模块（database）
- 添加认证服务（auth-service）

### 变更
- 优化工作流引擎性能
- 改进前端用户体验

## [1.0.0] - 2024-01-01

### 新增
- 初始发布
- MCP工具网关服务
- 工作流引擎服务
- Web UI前端界面
```

## 相关资源

- [Keep a Changelog](https://keepachangelog.com/)
- [语义化版本](https://semver.org/)
- [约定式提交](https://www.conventionalcommits.org/)

