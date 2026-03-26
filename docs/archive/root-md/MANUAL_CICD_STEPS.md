# 手动完成CI/CD改进和启动步骤

## 问题说明
终端命令被交互式工具拦截，需要手动执行以下命令。

## 步骤1: 提交改进的工作流文件

在PowerShell中**直接执行**以下命令（不要通过任何工具）：

```powershell
# 1. 添加文件
git add .github/workflows/test-suite.yml
git add .github/workflows/deploy.yml

# 2. 提交
git commit -m "feat: 改进CI/CD - 添加智能测试选择和蓝绿部署"

# 3. 推送
git push origin main
```

## 步骤2: 启动CI/CD工作流

```powershell
# 启动部署工作流（staging环境）
gh workflow run deploy.yml --field environment=staging

# 查看运行状态
gh run list --workflow="deploy.yml" --limit 5

# 实时查看日志
gh run watch
```

## 如果git命令也卡住

如果git命令也出现 `[Use arrows to move, type to filter]`，尝试：

```powershell
# 方法1: 设置环境变量禁用交互
$env:GIT_PAGER = ""
$env:PAGER = ""
git add .github/workflows/test-suite.yml
git add .github/workflows/deploy.yml
git commit -m "feat: 改进CI/CD"
git push origin main

# 方法2: 使用--no-pager
git --no-pager add .github/workflows/test-suite.yml
git --no-pager add .github/workflows/deploy.yml
git --no-pager commit -m "feat: 改进CI/CD"
git --no-pager push origin main
```

## 改进内容总结

### 1. 智能测试选择 ✅
- 添加了 `detect-changes` job，自动检测文件变更
- 根据变更类型（Python/前端/配置/测试）智能选择要运行的测试
- 减少不必要的测试执行，提高CI/CD效率

### 2. 蓝绿部署 ✅
- 在 `deploy.yml` 中集成了蓝绿部署逻辑
- 先启动新版本，验证健康后再切换
- 如果新版本失败，自动回滚到旧版本

## 验证改进

提交后，可以通过以下方式验证：

1. **查看工作流文件**：
   - `.github/workflows/test-suite.yml` - 应该包含 `detect-changes` job
   - `.github/workflows/deploy.yml` - 应该包含蓝绿部署逻辑

2. **触发工作流**：
   - 创建PR时会自动运行智能测试选择
   - 手动触发部署会使用蓝绿部署

---

**提示**: 如果所有命令都卡住，可能是终端配置问题，建议：
1. 关闭当前终端，打开新的PowerShell窗口
2. 或者使用Git Bash执行git命令
3. 或者直接在GitHub Web界面手动编辑和提交文件





