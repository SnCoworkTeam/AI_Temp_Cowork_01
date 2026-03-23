# Web UI Testing Guide

## 测试基础设施

本项目使用以下测试工具栈：
- **Vitest** - 测试运行器
- **@testing-library/react** - React组件测试工具
- **@testing-library/jest-dom** - DOM断言库
- **happy-dom** - 轻量级DOM环境

## 运行测试

```bash
# 运行所有测试
npm test

# 监听模式
npm run test:watch

# 查看UI界面
npm run test:ui

# 生成覆盖率报告
npm run test:coverage
```

## 测试文件结构

```
src/
├── lib/
│   ├── __tests__/
│   │   ├── auth.test.ts          # auth.ts的测试 (13个测试)
│   │   └── utils.test.ts         # utils.ts的测试 (16个测试)
│   ├── api/
│   │   └── __tests__/
│   │       ├── auth.test.ts      # auth API测试 (22个测试) ⭐ 新增
│   │       └── client.test.ts    # API客户端测试 (11个测试)
│   └── auth.ts
├── components/
│   ├── __tests__/
│   │   └── AuthGuard.test.tsx    # AuthGuard组件测试 (7个测试)
│   └── AuthGuard.tsx
└── __tests__/
    ├── setup.ts                   # 测试环境配置
    └── test-utils.tsx             # 测试工具函数
```

## 编写测试示例

### 1. 工具函数测试

```typescript
import { describe, it, expect } from 'vitest'
import { yourFunction } from '../yourFile'

describe('yourFunction', () => {
  it('should return expected result', () => {
    const result = yourFunction('input')
    expect(result).toBe('expected output')
  })
})
```

### 2. React组件测试

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/__tests__/test-utils'
import { YourComponent } from '../YourComponent'

describe('YourComponent', () => {
  it('should render correctly', () => {
    render(<YourComponent prop="value" />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })

  it('should handle user interaction', async () => {
    const mockCallback = vi.fn()
    render(<YourComponent onAction={mockCallback} />)

    const button = screen.getByRole('button')
    await userEvent.click(button)

    expect(mockCallback).toHaveBeenCalled()
  })
})
```

### 3. 异步测试

```typescript
import { waitFor } from '@testing-library/react'

it('should handle async operations', async () => {
  render(<AsyncComponent />)

  await waitFor(() => {
    expect(screen.getByText('Loaded')).toBeInTheDocument()
  })
})
```

## Mock示例

### Mock Next.js Router

已在 `setup.ts` 中全局配置，可直接使用：

```typescript
import { useRouter } from 'next/navigation'

const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))
```

### Mock API调用

```typescript
vi.mock('@/lib/api/auth', () => ({
  authClient: {
    login: vi.fn().mockResolvedValue({ token: 'fake-token' }),
    logout: vi.fn().mockResolvedValue(undefined)
  }
}))
```

## 最佳实践

### 1. 测试命名
- 使用描述性的测试名称，说明测试内容和预期结果
- 格式: `should [expected behavior] when [condition]`
- 示例:
  - ✅ `should return null when token is expired`
  - ✅ `should redirect to login when authentication fails`
  - ❌ `test token` (不够清晰)

### 2. 测试隔离
- 每个测试应该独立运行，不依赖其他测试
- 使用 `beforeEach` 设置测试环境
- 使用 `afterEach` 清理测试环境
- 示例:
```typescript
describe('MyComponent', () => {
  beforeEach(() => {
    // 重置mock
    vi.clearAllMocks()
  })

  afterEach(() => {
    // 清理副作用
    vi.restoreAllMocks()
  })
})
```

### 3. Mock外部依赖
- Mock所有外部API调用和第三方库
- 使用vi.mock()进行模块级mock
- 使用vi.fn()创建函数mock
- 示例:
```typescript
// 模块级mock
vi.mock('@/lib/api/auth', () => ({
  authClient: {
    login: vi.fn().mockResolvedValue({ token: 'fake-token' })
  }
}))

// 函数mock
const mockCallback = vi.fn()
```

### 4. 测试用户行为
- 从用户角度测试，而不是实现细节
- 使用Testing Library的用户交互API
- 避免测试内部状态
- 示例:
```typescript
// ✅ 测试用户可见的行为
expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument()
await userEvent.click(screen.getByRole('button'))

