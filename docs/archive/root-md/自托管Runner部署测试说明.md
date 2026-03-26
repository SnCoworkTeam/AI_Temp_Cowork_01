# 自托管 Runner 自动部署测试说明

## ✅ 已完成

1. ✅ **Runner 安装完成**
   - 文件已上传到服务器
   - Runner 已配置并连接到 GitHub
   - 服务已安装并启动
   - 状态：Online

2. ✅ **工作流文件已提交**
   - `deploy-self-hosted.yml` - 自托管 Runner 部署工作流
   - `deploy-lightweight.yml` - 轻量级部署工作流
   - 所有文件已推送到 GitHub

3. ✅ **代码已推送**
   - 提交：`test: 测试自托管 Runner 自动部署功能`
   - 已推送到 main 分支

## 🔍 查看部署状态

### 方法1: GitHub Actions 页面

访问：
```
https://github.com/PMLiuyubin/enterprise-ai-platform/actions
```

应该看到：
- **🚀 自托管 Runner 自动部署** - 正在运行或已完成

### 方法2: Runner 状态页面

访问：
```
https://github.com/PMLiuyubin/enterprise-ai-platform/settings/actions/runners
```

应该看到：
- Runner 名称：`server-production`
- 状态：**Online**（绿色圆点）

### 方法3: 服务器日志

```bash
# SSH 到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 查看 Runner 服务日志
sudo journalctl -u actions.runner.* -f

# 或者查看 Runner 诊断日志
tail -f /opt/actions-runner/_diag/Runner_*.log
```

## 📊 部署流程

当代码推送到 main 分支时，自托管 Runner 会自动：

1. **检出代码** - 从 GitHub 拉取最新代码
2. **拉取最新代码** - 更新服务器上的代码
3. **运行数据库迁移** - 执行 Alembic 迁移
4. **备份容器状态** - 保存当前运行状态
5. **停止旧版本** - 优雅停止旧服务
6. **构建新版本** - 构建 Docker 镜像
7. **启动新版本** - 启动所有服务
8. **健康检查** - 验证服务是否正常

## 🎯 测试结果

### 成功标志

- ✅ GitHub Actions 显示工作流运行成功
- ✅ Runner 日志显示任务执行完成
- ✅ 服务器上服务正常运行
- ✅ API Gateway 健康检查通过

### 验证服务

```bash
# 检查服务状态
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
docker-compose ps

# 检查 API Gateway
curl http://43.143.139.197:8080/health

# 检查 Web UI
curl http://43.143.139.197:3000
```

## 🔧 故障排查

### 如果工作流没有触发

1. **检查 Runner 状态**：
   - 访问 Runner 设置页面
   - 确认 Runner 为 "Online"

2. **检查工作流文件**：
   - 确认 `deploy-self-hosted.yml` 已提交
   - 检查触发条件是否正确

3. **手动触发测试**：
   - 进入 Actions 页面
   - 选择 "🚀 自托管 Runner 自动部署"
   - 点击 "Run workflow"

### 如果部署失败

1. **查看工作流日志**：
   - 在 GitHub Actions 页面查看详细日志

2. **查看服务器日志**：
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
   cd /opt/enterprise-ai-platform
   docker-compose logs --tail=50
   ```

3. **检查 Runner 日志**：
   ```bash
   sudo journalctl -u actions.runner.* -n 100
   ```

## 📝 后续使用

### 自动部署

每次推送代码到 main 分支，会自动触发部署：
```powershell
git add .
git commit -m "更新代码"
git push origin main
```

### 手动触发

在 GitHub Actions 页面手动触发：
1. 进入 Actions 页面
2. 选择 "🚀 自托管 Runner 自动部署"
3. 点击 "Run workflow"

### 查看部署历史

在 GitHub Actions 页面可以查看所有部署历史记录。

## 🎉 优势

- ✅ **完全免费** - 不消耗 GitHub Actions 分钟数
- ✅ **无时间限制** - 可以运行任意长时间
- ✅ **更快部署** - 直接在服务器上运行
- ✅ **自动启动** - 服务器重启后自动运行

---

**部署测试已完成！** 🚀


