# 重新配置 Runner 指南

## 问题
Runner 标签在 GitHub 上显示正确，但无法接收任务。

## 解决方案
重新配置 Runner 并明确指定标签。

## 步骤

### 1. 获取新的配置 Token

1. 访问 Runner 设置页面：
   ```
   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners
   ```

2. **选项 A：删除并重新添加 Runner（推荐）**
   - 点击 Runner "server-production" 右侧的 "..." 菜单
   - 选择 "Remove runner"
   - 确认删除
   - 点击 "New runner" 按钮
   - 选择 "Linux" 和 "x64"
   - 复制显示的 Token（格式类似：`AXXXXXXXXXXXXXXXXXXXXX`）

3. **选项 B：获取现有 Runner 的配置 Token**
   - 点击 Runner "server-production" 右侧的 "..." 菜单
   - 选择 "Configure" 或 "Edit"
   - 查看是否有重新配置的选项
   - 如果没有，使用选项 A

### 2. 运行修复脚本

在本地 PowerShell 中运行：

```powershell
# 步骤 1: 清理旧配置
.\fix-runner-labels.ps1

# 步骤 2: 使用新 Token 重新配置（明确指定标签）
.\configure-runner-with-labels.ps1 YOUR_TOKEN_HERE
```

### 3. 验证配置

1. 检查 Runner 状态：
   ```
   https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners
   ```
   应该看到：
   - Runner 名称：server-production
   - 状态：Online（绿色）
   - 标签：self-hosted, Linux, X64

2. 测试工作流：
   - 访问 Actions 页面
   - 手动触发 "🚀 自托管 Runner 自动部署" 工作流
   - 应该能够接收任务并开始执行

## 注意事项

- 重新配置会删除旧的 Runner 配置
- 需要新的 Token 才能重新配置
- 配置完成后，Runner 会自动重新连接
- 确保服务器上的 Runner 文件没有被删除（在 `/opt/actions-runner`）

## 故障排查

如果重新配置后仍然无法接收任务：

1. 检查 Runner 服务状态：
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
   cd /opt/actions-runner
   sudo ./svc.sh status
   ```

2. 检查 Runner 日志：
   ```bash
   sudo journalctl -u actions.runner.* -f
   ```

3. 检查诊断日志：
   ```bash
   tail -50 /opt/actions-runner/_diag/Runner_*.log
   ```

4. 重启 Runner 服务：
   ```bash
   cd /opt/actions-runner
   sudo ./svc.sh restart
   ```


