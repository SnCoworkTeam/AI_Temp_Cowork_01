# 变更日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增
- **元数据服务增强功能**
  - 添加数据血缘分析功能
    - `GET /api/lineage/impact/{asset_id}` - 影响分析（分析资产变更对下游的影响）
    - `GET /api/lineage/lineage/{asset_id}` - 获取数据血缘详情（包含完整图谱和分析）
    - `GET /api/lineage/root-cause/{asset_id}` - 根因分析（分析资产问题的上游根因）
  - 添加元数据统一API接口
    - `GET /api/metadata/assets` - 列出数据资产（支持分类、业务域、质量分数过滤）
    - `GET /api/metadata/assets/{asset_id}` - 获取资产详情（包含血缘关系等扩展信息）
    - `GET /api/metadata/search` - 搜索元数据（返回结构化搜索结果）
  - 增强数据质量管理功能
    - `GET /api/quality/metrics/{asset_id}` - 获取数据质量指标（标准化格式）
    - `POST /api/quality/checks/{asset_id}` - 执行质量检查（运行完整的质量评估）
    - `GET /api/quality/dashboard` - 质量监控仪表板（包含质量分布、主要问题、趋势数据）
  - 添加新的响应模型
    - `ImpactAnalysis` - 影响分析模型（包含受影响资产、影响路径、风险等级、建议措施）
    - `RootCauseAnalysis` - 根因分析模型（包含来源资产、关键路径、数据质量问题、建议措施）
    - `DataLineageDetail` - 数据血缘详情模型（包含完整图谱和分析）
    - `DataAssetDetail` - 数据资产详情模型（包含血缘关系等扩展信息）
    - `SearchResults` - 搜索结果模型（包含分面信息）
    - `QualityCheckResult` - 质量检查结果模型（包含检查状态、问题、建议）
    - `QualityDashboard` - 质量监控仪表板模型（包含统计、分布、趋势数据）
- 添加完整的项目文档系统
- 添加项目迭代指南
- 添加变更日志指南
- 添加快速开始指南
- **元数据服务 (metadata-service)**
  - 添加元数据自动采集服务
    - 服务启动时自动注册基础元数据
    - 数据变更时自动更新元数据版本
    - 工具执行时自动收集使用统计
    - 工作流运行时自动收集执行指标
    - 用户交互时收集访问模式
  - 添加数据血缘追踪功能
    - MCP工具执行血缘追踪
    - 工作流执行血缘追踪
    - 知识处理血缘追踪
    - 模型推理血缘追踪
  - 增强数据血缘模型
    - 添加 `source_asset` 和 `target_asset` 字段
    - 添加 `transformation` 字段
    - 添加 `business_rules` 字段
    - 添加 `data_quality_impact` 字段
  - 添加 `DataQualityMetrics` 模型
    - 核心质量指标（完整性、准确性、一致性、及时性、有效性、唯一性）
    - 总体评分计算
    - 质量等级获取

### 文档
- 更新README.md，添加auto_debug模块说明
- 更新项目结构文档
- 更新系统架构文档
- 更新API文档索引
- 添加元数据服务采集时机说明文档 (COLLECTION_TIMING.md)
- 添加元数据服务血缘追踪说明文档 (LINEAGE_TRACKING.md)
- 更新元数据服务README，添加新功能说明

## [1.2.0] - 2024-01-20

### 新增
- 添加自动化调试系统模块（src/auto_debug/）
  - 平台错误分析器（PlatformErrorAnalyzer）
    - 支持MCP工具、工作流引擎、认证、知识库、前端UI错误识别
    - 上下文感知分析
    - 智能根因定位
  - 修复策略管理器（PlatformFixStrategyManager）
    - MCP工具修复策略（重试、参数验证、备用工具切换）
    - 工作流引擎修复策略（状态恢复、节点重试、依赖检测、版本回滚）
    - 知识库修复策略（索引重建、文档重解析、搜索优化、缓存清理）
    - 前端UI修复策略（API重试、状态同步、错误边界、本地存储清理）
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
  - 决策信息展示
  - 决策建议生成
  - 快速审批流程
  - 决策效果追踪
- 添加配置文件：
  - config/platform_integration.yaml - 平台集成配置
  - config/debug_workflows.yaml - 调试工作流配置
  - config/decision_rules.yaml - 决策规则配置

### 变更
- 更新README.md，添加auto_debug模块和最新功能说明
- 更新项目结构文档，反映最新目录结构（包括auto_debug模块）
- 更新系统架构文档，添加自动化调试系统架构说明
- 优化文档索引，添加新文档链接

### 文档
- 添加自动化调试系统完整文档（docs/development-docs/auto-debug-system.md）
- 添加快速开始指南（docs/development-docs/QUICK_START.md）
- 添加项目迭代指南（docs/development-docs/ITERATION_GUIDE.md）
- 添加变更日志指南（docs/development-docs/CHANGELOG_GUIDE.md）
- 更新API文档，添加自动化调试系统API说明

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
- MCP工具网关服务（mcp-gateway）
- 工作流引擎服务（workflow-engine）
- Web UI前端界面（web-ui）
- 共享库（shared-libs）
