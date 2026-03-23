# CI/CD 工作流状态查看命令

## ✅ 工作流已启动

你的CI/CD工作流已经成功启动！由于终端交互问题，使用以下**非交互式**命令查看状态：

## 方法1: 查看运行列表（推荐）

```powershell
# 查看最近的5个运行
gh run list --workflow="deploy.yml" --limit 5

# 查看所有运行
gh run list --workflow="deploy.yml"
```

## 方法2: 查看特定运行的详细信息

```powershell
# 先获取运行ID（从上面的列表中）
# 然后查看详细信息
gh run view <run-id>

# 查看日志
gh run view <run-id> --log

# 在浏览器中打开
gh run view <run-id> --web
```

## 方法3: 使用Web界面（最简单）

直接访问GitHub Actions页面：
```
https://github.com/PMLiuyubin/enterprise-ai-platform/actions
```

然后点击 `Deploy to Server` 工作流，查看最新的运行。

## 方法4: 使用脚本

运行我创建的脚本：
```powershell
powershell -ExecutionPolicy Bypass -File check-cicd-status.ps1
```

## 实时监控

如果想实时查看日志（避免交互选择），可以：

```powershell
# 获取最新的运行ID
$runId = gh run list --workflow="deploy.yml" --limit 1 --json databaseId --jq '.[0].databaseId'

# 查看该运行的日志
gh run watch $runId
```

## 工作流状态说明

- **queued** - 排队中
- **in_progress** - 运行中
- **completed** - 已完成
  - **success** - 成功
  - **failure** - 失败
  - **cancelled** - 已取消

## 当前改进功能

本次部署包含以下改进：

1. ✅ **智能测试选择**
   - 自动检测文件变更
   - 只运行相关的测试

2. ✅ **蓝绿部署**
   - 零停机部署
   - 自动健康检查
   - 失败自动回滚

---

**提示**: 如果命令仍然卡住，直接使用GitHub Web界面查看是最可靠的方式。





