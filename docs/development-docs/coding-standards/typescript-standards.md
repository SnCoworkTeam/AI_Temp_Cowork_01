# TypeScript编码规范

## 代码风格

### 格式化工具
- **Prettier**: 代码格式化
- **ESLint**: 代码检查

### 配置

```bash
# 格式化代码
npm run format

# 检查代码
npm run lint
```

## 命名规范

### 变量和函数
- 使用驼峰命名: `userName`, `getUserInfo()`
- 布尔值使用is/has前缀: `isActive`, `hasPermission`

### 类
- 使用大驼峰命名: `UserService`, `WorkflowRepository`

### 常量
- 使用大写字母和下划线: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`

## 类型定义

所有函数都应该有类型注解：

```typescript
function getUser(userId: string): User | null {
  // ...
}
```

## 组件文档

使用JSDoc注释：

```typescript
/**
 * 用户信息组件
 * 
 * @param userId - 用户ID
 * @returns 用户信息或null
 */
function getUserInfo(userId: string): User | null {
  // ...
}
```









