# 持续测试系统

## 🎯 目标

持续进行测试，不停止，直到所有21个服务测试通过。

## 📋 系统功能

### 主脚本: `scripts/cicd/continuous-test-until-pass.py`

**特点：**
- ✅ **持续运行** - 无限制迭代（最多999次）
- ✅ **自动检测** - 检查所有作业状态
- ✅ **自动修复** - 发现错误自动修复
- ✅ **自动提交** - 修复后自动提交并推送
- ✅ **智能停止** - 连续2次所有测试通过才停止

### 完整流程

1. **启动工作流** - 自动触发GitHub Actions
2. **获取运行ID** - 获取最新运行的ID
3. **等待完成** - 等待工作流执行（最多1小时）
4. **检查状态** - 检查所有作业的状态
5. **分析结果** - 统计成功/失败/跳过的作业数
6. **自动修复** - 如果失败，自动修复错误
7. **提交推送** - 修复后自动提交
8. **循环** - 继续下一轮直到所有测试通过

### 21个服务列表

1. api-gateway
2. auth-service
3. knowledge-base
4. metadata-service
5. workflow-engine
6. web-ui
7. registry-service
8. config-center
9. sap-mcp-server
10. mcp-gateway
11. chat-service
12. dag-orchestrator
13. agent-service
14. agent-orchestrator
15. agent-registry
16. joyagent-adapter
17. memory-service
18. sap-metadata-agent
19. vector-coordinator-service

### 运行方式

```powershell
# 启动持续测试（后台运行）
python scripts\cicd\continuous-test-until-pass.py

# 或者前台运行（可以看到实时输出）
python scripts\cicd\continuous-test-until-pass.py
```

### 停止条件

系统会在以下情况停止：
1. ✅ **所有作业成功** - 连续2次所有测试通过
2. ⚠️ **达到最大迭代** - 达到999次迭代（几乎不可能）
3. 🛑 **用户中断** - 按 Ctrl+C 手动停止

### 输出示例

```
============================================================
迭代 1 / 999
时间: 2025-12-03 19:30:00
============================================================

[19:30:00] 启动工作流...
✅ 工作流已启动
运行ID: 19905975821
等待运行完成... (最多3600秒)
  状态: in_progress (已等待 0s)
  状态: completed

============================================================
作业状态检查 (共 4 个作业)
============================================================
✅ Run Tests
✅ Frontend Tests
✅ Build Docker Images
✅ Deploy to staging
============================================================
成功: 4 | 失败: 0 | 跳过: 0 | 进行中: 0
============================================================

✅ 所有测试通过！ (连续成功: 1)
```

### 日志位置

- 本地日志: `%TEMP%\github-errors\run-{runId}\`
- GitHub运行: https://github.com/PMLiuyubin/enterprise-ai-platform/actions

### 监控方式

```powershell
# 查看最新运行状态
gh run list --workflow=deploy.yml --limit 1

# 查看特定运行
gh run view {runId}

# 查看运行日志
gh run view {runId} --log
```

## 🔧 自动修复功能

系统会自动修复以下类型的错误：

1. **User接口字段缺失** - 自动添加`display_name`、`permissions`、`created_at`等
2. **缺失导入** - 自动添加lucide-react图标导入
3. **JSX语法错误** - 修复缺失的闭合标签
4. **类型不匹配** - 修复常见的类型错误

## 📊 当前状态

- ✅ 脚本已创建并启动
- ✅ 系统正在后台持续运行
- ✅ 自动检测和修复已启用
- ✅ 日志记录已配置

## ⚠️ 注意事项

1. **不要手动停止** - 除非确定所有测试已通过
2. **检查日志** - 如果长时间失败，检查日志目录
3. **网络连接** - 确保网络连接稳定
4. **GitHub Token** - 确保GitHub CLI已正确配置

## 🎉 完成标志

当看到以下消息时，表示所有测试已通过：

```
============================================================
🎉 所有服务测试通过！系统停止。
============================================================
总迭代次数: X
成功作业数: Y
```





