# Web UI 前端应用

企业AI平台的现代化Web前端界面，基于Next.js 14和TypeScript构建。

## 功能特性

- 🎨 **现代化UI**: 基于TailwindCSS的响应式设计
- 🔄 **工作流设计器**: 可视化工作流设计和编辑
- 💬 **聊天界面**: 与AI助手交互的聊天界面
- 📊 **管理后台**: 系统管理和监控面板
- 🔐 **认证集成**: 与Auth Service集成的SSO登录
- 📱 **响应式设计**: 支持桌面和移动设备

## 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: TailwindCSS
- **状态管理**: React Context / Zustand
- **HTTP客户端**: Fetch API / Axios
- **Node版本**: 20+

## 项目结构

```
web-ui/
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── (auth)/          # 认证相关页面
│   │   ├── (dashboard)/     # 仪表板页面
│   │   ├── admin/           # 管理后台
│   │   └── api/             # API路由
│   ├── components/          # React组件
│   │   ├── WorkflowDesigner/ # 工作流设计器
│   │   ├── Chat/            # 聊天组件
│   │   └── common/          # 通用组件
│   ├── lib/                 # 工具函数
│   │   ├── api/             # API客户端
│   │   └── utils/           # 工具函数
│   └── types/               # TypeScript类型定义
├── public/                  # 静态资源
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

## 环境变量

在 `.env.local` 文件中配置：

```bash
# 后端服务URL（浏览器访问）
NEXT_PUBLIC_MCP_GATEWAY_URL=http://localhost:8001
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=http://localhost:8002
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8003
NEXT_PUBLIC_KNOWLEDGE_BASE_URL=http://localhost:8004
NEXT_PUBLIC_METADATA_SERVICE_URL=http://localhost:8005

# 认证配置
NEXT_PUBLIC_SSO_ENABLED=true
NEXT_PUBLIC_SSO_CLIENT_ID=your_client_id
```

## 开发

### 本地运行

```bash
cd web-ui
npm install
npm run dev
```

服务将在 `http://localhost:3000` 启动

### Docker开发

```bash
# 构建开发镜像
docker build -f Dockerfile.dev -t web-ui:dev .

# 运行容器
docker run -p 3000:3000 -v $(pwd):/app web-ui:dev
```

### Docker Compose

```bash
# 启动服务
docker-compose up web-ui

# 查看日志
docker-compose logs -f web-ui
```

## 主要功能模块

### 1. 工作流设计器

可视化工作流设计工具，支持：
- 拖拽式节点创建
- 节点连接和配置
- 工作流保存和加载
- 实时预览

**组件位置**: `src/components/WorkflowDesigner/`

### 2. 聊天界面

与AI助手交互的聊天界面，支持：
- 实时消息发送和接收
- 消息历史记录
- 文件上传
- 代码高亮

**组件位置**: `src/components/Chat/`

### 3. 管理后台

系统管理和监控面板，包括：
- 用户管理
- 工作流管理
- 系统监控
- 数据库管理

**页面位置**: `src/app/admin/`

### 4. 认证集成

与Auth Service集成的SSO登录：
- OAuth 2.0流程
- JWT令牌管理
- 用户会话管理

**相关文档**: [AUTH_README.md](./AUTH_README.md)

## API集成

前端通过以下API与后端服务通信：

### MCP Gateway

```typescript
// 获取工具列表
GET ${NEXT_PUBLIC_MCP_GATEWAY_URL}/api/tools

// 执行工具
POST ${NEXT_PUBLIC_MCP_GATEWAY_URL}/api/tools/{name}/execute
```

### Workflow Engine

```typescript
// 获取工作流列表
GET ${NEXT_PUBLIC_WORKFLOW_ENGINE_URL}/api/workflows

// 执行工作流
POST ${NEXT_PUBLIC_WORKFLOW_ENGINE_URL}/api/workflows/{id}/execute
```

### Auth Service

```typescript
// SSO登录
GET ${NEXT_PUBLIC_AUTH_SERVICE_URL}/auth/sso/login

// 获取当前用户
GET ${NEXT_PUBLIC_AUTH_SERVICE_URL}/users/me
```

## 构建和部署

### 开发构建

```bash
npm run build
npm run start
```

### 生产构建

```bash
# 构建生产镜像
docker build -f Dockerfile -t web-ui:prod .

# 运行容器
docker run -p 3000:3000 web-ui:prod
```

## 代码规范

- 使用TypeScript进行类型检查
- 遵循ESLint规则
- 使用Prettier格式化代码
- 组件使用函数式组件和Hooks

## 测试

```bash
# 运行测试
npm test

# 运行E2E测试
npm run test:e2e
```

## 依赖

主要依赖项：
- `next@14.x` - Next.js框架
- `react@18.x` - React库
- `typescript@5.x` - TypeScript
- `tailwindcss@3.x` - TailwindCSS
- `@headlessui/react` - UI组件库

## 端口说明

⚠️ **注意**: 默认使用端口 **3000**。确保该端口未被其他服务占用。

## 相关文档

- [项目主文档](../README.md)
- [认证集成文档](./AUTH_README.md)
- [工作流设计器文档](./src/components/WorkflowDesigner/README.md)
- [数据库管理文档](./src/app/admin/database/README.md)

