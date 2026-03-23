# 部署到测试服务器指南

本目录包含将本地开发环境部署到测试服务器（43.143.139.197）的脚本。

## 前置要求

1. **SSH密钥文件**: `enterprise_ai_platform.pem` 需要放在项目根目录或 `~/.ssh/` 目录
2. **服务器配置**: `remote.ssh` 文件已配置服务器连接信息
3. **Docker**: 本地已安装Docker并构建了镜像
4. **SSH工具**: 需要 `ssh` 和 `scp` 命令（Git for Windows包含）

## 脚本说明

### 1. `upload-docker-images.ps1` - Docker镜像上传

导出本地Docker镜像并上传到测试服务器。

**使用方法：**
```powershell
# 上传所有服务的镜像
.\scripts\deployment\upload-docker-images.ps1

# 只上传指定服务的镜像
.\scripts\deployment\upload-docker-images.ps1 -ServiceName "api-gateway"

# 只构建，不上传
.\scripts\deployment\upload-docker-images.ps1 -BuildOnly

# 跳过构建，直接上传已有镜像
.\scripts\deployment\upload-docker-images.ps1 -SkipBuild

# 不压缩镜像（上传更快但文件更大）
.\scripts\deployment\upload-docker-images.ps1 -Compress:$false
```

**功能：**
- 自动从 `docker-compose.yml` 读取服务列表
- 构建Docker镜像（可选）
- 导出镜像为tar文件
- 压缩镜像（可选，使用gzip）
- 上传到服务器
- 在服务器上自动加载镜像

### 2. `watch-and-sync.ps1` - 文件监控和自动同步（热加载）

监控本地代码文件变更，自动上传到服务器。

**使用方法：**
```powershell
# 监控所有服务的文件
.\scripts\deployment\watch-and-sync.ps1

# 只监控指定服务的文件
.\scripts\deployment\watch-and-sync.ps1 -ServiceName "api-gateway"

# 监控并自动重启服务
.\scripts\deployment\watch-and-sync.ps1 -ServiceName "api-gateway" -AutoRestart

# 自定义检查间隔（秒）
.\scripts\deployment\watch-and-sync.ps1 -Interval 5
```

**功能：**
- 实时监控代码文件变更
- 自动上传变更的文件到服务器
- 支持防抖（避免频繁上传）
- 可选自动重启服务
- 自动排除不需要的文件（.git, node_modules等）

**停止监控：** 按 `Ctrl+C`

### 3. `deploy-test-server.ps1` - 一键部署

完整部署流程：构建镜像 → 上传镜像 → 同步代码 → 重启服务。

**使用方法：**
```powershell
# 完整部署所有服务
.\scripts\deployment\deploy-test-server.ps1

# 只部署指定服务
.\scripts\deployment\deploy-test-server.ps1 -ServiceName "api-gateway"

# 只构建镜像，不部署
.\scripts\deployment\deploy-test-server.ps1 -BuildOnly

# 跳过镜像上传，只同步代码
.\scripts\deployment\deploy-test-server.ps1 -SkipImages

# 跳过代码同步，只上传镜像
.\scripts\deployment\deploy-test-server.ps1 -SkipCode

# 不自动重启服务
.\scripts\deployment\deploy-test-server.ps1 -Restart:$false
```

**功能：**
- 构建Docker镜像
- 上传镜像到服务器
- 同步代码文件
- 重启服务
- 验证部署状态

### 4. `sync-to-server.ps1` - 代码同步

同步Git变更的文件到服务器（已存在，用于增量同步）。

**使用方法：**
```powershell
# 同步所有变更的文件
.\scripts\deployment\sync-to-server.ps1

# 包含未跟踪的文件
.\scripts\deployment\sync-to-server.ps1 -IncludeUntracked

# 预览模式（不实际上传）
.\scripts\deployment\sync-to-server.ps1 -DryRun
```

## 典型使用场景

### 场景1: 首次部署

```powershell
# 1. 构建并上传所有镜像
.\scripts\deployment\upload-docker-images.ps1

# 2. 同步代码文件
.\scripts\deployment\sync-to-server.ps1

# 3. 在服务器上启动服务（SSH连接后）
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
docker compose up -d
```

### 场景2: 开发时热加载

```powershell
# 启动文件监控（自动上传变更）
.\scripts\deployment\watch-and-sync.ps1 -ServiceName "api-gateway" -AutoRestart
```

这样，当你修改代码时，文件会自动上传到服务器，并自动重启服务。

### 场景3: 快速部署单个服务

```powershell
# 一键部署指定服务
.\scripts\deployment\deploy-test-server.ps1 -ServiceName "api-gateway"
```

### 场景4: 只更新代码，不重新构建镜像

```powershell
# 同步代码并重启服务
.\scripts\deployment\sync-to-server.ps1
# 然后SSH到服务器重启服务
```

## 服务器端操作

### SSH连接到服务器

```powershell
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
```

### 查看服务状态

```bash
cd /opt/enterprise-ai-platform
docker compose ps
```

### 查看服务日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看指定服务日志
docker compose logs -f api-gateway
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启指定服务
docker compose restart api-gateway
```

### 重新加载镜像

如果镜像已上传但未加载：

```bash
cd /opt/enterprise-ai-platform
gunzip -c docker-images/api-gateway.tar.gz | docker load
docker compose restart api-gateway
```

## 注意事项

1. **镜像大小**: Docker镜像可能很大，首次上传需要较长时间
2. **网络速度**: 上传速度取决于网络带宽
3. **服务器空间**: 确保服务器有足够的磁盘空间
4. **权限问题**: 确保SSH密钥文件权限正确（Windows上通常不需要特别设置）
5. **服务依赖**: 某些服务依赖其他服务，注意启动顺序

## 故障排查

### 问题1: 无法连接服务器

- 检查 `remote.ssh` 配置
- 检查SSH密钥文件是否存在
- 检查网络连接

### 问题2: 镜像上传失败

- 检查服务器磁盘空间
- 检查网络连接
- 尝试不压缩上传（`-Compress:$false`）

### 问题3: 文件同步失败

- 检查文件路径是否正确
- 检查服务器目录权限
- 检查SSH连接是否正常

### 问题4: 服务无法启动

- SSH到服务器查看日志：`docker compose logs [service-name]`
- 检查环境变量配置
- 检查服务依赖是否已启动

## 性能优化建议

1. **使用rsync**: 如果安装了rsync，代码同步会更快
2. **压缩镜像**: 默认启用压缩，可以显著减少传输时间
3. **增量同步**: 使用 `sync-to-server.ps1` 只同步变更的文件
4. **批量操作**: 使用 `deploy-test-server.ps1` 一次性完成所有操作

## 相关文件

- `remote.ssh` - SSH服务器配置
- `docker-compose.yml` - Docker服务配置
- `scripts/deployment/sync-to-server.ps1` - 代码同步脚本

