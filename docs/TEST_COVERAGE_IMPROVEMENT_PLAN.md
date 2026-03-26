# 测试覆盖率提升计划

## 目标
将所有服务的测试覆盖率提升到 **80%** 以上

## 当前状态分析

### 1. auth-service
**需要测试的模块：**
- `routes/auth_enhanced.py` - 增强认证路由（部分覆盖）
- `routes/admin/*` - 管理后台路由（未覆盖）
- `routes/monitoring.py` - 监控路由（未覆盖）
- `services/permission_service.py` - 权限服务（部分覆盖）
- `services/role_service.py` - 角色服务（部分覆盖）
- `repositories/*` - 仓库层（部分覆盖）
- `middleware/*` - 中间件（未覆盖）
- `sso/*` - SSO相关（部分覆盖）

**优先级：高**

### 2. knowledge-base
**需要测试的模块：**
- `core/*` - 核心组件（部分覆盖）
- `repositories/*` - 仓库层（部分覆盖）
- `services/*` - 服务层（部分覆盖）
- `routes/*` - 路由层（部分覆盖）

**优先级：高**

### 3. metadata-service
**需要测试的模块：**
- `collectors/*` - 收集器（部分覆盖）
- `services/*` - 服务层（部分覆盖）
- `api/*` - API路由（部分覆盖）

**优先级：中**

### 4. workflow-engine
**需要测试的模块：**
- `core/nodes/*` - 节点实现（部分覆盖）
- `core/dynamic_workflow_engine.py` - 动态工作流引擎（部分覆盖）
- `repositories/*` - 仓库层（部分覆盖）
- `routes/*` - 路由层（部分覆盖）

**优先级：中**

### 5. mcp-gateway
**需要测试的模块：**
- `core/*` - 核心组件（部分覆盖）
- `tools/*` - 工具实现（部分覆盖）
- `services/*` - 服务层（部分覆盖）
- `routes/*` - 路由层（部分覆盖）

**优先级：中**

### 6. database
**需要测试的模块：**
- `repositories/*` - 仓库层（部分覆盖）
- `core/*` - 核心组件（部分覆盖）

**优先级：低**

## 实施计划

### 阶段1: auth-service (优先级最高)
1. 为 `routes/auth_enhanced.py` 添加完整测试
2. 为 `routes/admin/*` 添加测试
3. 为 `middleware/*` 添加测试
4. 为 `repositories/*` 添加完整测试
5. 为 `services/*` 添加完整测试

### 阶段2: knowledge-base
1. 为 `core/*` 组件添加测试
2. 为 `repositories/*` 添加测试
3. 为 `services/*` 添加测试
4. 为 `routes/*` 添加测试

### 阶段3: 其他服务
1. metadata-service
2. workflow-engine
3. mcp-gateway
4. database

## 测试编写规范

1. **单元测试**：测试单个函数/方法的功能
2. **集成测试**：测试模块间的交互
3. **Mock使用**：对外部依赖使用mock
4. **覆盖率目标**：每个模块至少80%覆盖率

## 进度跟踪

- [ ] auth-service 达到80%覆盖率
- [ ] knowledge-base 达到80%覆盖率
- [ ] metadata-service 达到80%覆盖率
- [ ] workflow-engine 达到80%覆盖率
- [ ] mcp-gateway 达到80%覆盖率
- [ ] database 达到80%覆盖率

