# 部署指南

## 📋 概述

本指南说明如何将本地开发环境的Docker服务同步到服务器测试环境。

## 🏗️ 环境架构

```
本地开发环境 (dev分支)
    ↓ 热加载开发
    ↓ 构建镜像
    ↓ 同步脚本
服务器测试环境 (test分支)
```

## 🚀 快速开始

### 1. 首次部署 - 服务器初始化

```bash
# 上传初始化脚本
scp -i enterprise_ai_platform.pem scripts/setup-server.sh ubuntu@43.143.139.197:~/

# SSH到服务器并执行
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
chmod +x ~/setup-server.sh
~/setup-server.sh
```

### 2. 日常开发流程

#### 步骤1: 本地开发（dev分支）

```bash
# 切换到dev分支
git checkout dev

# 启动本地开发环境（支持热加载）
docker-compose up

# 进行开发和测试
# ... 修改代码 ...

# 提交更改
git add .
git commit -m "feat: 新功能"
git push origin dev
```

#### 步骤2: 部署到测试环境（test分支）

```bash
# 切换到test分支
git checkout test

# 合并dev分支的更改
git merge dev

# 构建并同步到服务器
./scripts/deploy-to-server.sh

# 或者只同步特定服务
./scripts/sync-to-server.sh agent-service api-gateway
```

## 📦 同步脚本说明

### sync-to-server.sh / sync-to-server.ps1

**功能**:
1. 导出本地Docker镜像
2. 压缩镜像文件（减少传输时间）
3. 上传到服务器
4. 在服务器上加载镜像
5. 同步配置文件
6. 可选：重启服务

**使用方法**:

```bash
# Linux/Mac
./scripts/sync-to-server.sh

# Windows PowerShell
.\scripts\sync-to-server.ps1

# 同步特定服务
./scripts/sync-to-server.sh agent-service api-gateway
```

### deploy-to-server.sh

**功能**: 一键部署流程
1. 构建所有Docker镜像
2. 标记镜像为latest
3. 同步到服务器

**使用方法**:

```bash
./scripts/deploy-to-server.sh
```

## 🔧 服务器配置

### 目录结构

```
~/enterprise-ai-platform/
├── docker-compose.test.yml  # 测试环境配置
├── images/                  # 镜像文件存储（临时）
├── logs/                    # 日志目录
└── data/                    # 数据目录
```

### 服务管理

```bash
# SSH到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 进入项目目录
cd ~/enterprise-ai-platform

# 启动服务
docker-compose -f docker-compose.test.yml up -d

# 查看服务状态
docker-compose -f docker-compose.test.yml ps

# 查看日志
docker-compose -f docker-compose.test.yml logs -f [service-name]

# 停止服务
docker-compose -f docker-compose.test.yml down

# 重启服务
docker-compose -f docker-compose.test.yml restart [service-name]
```

## 🔥 热加载说明

### 开发环境（本地）

- **Python服务**: `uvicorn --reload --reload-dir /app/src`
- **Node.js服务**: `tsx watch src/index.ts` 或 `nodemon`
- **配置文件**: 通过volume挂载实现实时更新

### 测试环境（服务器）

测试环境使用预构建的镜像，**不支持热加载**。需要：

1. 本地修改代码
2. 构建新镜像：`docker-compose build [service-name]`
3. 同步到服务器：`./scripts/sync-to-server.sh [service-name]`
4. 重启服务：在服务器上执行 `docker-compose -f docker-compose.test.yml restart [service-name]`

## 📊 工作流程

```
┌─────────────────┐
│  本地开发环境    │
│  (dev分支)      │
└────────┬────────┘
         │
         │ 1. 修改代码
         │ 2. 本地测试
         │ 3. 提交到dev
         ↓
┌─────────────────┐
│  合并到test分支  │
└────────┬────────┘
         │
         │ 4. git merge dev
         │ 5. 构建镜像
         │ 6. 同步到服务器
         ↓
┌─────────────────┐
│  服务器测试环境  │
│  (test分支)     │
└─────────────────┘
```

## 🐛 故障排查

### 镜像同步失败

1. **检查SSH密钥权限**
   ```bash
   chmod 600 enterprise_ai_platform.pem
   ```

2. **检查服务器磁盘空间**
   ```bash
   ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197 "df -h"
   ```

3. **检查网络连接**
   ```bash
   ping 43.143.139.197
   ```

### 服务启动失败

1. **查看日志**
   ```bash
   docker-compose -f docker-compose.test.yml logs [service-name]
   ```

2. **检查镜像是否存在**
   ```bash
   docker images | grep enterprise-ai
   ```

3. **检查端口占用**
   ```bash
   netstat -tlnp | grep [port]
   ```

### 配置文件不同步

确保 `docker-compose.test.yml` 已同步到服务器：

```bash
scp -i enterprise_ai_platform.pem docker-compose.test.yml ubuntu@43.143.139.197:~/enterprise-ai-platform/
```

## ⚠️ 注意事项

1. **SSH密钥安全**: 不要将 `.pem` 文件提交到Git
2. **镜像大小**: 大镜像传输可能需要较长时间，建议使用压缩
3. **网络带宽**: 确保网络连接稳定
4. **服务器资源**: 确保服务器有足够的磁盘空间和内存
5. **服务依赖**: 同步时注意服务之间的依赖关系

## 🔄 自动化部署（可选）

可以配置GitHub Actions或GitLab CI/CD实现自动部署：

1. 推送到test分支时自动触发
2. 构建镜像
3. 同步到服务器
4. 重启服务

## 📝 示例

### 完整部署流程

```bash
# 1. 本地开发
git checkout dev
# ... 修改代码 ...
git add .
git commit -m "feat: 新功能"
git push origin dev

# 2. 切换到test分支并合并
git checkout test
git merge dev

# 3. 构建并部署
./scripts/deploy-to-server.sh

# 4. 在服务器上验证
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd ~/enterprise-ai-platform
docker-compose -f docker-compose.test.yml ps
```

### 只更新特定服务

```bash
# 只同步agent-service
./scripts/sync-to-server.sh agent-service

# 同步多个服务
./scripts/sync-to-server.sh agent-service api-gateway chat-service
```

## 📚 相关文档

- [README_DEPLOY.md](./README_DEPLOY.md) - 详细部署文档
- [docker-compose.test.yml](./docker-compose.test.yml) - 测试环境配置
- [scripts/](./scripts/) - 部署脚本目录






























