# 快速开始：部署到测试服务器

## 快速部署步骤

### 1. 首次部署（完整部署）

```powershell
# 方式1: 使用批处理文件（推荐）
.\deploy-to-test.bat

# 方式2: 使用PowerShell脚本
.\scripts\deployment\deploy-test-server.ps1
```

这将完成：
- ✅ 构建所有Docker镜像
- ✅ 上传镜像到服务器
- ✅ 同步代码文件
- ✅ 重启服务

### 2. 开发时热加载（推荐）

```powershell
# 方式1: 使用批处理文件
.\watch-and-sync.bat api-gateway

# 方式2: 使用PowerShell脚本（带自动重启）
.\scripts\deployment\watch-and-sync.ps1 -ServiceName "api-gateway" -AutoRestart
```

这样，当你修改代码时：
- 📝 自动检测文件变更
- 📤 自动上传到服务器
- 🔄 自动重启服务（如果启用）

**停止监控：** 按 `Ctrl+C`

### 3. 只上传Docker镜像

```powershell
# 方式1: 使用批处理文件
.\upload-images.bat

# 方式2: 使用PowerShell脚本
.\scripts\deployment\upload-docker-images.ps1
```

### 4. 只同步代码（不重新构建镜像）

```powershell
.\scripts\deployment\sync-to-server.ps1
```

然后SSH到服务器重启服务：
```bash
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
docker compose restart [service-name]
```

## 常用命令

### 部署单个服务

```powershell
.\deploy-to-test.bat api-gateway
```

### 监控单个服务（热加载）

```powershell
.\watch-and-sync.bat api-gateway
```

### 只构建镜像，不上传

```powershell
.\scripts\deployment\upload-docker-images.ps1 -BuildOnly
```

### 跳过构建，直接上传已有镜像

```powershell
.\scripts\deployment\upload-docker-images.ps1 -SkipBuild
```

## 服务器信息

- **服务器地址**: 43.143.139.197
- **用户名**: ubuntu
- **远程路径**: /opt/enterprise-ai-platform
- **SSH密钥**: enterprise_ai_platform.pem

## 查看服务器状态

```powershell
# SSH连接
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 查看服务状态
cd /opt/enterprise-ai-platform
docker compose ps

# 查看日志
docker compose logs -f [service-name]
```

## 注意事项

1. **首次部署**: 需要先上传镜像，可能需要较长时间
2. **热加载**: 适合开发时使用，修改代码后自动同步
3. **网络速度**: 上传速度取决于网络带宽
4. **服务依赖**: 某些服务依赖其他服务，注意启动顺序

## 更多信息

详细文档请查看：`scripts/deployment/README_DEPLOYMENT.md`

