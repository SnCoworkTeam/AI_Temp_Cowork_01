# 前端认证系统

前端登录页面和管理后台，集成SSO单点登录认证。

## 功能特性

### 认证功能
- ✅ **用户名密码登录**：支持用户名或邮箱登录
- ✅ **用户注册**：新用户注册功能
- ✅ **SSO单点登录集成**：企业SSO登录
- ✅ **自动令牌刷新机制**：自动刷新访问令牌
- ✅ **路由守卫保护**：保护需要认证的页面
- ✅ **用户状态管理**：React Context全局状态管理
- ✅ **Cookie和localStorage双重存储**：安全的令牌存储
- ✅ **密码修改**：用户可修改密码
- ✅ **会话管理**：查看和管理活跃会话

### 管理后台
- 📊 数据概览仪表板
- 👥 用户管理页面
- 🔄 工作流管理页面
- 🔧 MCP工具管理页面
- 📱 响应式设计，支持移动端

## 页面结构

### 登录相关
- `/login` - 登录首页（支持用户名密码登录、注册和SSO登录）
- `/auth/callback` - SSO回调处理页面
- `/unauthorized` - 未授权访问页面

### 管理后台
- `/admin/dashboard` - 数据概览仪表板
- `/admin/users` - 用户管理
- `/admin/workflows` - 工作流管理
- `/admin/tools` - MCP工具管理

## 核心组件

### 1. AuthContext (`src/contexts/AuthContext.tsx`)
- 全局用户状态管理
- 自动令牌刷新（每10分钟检查）
- 用户信息加载和缓存

### 2. AuthGuard (`src/components/AuthGuard.tsx`)
- 路由守卫组件
- 支持角色权限检查
- 自动重定向到登录页

### 3. LoginForm (`src/components/LoginForm.tsx`)
- 用户名密码登录表单
- 用户注册表单
- SSO登录表单
- 响应式设计
- 表单验证和错误处理

### 4. 认证工具函数 (`src/lib/auth.ts`)
- 令牌管理（获取、设置、清除）
- 用户信息管理
- 角色权限检查

## 使用示例

### 保护路由
```tsx
import { AuthGuard } from '@/components/AuthGuard'

export default function ProtectedPage() {
  return (
    <AuthGuard requireAuth requireRoles={['admin']}>
      <div>管理员内容</div>
    </AuthGuard>
  )
}
```

### 使用认证状态
```tsx
'use client'

import { useAuth } from '@/contexts/AuthContext'

export default function MyComponent() {
  const { user, loading, logout } = useAuth()

  if (loading) return <div>加载中...</div>

  return (
    <div>
      <p>欢迎，{user?.username}</p>
      <button onClick={logout}>登出</button>
    </div>
  )
}
```

### 检查角色权限
```tsx
import { useAuth } from '@/contexts/AuthContext'
import { hasRole } from '@/lib/auth'

export default function AdminPanel() {
  const { user } = useAuth()

  if (!hasRole(user, 'admin')) {
    return <div>需要管理员权限</div>
  }

  return <div>管理员面板</div>
}
```

## 认证流程

### 用户名密码登录流程
1. 用户访问 `/login`
2. 选择"登录"标签页
3. 输入用户名（或邮箱）和密码
4. 点击"登录"按钮
5. 前端调用 `POST /api/auth/login` API
6. 后端验证凭据，返回JWT令牌
7. 前端保存令牌并跳转到管理后台

### 用户注册流程
1. 用户访问 `/login`
2. 选择"注册"标签页
3. 填写用户名、邮箱、密码等信息
4. 点击"注册"按钮
5. 前端调用 `POST /api/auth/register` API
6. 后端创建用户账户
7. 注册成功后自动登录

### SSO登录流程
1. 用户访问 `/login`
2. 点击"使用SSO登录"按钮
3. 重定向到SSO提供者授权页面
4. 用户授权后回调到 `/auth/callback`
5. 后端处理回调，设置Cookie
6. 前端获取用户信息并跳转到管理后台

### 自动令牌刷新
- 每10分钟自动检查令牌状态
- 如果令牌即将过期，自动刷新
- 刷新失败时自动登出

### 路由守卫
- 未登录用户访问受保护页面时重定向到 `/login`
- 权限不足时重定向到 `/unauthorized`
- 支持角色和权限检查

## 环境变量

在 `.env.local` 中配置：

```bash
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8003
NEXT_PUBLIC_MCP_GATEWAY_URL=http://localhost:8001
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=http://localhost:8002
```

## 响应式设计

所有页面都支持响应式设计：
- 移动端：侧边栏自动隐藏，通过汉堡菜单打开
- 平板：两列布局
- 桌面：三列布局，完整侧边栏

## 安全注意事项

1. **Cookie安全**：生产环境必须使用HTTPS
2. **令牌存储**：优先使用HTTP-only Cookie
3. **XSS防护**：避免在localStorage存储敏感信息
4. **CSRF防护**：使用状态参数验证

## 开发

### 本地运行
```bash
cd web-ui
npm install
npm run dev
```

### 访问页面
- 登录页：http://localhost:3000/login
- 管理后台：http://localhost:3000/admin/dashboard

## 注意事项

1. 确保认证服务（auth-service）正在运行
2. 配置正确的SSO提供者信息
3. 确保Cookie可以正常设置（同域或正确的CORS配置）








