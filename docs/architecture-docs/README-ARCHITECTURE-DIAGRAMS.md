# LuminaOS 系统架构图说明

本文档包含使用PlantUML生成的系统架构图，全面展示LuminaOS企业AI平台的架构设计。

## 架构图文件

### 1. system-architecture.puml
**系统整体架构图**

展示系统的分层架构和主要组件：
- 前端层：Web UI
- 核心架构层：API Gateway、Registry Service、Config Center
- 业务服务层：AI核心服务、数据与知识服务、集成与工具服务、基础服务
- 基础设施层：PostgreSQL、Redis、Qdrant、Neo4j

**生成命令：**
```bash
plantuml docs/architecture-docs/system-architecture.puml -o ../../docs/images/
```

### 2. system-architecture-detailed.puml
**详细系统架构图**

包含更详细的组件内部结构和数据流：
- 各服务的内部模块
- 详细的服务间依赖关系
- 数据流向
- 外部系统集成

**生成命令：**
```bash
plantuml docs/architecture-docs/system-architecture-detailed.puml -o ../../docs/images/
```

### 3. system-architecture-deployment.puml
**部署架构图**

展示Docker容器化部署架构：
- Docker网络配置
- 容器部署结构
- 服务间网络通信
- 数据持久化配置

**生成命令：**
```bash
plantuml docs/architecture-docs/system-architecture-deployment.puml -o ../../docs/images/
```

### 4. system-architecture-dataflow.puml
**数据流图**

展示典型用户请求的数据流：
- 用户请求流程
- 智能体处理流程
- 数据查询流程
- 缓存流程
- 响应流程

**生成命令：**
```bash
plantuml docs/architecture-docs/system-architecture-dataflow.puml -o ../../docs/images/
```

## 如何生成图片

### 方法1：使用PlantUML命令行工具

1. 安装PlantUML：
   ```bash
   # Windows (使用Chocolatey)
   choco install plantuml
   
   # macOS (使用Homebrew)
   brew install plantuml
   
   # Linux
   sudo apt-get install plantuml
   ```

2. 生成图片：
   ```bash
   plantuml docs/architecture-docs/*.puml -o docs/images/architecture/
   ```

### 方法2：使用在线工具

1. 访问 [PlantUML在线编辑器](http://www.plantuml.com/plantuml/uml/)
2. 复制`.puml`文件内容
3. 粘贴到编辑器中
4. 点击生成图片
5. 下载PNG或SVG格式

### 方法3：使用VS Code插件

1. 安装PlantUML插件（如"PlantUML"）
2. 打开`.puml`文件
3. 使用快捷键（通常是`Alt+D`）预览
4. 导出为图片

## 架构图说明

### 系统分层

1. **前端层**
   - Web UI (Next.js 14)
   - 提供用户交互界面

2. **核心架构层**
   - API Gateway：统一入口，路由转发
   - Registry Service：服务注册与发现
   - Config Center：配置管理

3. **业务服务层**
   - **AI核心服务**：智能体、工作流、编排
   - **数据与知识服务**：知识库、元数据、记忆
   - **集成与工具服务**：MCP网关、SAP集成
   - **基础服务**：认证、对话

4. **基础设施层**
   - PostgreSQL：主数据库
   - Redis：缓存服务
   - Qdrant：向量数据库
   - Neo4j：图数据库

### 关键特性

- **微服务架构**：服务独立部署、独立扩展
- **服务发现**：动态服务注册与发现
- **统一网关**：单一入口，统一路由
- **智能路由**：基于内容自动路由
- **流式处理**：支持SSE实时响应
- **数据持久化**：多数据库支持

## 更新架构图

当系统架构发生变化时，请更新相应的`.puml`文件：

1. 修改`.puml`文件
2. 重新生成图片
3. 更新本文档（如有需要）
4. 提交到Git仓库

## 相关文档

- [系统架构概览](../architecture-docs/system-overview/system-architecture.md)
- [统一平台架构分析](../architecture-docs/UNIFIED_PLATFORM_ARCHITECTURE_ANALYSIS.md)
- [综合架构分析](../architecture-docs/COMPREHENSIVE_ARCHITECTURE_ANALYSIS.md)




