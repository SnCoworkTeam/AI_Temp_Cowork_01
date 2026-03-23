# 路由结构文档

## 路由分组

### 1. 公共路由（无需认证）

- `/` - 首页（自动重定向）
- `/login` - 登录页面
- `/auth/callback` - SSO回调页面
- `/unauthorized` - 未授权页面

### 2. 受保护路由（需要认证）

#### 主应用路由

- `/chat` - AI助手聊天页面
- `/workflow-designer` - 工作流设计器

#### 管理后台路由 (`/admin/*`)

- `/admin/dashboard` - 仪表板
- `/admin/users` - 用户管理
- `/admin/workflows` - 工作流管理
- `/admin/tools` - 工具管理
- `/admin/monitoring` - 系统监控总览
  - `/admin/monitoring/services` - 服务监控
  - `/admin/monitoring/logs` - 日志查看
- `/admin/settings` - 个人设置

### 3. 错误页面

- `/404` (`not-found.tsx`) - 404页面
- `/error` (`error.tsx`) - 应用错误页面
- `/global-error` (`global-error.tsx`) - 全局错误页面

## 布局结构

### 根布局 (`app/layout.tsx`)

- 提供全局样式和认证状态
- 包含顶部导航栏（非管理后台页面）

### 公共路由布局 (`app/(public)/layout.tsx`)

- 用于登录、回调等公共页面

### 管理后台布局 (`app/admin/layout.tsx`)

- 包含侧边栏导航
- 顶部导航栏
- 面包屑导航
- 需要认证

### 聊天页面布局 (`app/chat/layout.tsx`)

- 需要认证
- 全屏聊天界面

### 工作流设计器布局 (`app/workflow-designer/layout.tsx`)

- 需要认证
- 全屏设计器界面

## 导航菜单

### 主菜单（顶部导航栏）

- AI助手 (`/chat`)
- 工作流设计器 (`/workflow-designer`)
- 管理后台 (`/admin/dashboard`)

### 管理菜单（侧边栏）

- 仪表板 (`/admin/dashboard`)
- 管理
  - 用户管理 (`/admin/users`)
  - 工作流管理 (`/admin/workflows`)
  - 工具管理 (`/admin/tools`)
  - 系统监控 (`/admin/monitoring`)
- AI助手 (`/chat`)
- 工作流设计器 (`/workflow-designer`)

### 用户菜单（下拉菜单）

- 个人设置 (`/admin/settings`)
- 退出登录

## 路由保护

使用 `AuthGuard` 组件保护路由：

```tsx
<AuthGuard requireAuth>
  {/* 需要认证的内容 */}
</AuthGuard>

<AuthGuard requireAuth requireRoles={['admin']}>
  {/* 需要特定角色的内容 */}
</AuthGuard>
```

## 面包屑导航

自动根据当前路径生成面包屑导航，显示在管理后台页面的顶部。

## 移动端支持

- 响应式设计
- 汉堡菜单（移动端显示）
- 侧边栏抽屉（移动端）
- 触摸友好的交互
