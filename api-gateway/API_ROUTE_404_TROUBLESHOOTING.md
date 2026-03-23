# API 路由 404 错误排查指南

## 问题描述

删除文档时出现 404 错误：
- `DELETE http://localhost:3000/api/knowledge/documents/{id} 404 (Not Found)`

## 可能的原因

### 1. Next.js 路由缓存问题（最可能）

Next.js 开发服务器可能没有识别到新的路由文件。

**解决方案**：
```bash
# 停止开发服务器（Ctrl+C）
# 清除 Next.js 缓存
cd web-ui
rm -rf .next

# 重新启动开发服务器
npm run dev
```

### 2. 路由文件路径问题

确保文件路径正确：
```
web-ui/src/app/api/knowledge/documents/[id]/route.ts
```

**检查**：
- 文件是否存在
- 文件名是否正确（`route.ts`，不是 `routes.ts`）
- 目录结构是否正确

### 3. 路由参数解析问题

在 Next.js 14+ 中，动态路由参数可能需要特殊处理。

**已修复**：已更新代码以兼容 Next.js 14 和 15。

### 4. 后端服务未运行

如果后端服务未运行，Next.js API 路由可能无法正确代理请求。

**检查**：
```bash
# 检查知识库服务
curl http://localhost:8004/api/health

# 检查 API Gateway（如果使用）
curl http://localhost:8080/health
```

## 快速修复步骤

### 步骤 1: 重启开发服务器

```bash
# 停止当前开发服务器（Ctrl+C）
cd web-ui
npm run dev
```

### 步骤 2: 清除缓存

```bash
cd web-ui
# Windows
rmdir /s /q .next
# 或手动删除 .next 文件夹

# 重新启动
npm run dev
```

### 步骤 3: 检查路由文件

确认以下文件存在：
- `web-ui/src/app/api/knowledge/documents/[id]/route.ts`
- 文件包含 `export async function DELETE` 函数

### 步骤 4: 测试路由

在浏览器中直接访问（应该返回 400，因为缺少参数）：
```
http://localhost:3000/api/knowledge/documents/test-id
```

或者使用 curl：
```bash
curl -X DELETE http://localhost:3000/api/knowledge/documents/test-id
```

## 已修复的问题

### 1. 路由参数兼容性

已更新代码以兼容 Next.js 14 和 15：
```typescript
// 兼容 Next.js 14 和 15
const params = context.params instanceof Promise ? await context.params : context.params
```

### 2. 错误处理改进

- 添加了详细的日志
- 改进了错误消息
- 添加了调试信息

## 验证修复

### 1. 检查控制台日志

删除文档时，应该看到：
```
[Delete Document API] Request URL: http://localhost:8080/api/knowledge/documents/{id}
[Delete Document API] Document ID: {id}
[Delete Document API] API Gateway URL: http://localhost:8080
[Delete Document API] Knowledge Base URL: http://localhost:8004
```

### 2. 检查网络请求

在浏览器开发者工具的 Network 标签中：
- 查看请求 URL 是否正确
- 查看响应状态码
- 查看响应内容

### 3. 直接测试后端

```bash
# 测试后端删除接口
curl -X DELETE http://localhost:8004/api/documents/{document_id}

# 或通过 API Gateway
curl -X DELETE http://localhost:8080/api/knowledge/documents/{document_id}
```

## 如果问题仍然存在

1. **检查 Next.js 版本**：
   ```bash
   cd web-ui
   npm list next
   ```

2. **检查文件权限**：
   - 确保文件可读
   - 确保目录结构正确

3. **查看 Next.js 日志**：
   - 检查开发服务器控制台输出
   - 查找路由注册信息

4. **尝试硬刷新**：
   - 浏览器：Ctrl+Shift+R 或 Cmd+Shift+R
   - 清除浏览器缓存

5. **检查环境变量**：
   - 确保 `API_GATEWAY_URL` 或 `KNOWLEDGE_BASE_URL` 正确设置

## 常见错误

### 错误 1: "Route not found"

**原因**：路由文件不存在或路径错误

**解决**：检查文件路径和文件名

### 错误 2: "Cannot read property 'id' of undefined"

**原因**：路由参数解析问题

**解决**：已修复，使用兼容的参数解析方式

### 错误 3: "404 from backend"

**原因**：后端服务未运行或路由配置错误

**解决**：
1. 检查后端服务是否运行
2. 检查 API Gateway 路由配置
3. 检查后端路由是否正确注册

## 下一步

如果重启开发服务器后问题仍然存在，请：
1. 检查后端服务日志
2. 查看 Next.js 开发服务器日志
3. 检查浏览器控制台的完整错误信息
4. 尝试直接访问后端 API 确认服务正常


