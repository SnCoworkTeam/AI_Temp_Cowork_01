# 部署脚本创建完成

已成功创建以下部署脚本，用于将本地Docker环境部署到测试服务器（43.143.139.197）：

## 📦 已创建的脚本

### 1. Docker镜像上传脚本
- **文件**: `scripts/deployment/upload-docker-images.ps1`
- **功能**: 导出本地Docker镜像并上传到测试服务器
- **使用方法**: 
  ```powershell
  .\scripts\deployment\upload-docker-images.ps1
  # 或使用批处理文件
  .\upload-images.bat
  ```

### 2. 文件监控和自动同步（热加载）
- **文件**: `scripts/deployment/watch-and-sync.ps1`
- **功能**: 监控本地代码文件变更，自动上传到服务器
- **使用方法**: 
  ```powershell
  .\scripts\deployment\watch-and-sync.ps1 -ServiceName "api-gateway" -AutoRestart
  # 或使用批处理文件
  .\watch-and-sync.bat api-gateway
  ```

### 3. 一键部署脚本
- **文件**: `scripts/deployment/deploy-test-server.ps1`
- **功能**: 完整部署流程（构建→上传→同步→重启）
- **使用方法**: 
  ```powershell
  .\scripts\deployment\deploy-test-server.ps1
  # 或使用批处理文件
  .\deploy-to-test.bat
  ```

### 4. 便捷批处理文件
- `deploy-to-test.bat` - 一键部署
- `watch-and-sync.bat` - 启动热加载
- `upload-images.bat` - 上传镜像

## 🚀 快速开始

### 首次部署

```powershell
# 方式1: 使用批处理文件（推荐）
.\deploy-to-test.bat

# 方式2: 使用PowerShell脚本
.\scripts\deployment\deploy-test-server.ps1
```

### 开发时热加载（推荐）

```powershell
# 监控指定服务，自动上传并重启
.\watch-and-sync.bat api-gateway
```

这样，当你修改代码时：
- ✅ 自动检测文件变更
- ✅ 自动上传到服务器
- ✅ 自动重启服务（如果启用）

**停止监控**: 按 `Ctrl+C`

### 只上传Docker镜像

```powershell
.\upload-images.bat
```

## 📋 服务器信息

- **服务器地址**: 43.143.139.197
- **用户名**: ubuntu
- **远程路径**: /opt/enterprise-ai-platform
- **SSH密钥**: enterprise_ai_platform.pem（需要在项目根目录或 ~/.ssh/）

## 📚 详细文档

- **快速开始**: `QUICK_START_DEPLOYMENT.md`
- **详细说明**: `scripts/deployment/README_DEPLOYMENT.md`

## ⚠️ 注意事项

1. **首次部署**: 需要先上传镜像，可能需要较长时间
2. **网络速度**: 上传速度取决于网络带宽
3. **服务依赖**: 某些服务依赖其他服务，注意启动顺序
4. **SSH密钥**: 确保 `enterprise_ai_platform.pem` 文件存在且可访问

## 🔧 故障排查

如果遇到问题：

1. **检查SSH连接**:
   ```powershell
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
   ```

2. **查看服务器日志**:
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
   cd /opt/enterprise-ai-platform
   docker compose logs -f [service-name]
   ```

3. **检查服务状态**:
   ```bash
   docker compose ps
   ```

## ✨ 特性

- ✅ 自动从 `remote.ssh` 读取服务器配置
- ✅ 支持单个服务或所有服务部署
- ✅ 自动压缩镜像（减少传输时间）
- ✅ 增量代码同步（只上传变更的文件）
- ✅ 文件监控和自动同步（热加载）
- ✅ 自动重启服务（可选）

## 📝 下一步

1. 确保 `enterprise_ai_platform.pem` 文件存在
2. 检查 `remote.ssh` 配置是否正确
3. 运行 `.\deploy-to-test.bat` 进行首次部署
4. 开发时使用 `.\watch-and-sync.bat [service-name]` 启用热加载

