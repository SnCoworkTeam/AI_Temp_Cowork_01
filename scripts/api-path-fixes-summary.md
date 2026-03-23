# API路径修复总结

## 问题描述

用户报告了以下404错误：
1. `GET /api/workflows/v1/workflows/{id}` - 404 (工作流详情API路径错误)
2. `GET /api/config/llm/models` - 404 (LLM配置API路径错误)
3. `GET /api/config/llm/default` - 404 (LLM默认配置API路径错误)

## 根本原因

### 1. 工作流API路径问题
- **问题**: 前端调用 `/api/workflows/v1/workflows/{id}`，但正确的路径应该是 `/api/workflows/{id}`
- **原因**: `getWorkflowPath` 函数在构建路径时添加了多余的 `/v1/workflows` 前缀
- **API Gateway配置**: `/api/workflows/{path}` -> `/api/v1/workflows/{path}`

### 2. LLM配置API路径问题
- **问题**: FastAPI路由 `/api/config/{key}` 会匹配 `/api/config/llm/models`，导致LLM专用端点无法访问
- **原因**: FastAPI按定义顺序匹配路由，但 `/api/config/{key}` 是通用路由，会匹配所有路径

## 解决方案

### 1. 修复工作流API路径 (`web-ui/src/lib/api/workflow.ts`)

**修改前**:
```typescript
const finalPath = `/v1/workflows${cleanPath}`  // 错误：会导致 /api/workflows/v1/workflows/{id}
```

**修改后**:
```typescript
// 通过API Gateway时，直接返回cleanPath
// API Gateway会将 /api/workflows/{path} 转发到 /api/v1/workflows/{path}
const finalPath = cleanPath  // 正确：/api/workflows/{id} -> /api/v1/workflows/{id}
```

### 2. 修复配置中心路由 (`config-center/src/main.py`)

**修改**: 将 `/api/config/{key}` 改为 `/api/config/{key:path}`，使用路径参数类型，避免匹配 `/api/config/llm/models`

**注意**: 此修改可能导致容器启动失败，需要检查依赖

## 修复状态

### ✅ 已修复
- [x] 工作流详情API路径 (`/api/workflows/{id}`)
- [x] API Gateway路由配置

### ⚠️ 待处理
- [ ] LLM配置API路径 (配置中心容器重启问题)
- [ ] 配置中心路由修复 (需要验证容器启动)

## 测试结果

### 工作流API
```bash
# 测试通过
curl http://localhost:8080/api/workflows/abc62b1c-cda0-461a-a0ad-89851f2aa8cb
# 返回: 完整的工作流数据 ✅
```

### LLM配置API
```bash
# 待测试（配置中心容器需要修复）
curl http://localhost:8080/api/config/llm/models
```

## 建议

1. **前端使用fallback值**: LLM配置API即使失败，前端也有默认值，不影响功能
2. **配置中心修复**: 需要检查容器依赖和路由定义顺序
3. **API Gateway路由**: 已正确配置，无需修改





