# 部署文档

## 环境说明

- **开发环境**: 本地Docker（支持热加载）
- **测试环境**: 服务器 43.143.139.197

## 分支管理

- **dev分支**: 开发分支，用于本地开发
- **test分支**: 测试分支，包含服务器部署配置

## 快速开始

### 1. 服务器初始化（首次部署）

在服务器上执行：

```bash
# 上传初始化脚本到服务器
scp -i enterprise_ai_platform.pem scripts/setup-server.sh ubuntu@43.143.139.197:~/

# 在服务器上执行
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
chmod +x ~/setup-server.sh
~/setup-server.sh
```

### 2. 本地开发流程

```bash
# 1. 切换到dev分支
git checkout dev

# 2. 进行开发（支持热加载）
docker-compose up

# 3. 测试通过后，提交到dev分支
git add .
git commit -m "feat: 新功能"
git push origin dev
```

### 3. 部署到测试环境

```bash
# 1. 切换到test分支
git checkout test

# 2. 合并dev分支的更改
git merge dev

# 3. 构建并同步到服务器
./scripts/deploy-to-server.sh

# 或者只同步特定服务
./scripts/sync-to-server.sh agent-service api-gateway
```

## 同步脚本说明

### sync-to-server.sh / sync-to-server.ps1

将本地Docker镜像同步到服务器：

1. 导出本地Docker镜像
2. 压缩镜像文件
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

一键部署流程：

1. 构建所有Docker镜像
2. 标记镜像为latest
3. 同步到服务器

## 服务器配置

### 目录结构

```
~/enterprise-ai-platform/
├── docker-compose.test.yml  # 测试环境配置
├── images/                  # 镜像文件存储
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
docker-compose -f docker-compose.test.yml logs -f

# 停止服务
docker-compose -f docker-compose.test.yml down
```

## 热加载说明

### 开发环境（本地）

开发环境已配置热加载：

- **Python服务**: 使用 `uvicorn --reload`
- **Node.js服务**: 使用 `tsx watch` 或 `nodemon`
- **配置文件**: 通过volume挂载实现实时更新

### 测试环境（服务器）

测试环境使用预构建的镜像，不支持热加载。需要：

1. 本地修改代码
2. 构建新镜像
3. 同步到服务器
4. 重启服务

## 工作流程

```
本地开发 (dev分支)
    ↓
修改代码
    ↓
本地测试 (docker-compose up)
    ↓
提交到dev分支
    ↓
合并到test分支
    ↓
构建镜像
    ↓
同步到服务器
    ↓
服务器测试
```

## 故障排查

### 镜像同步失败

1. 检查SSH密钥权限：`chmod 600 enterprise_ai_platform.pem`
2. 检查服务器磁盘空间：`df -h`
3. 检查网络连接：`ping 43.143.139.197`

### 服务启动失败

1. 查看日志：`docker-compose -f docker-compose.test.yml logs [service-name]`
2. 检查镜像是否存在：`docker images | grep enterprise-ai`
3. 检查端口占用：`netstat -tlnp | grep [port]`

### 配置文件不同步

确保 `docker-compose.test.yml` 已同步到服务器。

## 注意事项

1. **SSH密钥安全**: 不要将 `.pem` 文件提交到Git
2. **镜像大小**: 大镜像传输可能需要较长时间
3. **网络带宽**: 确保网络连接稳定
4. **服务器资源**: 确保服务器有足够的磁盘空间和内存

## 自动化部署（可选）

可以配置GitHub Actions或GitLab CI/CD实现自动部署：

1. 推送到test分支时自动触发
2. 构建镜像
3. 同步到服务器
4. 重启服务





































