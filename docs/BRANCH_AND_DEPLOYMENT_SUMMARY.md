# 分支管理和部署方案总结

## ✅ 已完成的工作

### 1. Git分支管理

- ✅ **dev分支**: 开发分支，用于本地开发（支持热加载）
- ✅ **test分支**: 测试分支，包含服务器部署配置

### 2. Docker镜像同步方案

#### 同步脚本

- ✅ `scripts/sync-to-server.sh` - Linux/Mac同步脚本
- ✅ `scripts/sync-to-server.ps1` - Windows PowerShell同步脚本
- ✅ `scripts/deploy-to-server.sh` - 一键部署脚本
- ✅ `scripts/setup-server.sh` - 服务器初始化脚本

#### 功能特性

1. **镜像导出和压缩**: 自动导出Docker镜像并压缩，减少传输时间
2. **自动上传**: 通过SSH上传到服务器
3. **自动加载**: 在服务器上自动加载镜像
4. **配置同步**: 同步docker-compose配置文件
5. **可选重启**: 可选择是否重启服务器上的服务

### 3. 测试环境配置

- ✅ `docker-compose.test.yml` - 测试环境Docker Compose配置
  - 使用预构建镜像（不进行本地构建）
  - 生产环境配置（无热加载）
  - 优化的资源设置

### 4. 文档

- ✅ `README_DEPLOY.md` - 详细部署文档
- ✅ `DEPLOYMENT_GUIDE.md` - 部署指南
- ✅ `.gitignore` - 更新，排除敏感文件和构建产物

## 🚀 使用方法

### 首次部署

```bash
# 1. 服务器初始化
scp -i enterprise_ai_platform.pem scripts/setup-server.sh ubuntu@43.143.139.197:~/
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
chmod +x ~/setup-server.sh
~/setup-server.sh
```

### 日常开发流程

```bash
# 1. 本地开发（dev分支）
git checkout dev
docker-compose up  # 支持热加载

# 2. 测试通过后，部署到测试环境（test分支）
git checkout test
git merge dev
./scripts/deploy-to-server.sh
```

### 只更新特定服务

```bash
# 同步特定服务
./scripts/sync-to-server.sh agent-service api-gateway
```

## 📋 工作流程

```
本地开发 (dev分支)
    ↓
修改代码 + 本地测试
    ↓
提交到dev分支
    ↓
合并到test分支
    ↓
构建Docker镜像
    ↓
同步到服务器 (43.143.139.197)
    ↓
服务器测试环境运行
```

## 🔧 服务器信息

- **服务器地址**: 43.143.139.197
- **SSH用户**: ubuntu
- **SSH密钥**: enterprise_ai_platform.pem
- **项目目录**: ~/enterprise-ai-platform

## 📝 注意事项

1. **SSH密钥安全**: 
   - 确保 `enterprise_ai_platform.pem` 文件权限为 600
   - 不要将密钥文件提交到Git

2. **镜像大小**: 
   - 大镜像传输可能需要较长时间
   - 脚本已自动压缩镜像以减少传输时间

3. **网络稳定性**: 
   - 确保网络连接稳定
   - 如果传输中断，可以重新运行脚本

4. **服务依赖**: 
   - 同步时注意服务之间的依赖关系
   - 建议按依赖顺序同步服务

## 🎯 下一步

1. **推送到远程仓库**:
   ```bash
   git push origin dev
   git push origin test
   ```

2. **首次服务器部署**:
   - 执行服务器初始化脚本
   - 运行首次同步

3. **验证部署**:
   - 检查服务是否正常启动
   - 验证功能是否正常

## 📚 相关文档

- [README_DEPLOY.md](./README_DEPLOY.md) - 详细部署文档
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - 部署指南
- [docker-compose.test.yml](./docker-compose.test.yml) - 测试环境配置






























