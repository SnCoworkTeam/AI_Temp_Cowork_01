# 核心服务优先测试系统

## 🎯 测试策略

### 优先级顺序

1. **核心服务优先** - 先测试最重要的服务
2. **逐个测试** - 一个服务一个服务地测试
3. **自动修复** - 发现错误自动修复

### 核心服务列表

1. **web-ui** - 前端界面（最重要）
2. **api-gateway** - API网关
3. **auth-service** - 认证服务
4. **workflow-engine** - 工作流引擎

### 其他服务（按顺序测试）

- knowledge-base
- metadata-service
- registry-service
- config-center
- mcp-gateway
- chat-service
- dag-orchestrator
- agent-service
- agent-orchestrator
- agent-registry
- memory-service
- sap-metadata-agent
- vector-coordinator-service
- sap-mcp-server
- joyagent-adapter

## 📋 系统功能

### 主脚本: `scripts/cicd/test-core-services-first.py`

**特点：**
- ✅ **核心服务优先** - 先测试web-ui、api-gateway等核心服务
- ✅ **使用Job ID** - 使用job ID而不是job name下载日志（解决404问题）
- ✅ **优先处理Frontend** - 优先分析和修复Frontend Tests错误
- ✅ **自动修复** - 发现错误自动修复并提交
- ✅ **逐个测试** - 一个服务一个服务地测试

## 🔧 改进点

### 1. 日志下载修复
- **问题**: 使用job name下载日志时出现404错误
- **解决**: 使用job ID (`databaseId`) 下载日志
- **备用**: 如果ID失败，回退到使用job name

### 2. 错误分析优化
- **优先**: 优先分析Frontend Tests错误
- **详细**: 显示错误文件、行号和消息
- **限制**: 只显示前5个错误，避免输出过多

### 3. 测试流程
1. 启动工作流
2. 等待完成
3. 检查作业状态（重点关注Frontend Tests）
4. 如果Frontend Tests失败，下载日志并分析
5. 自动修复错误
6. 验证修复
7. 提交并推送
8. 继续下一轮

## 🚀 使用方法

```powershell
# 运行核心服务测试
python scripts\cicd\test-core-services-first.py
```

## 📊 当前状态

- ✅ 新脚本已创建
- ✅ 旧脚本已停止
- ✅ 新脚本正在运行
- ✅ 优先测试核心服务

## 🎯 测试目标

1. **第一阶段**: 核心服务全部通过（web-ui, api-gateway, auth-service, workflow-engine）
2. **第二阶段**: 其他服务按顺序测试
3. **最终目标**: 所有服务测试通过

## 🔍 检查状态

```powershell
# 检查Python进程
Get-Process python

# 检查最新运行
gh run list --workflow=deploy.yml --limit 1

# 查看运行详情
gh run view {runId}
```

## 📝 日志位置

- **本地日志**: `%TEMP%\github-errors\run-{runId}\`
- **GitHub运行**: https://github.com/PMLiuyubin/enterprise-ai-platform/actions

## ⚠️ 注意事项

1. **优先处理Frontend** - 系统会优先分析和修复Frontend Tests错误
2. **使用Job ID** - 解决了日志下载404问题
3. **逐个测试** - 一个服务一个服务地测试，更稳定
4. **自动修复** - 发现错误自动修复并提交

---

**系统正在优先测试核心服务...** 🚀