// ❌ 测试内部实现
expect(component.state.isLoading).toBe(false)
```

### 5. 异步测试
- 使用waitFor等待异步操作完成
- 使用vi.useFakeTimers()控制时间
- 确保清理定时器
- 示例:
```typescript
// 等待异步更新
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// 使用假定时器
beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})
```

### 6. 边界条件测试
- 测试空值、null、undefined
- 测试边界值 (0, -1, MAX_VALUE)
- 测试错误情况
- 示例:
```typescript
it('should handle empty input', () => {
  expect(fn('')).toBe('')
  expect(fn(null)).toBe('')
  expect(fn(undefined)).toBe('')
})
```

### 7. 测试覆盖率目标
- 核心业务逻辑: 必须100%
- 工具函数: 目标90%+
- 组件: 目标80%+
- 页面: 目标60%+

## 覆盖率目标

- **目标覆盖率**: 80%+
- **优先级**:
  1. 核心业务逻辑 (必须100%)
  2. 工具函数 (目标90%+)
  3. 组件 (目标80%+)
  4. 页面 (目标60%+)

## 当前测试状态

**最后更新**: 2026-02-04 Round 4 (Final) ✅

### 测试统计
- **测试文件**: 9个
- **测试用例**: 145个 ✅
- **通过率**: 100%
- **执行时间**: ~32秒

### 覆盖率统计

#### 核心模块覆盖率
| 模块 | 语句 | 分支 | 函数 | 行数 | 评级 |
|------|------|------|------|------|------|
| **lib/utils.ts** | 100% | 100% | 100% | 100% | ⭐⭐⭐⭐⭐ 完美 |
| **lib/api/chat.ts** | 100% | 100% | 100% | 100% | ⭐⭐⭐⭐⭐ 完美 |
| **lib/auth.ts** | 98.97% | 73.33% | 100% | 98.97% | ⭐⭐⭐⭐⭐ 接近完美 |
| **lib/api/knowledge.ts** | 98.96% | 69.23% | 100% | 98.96% | ⭐⭐⭐⭐⭐ 优秀 |
| **lib/api/auth.ts** | 98.85% | 73.8% | 100% | 98.85% | ⭐⭐⭐⭐⭐ 优秀 |
| **lib/api/client.ts** | 97% | 68.96% | 100% | 97% | ⭐⭐⭐⭐ 优秀 |
| **lib/api/workflow.ts** | 92.77% | 78.84% | 100% | 92.77% | ⭐⭐⭐⭐ 优秀 |
| **components/AuthGuard.tsx** | 86.66% | 75.75% | 100% | 86.66% | ⭐⭐⭐⭐ 良好 |
| **contexts/AuthContext.tsx** | 部分覆盖 | 部分覆盖 | 部分覆盖 | 部分覆盖 | ⭐⭐⭐ 基础 |

**核心API+工具模块平均覆盖率**: 97.11% ⭐⭐⭐⭐⭐

*注: 整体覆盖率较低是因为大部分页面和组件还未添加测试*

### ✅ 已完成测试的模块 (145个测试)

#### 1. 认证与授权 (48个测试)
- **lib/__tests__/auth.test.ts** (34个测试) ⭐ 扩展
  - Token管理功能 (8个)
  - 用户信息处理 (4个)
  - Token刷新逻辑 (5个) ⭐ 新增
  - 登出功能 (3个) ⭐ 新增
  - 角色权限检查 (9个) ⭐ 新增
  - Cookie支持 (3个) ⭐ 新增

- **lib/api/__tests__/auth.test.ts** (22个测试)
  - 用户注册流程 (4个)
  - 用户登录流程 (5个)
  - SSO单点登录 (1个)
  - Token刷新机制 (3个)
  - 用户信息获取 (7个)
  - 用户登出 (2个)

- **components/__tests__/AuthGuard.test.tsx** (7个测试)
  - 认证保护
  - 权限控制
  - 路由重定向
  - 加载状态处理

- **contexts/__tests__/AuthContext.test.tsx** (6个测试) ⭐ 新增
  - useAuth Hook错误处理
  - AuthProvider初始化
  - 缓存用户加载
  - 用户信息更新
  - 加载状态管理

#### 2. 工具函数 (16个测试)
- **lib/__tests__/utils.test.ts** (16个测试)
  - 类名合并函数 (cn) - 7个测试
  - 防抖函数 (debounce) - 5个测试
  - 节流函数 (throttle) - 4个测试

#### 3. API客户端基础 (11个测试)
- **lib/api/__tests__/client.test.ts** (11个测试)
  - HTTP请求方法 (GET/POST/PUT/DELETE)
  - Token自动刷新
  - 错误处理 (401/404/429/500)
  - 请求重试机制
  - 限流处理

#### 4. 工作流API (23个测试) ⭐ 新增
- **lib/api/__tests__/workflow.test.ts** (23个测试)
  - 工作流管理 (列表、信息、保存、详情)
  - 工作流执行 (执行、状态查询)
  - 错误处理 (404友好提示、自动重试)
  - 路径处理 (API Gateway模式、直接访问模式)

#### 5. 知识库API (19个测试) ⭐ 新增
- **lib/api/__tests__/knowledge.test.ts** (19个测试)
  - 语义搜索 (2个)
  - 关键词搜索 (3个)
  - 混合搜索 (2个)
  - 文档管理 (5个)
  - 知识图谱 (4个)
  - 路径处理 (3个)

#### 6. 智能对话API (9个测试) ⭐ 新增
- **lib/api/__tests__/chat.test.ts** (9个测试)
  - 智能对话 (5个)
  - 智能体对话 (4个)

### ⏳ 待测试模块

#### 高优先级
- [x] ~~**contexts/AuthContext.tsx**~~ - 基础测试已完成（6个测试）
- [ ] **hooks/useChat.ts** - 对话Hook
- [x] ~~**lib/auth.ts**~~ - 已达98.97%覆盖率 ✅

#### 中优先级
- [ ] **contexts/AuthContext.tsx** - 提升至80%+覆盖率
- [ ] **lib/api/dag.ts** - DAG编排API
- [ ] **lib/api/monitoring.ts** - 监控API
- [ ] **lib/api/admin.ts** - 管理API
- [ ] **components/ErrorBoundary.tsx** - 错误边界
- [ ] **components/MessageList.tsx** - 消息列表
- [ ] **components/ErrorBoundary.tsx** - 错误边界
- [ ] **components/MessageList.tsx** - 消息列表

#### 低优先级
- [ ] 页面组件测试
- [ ] 复杂业务组件测试
- [ ] E2E测试

## 常见问题

### Q: 测试中如何处理localStorage?

A: 每个测试前会自动清理localStorage，直接使用即可。

### Q: 如何测试需要认证的组件?

A: Mock `useAuth` hook，返回需要的认证状态。

### Q: 如何运行单个测试文件?

A: `npm test -- auth.test.ts`

## 参考资源

- [Vitest文档](https://vitest.dev/)
- [Testing Library文档](https://testing-library.com/)
- [React Testing最佳实践](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
