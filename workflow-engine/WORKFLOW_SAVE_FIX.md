# 工作流保存问题修复

## 问题描述
前端保存工作流时出现 `405 Method Not Allowed` 错误：
```
POST http://127.0.0.1:8002/api/workflows 405 (Method Not Allowed)
```

## 根本原因
- 前端调用路径：`/api/workflows` (POST)
- 后端实际路由：`/api/v1/workflows` (POST)
- 路径不匹配导致 405 错误

## 修复内容

### 1. 前端修复 (`web-ui/src/lib/api/workflow.ts`)
- 将 `saveWorkflow` 函数的API路径从 `/api/workflows` 更新为 `/api/v1/workflows`

### 2. 后端兼容性修复 (`workflow-engine/src/main.py`)
- 添加向后兼容路由，将 `workflow_designer.router` 也注册到 `/api/workflows`
- 这样前端使用 `/api/workflows` 或 `/api/v1/workflows` 都能正常工作

## 测试步骤
1. 确保工作流服务正在运行（端口 8002）
2. 刷新前端页面
3. 创建工作流并保存
4. 应该能成功保存，不再出现 405 错误

## 注意事项
- 如果工作流服务正在运行，需要重启服务以使后端更改生效
- 前端更改会在热重载后自动生效

