# 自动部署配置说明

## 概述

已配置 CI/CD 工作流，当测试通过后自动部署到服务器 `43.143.139.197`。

## 部署条件

自动部署会在以下**所有条件**满足时触发：

1. ✅ **代码推送到 `main` 分支** 或 **创建版本标签 `v*`**
2. ✅ **所有测试通过** (`test` job 成功)
3. ✅ **前端测试通过** (`frontend-test` job 成功)
4. ✅ **Docker 镜像构建完成** (`build-images` job 完成，允许部分失败)

## 部署流程

```
代码推送 → 运行测试 → 前端测试 → 构建镜像 → 自动部署
   ↓           ↓          ↓          ↓          ↓
  main     pytest     npm build   docker    SSH部署
```

## 部署步骤

部署到服务器时会执行以下步骤：

1. **拉取最新代码** - 从 GitHub 拉取 main 分支最新代码
2. **数据库迁移** - 运行 Alembic 迁移（如果 api-gateway 正在运行）
3. **备份当前状态** - 备份当前运行的容器状态
4. **停止旧版本** - 优雅停止当前运行的服务
5. **构建新版本** - 在服务器上构建 Docker 镜像
6. **启动新版本** - 启动所有服务
7. **健康检查** - 验证 API Gateway 是否正常响应

## 服务器配置

部署目标服务器：
- **IP**: `43.143.139.197` (通过 `SERVER_HOST` secret 配置)
- **用户**: 通过 `SERVER_USER` secret 配置
- **SSH密钥**: 通过 `SSH_PRIVATE_KEY` secret 配置
- **项目目录**: `/opt/enterprise-ai-platform`

## GitHub Secrets 配置

确保以下 secrets 已正确配置：

```bash
# 配置服务器信息
gh secret set SERVER_HOST --body "43.143.139.197"
gh secret set SERVER_USER --body "your-username"
gh secret set SSH_PRIVATE_KEY < enterprise_ai_platform.pem
```

## 部署验证

部署完成后，可以通过以下方式验证：

1. **检查服务状态**:
   ```bash
   ssh $SERVER_USER@$SERVER_HOST "cd /opt/enterprise-ai-platform && docker-compose ps"
   ```

2. **检查健康状态**:
   ```bash
   curl http://43.143.139.197:8080/health
   ```

3. **查看部署日志**:
   在 GitHub Actions 的部署 job 中查看详细日志

## 回滚机制

如果部署失败或健康检查不通过：

1. 部署脚本会自动停止新版本
2. 可以手动恢复备份的容器状态
3. 备份文件保存在: `/tmp/containers_backup_YYYYMMDD_HHMMSS.json`

## 手动触发部署

如果需要手动触发部署：

```bash
gh workflow run deploy.yml --field environment=production
```

## 注意事项

1. ⚠️ **测试必须全部通过** - 如果测试失败，部署不会执行
2. ⚠️ **前端构建必须成功** - 前端类型检查和构建必须通过
3. ⚠️ **服务器必须可访问** - 确保 SSH 连接正常
4. ⚠️ **数据库迁移** - 如果 api-gateway 未运行，迁移步骤会跳过
5. ⚠️ **健康检查超时** - 如果 75 秒内服务未就绪，部署会失败

## 故障排查

### 部署失败

1. 检查 GitHub Actions 日志
2. 检查服务器 SSH 连接
3. 检查服务器上的 Docker 和 docker-compose
4. 检查服务器磁盘空间
5. 检查服务器上的项目目录权限

### 健康检查失败

1. 查看容器日志: `docker-compose logs api-gateway`
2. 检查端口占用: `netstat -tulpn | grep 8080`
3. 检查防火墙设置
4. 手动测试: `curl http://localhost:8080/health`

## 更新日志

- **2025-12-04**: 配置自动部署，测试通过后自动部署到服务器





