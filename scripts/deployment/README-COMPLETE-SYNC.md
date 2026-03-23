# 完整自动同步脚本使用指南

## 📖 简介

`complete-sync.ps1` 是一个完整的自动同步脚本，用于将本地开发环境的代码、Docker镜像、数据库迁移和数据同步到远程服务器。

## 🚀 快速开始

### 前置条件

1. **配置文件**
   - `remote.ssh` - SSH连接配置（项目根目录）
   - `enterprise_ai_platform.pem` - SSH私钥文件（项目根目录）

2. **本地环境**
   - PowerShell 5.1+
   - Docker Desktop
   - SSH客户端（Windows 10+内置）

3. **服务器环境**
   - Docker和Docker Compose已安装
   - Python 3.11+（用于执行数据库迁移）
   - 项目目录：`/opt/enterprise-ai-platform`

### 基本使用

```powershell
# 进入项目根目录
cd E:\enterprise-ai-platform

# 执行完整同步
.\scripts\deployment\complete-sync.ps1
```

## 📋 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-ConfigFile` | string | `remote.ssh` | SSH配置文件路径 |
| `-KeyFile` | string | `enterprise_ai_platform.pem` | SSH私钥文件名 |
| `-RemotePath` | string | `/opt/enterprise-ai-platform` | 服务器项目路径 |
| `-SkipDataSync` | switch | `$false` | 跳过数据同步 |
| `-BuildImagesOnly` | switch | `$false` | 仅构建镜像，不同步代码 |
| `-SkipMigration` | switch | `$false` | 跳过数据库迁移 |
| `-DryRun` | switch | `$false` | 干运行模式（仅显示操作） |
| `-Services` | string | `""` | 指定要同步的服务（逗号分隔） |

## 💡 使用示例

### 1. 完整同步（推荐首次使用）

```powershell
# 同步所有内容：代码、镜像、迁移、部署
.\scripts\deployment\complete-sync.ps1
```

### 2. 仅同步代码和镜像

```powershell
# 跳过数据库迁移和数据同步
.\scripts\deployment\complete-sync.ps1 -SkipMigration -SkipDataSync
```

### 3. 仅构建和同步镜像

```powershell
# 不同步代码，只构建镜像
.\scripts\deployment\complete-sync.ps1 -BuildImagesOnly
```

### 4. 同步指定服务

```powershell
# 只同步api-gateway和workflow-engine
.\scripts\deployment\complete-sync.ps1 -Services "api-gateway,workflow-engine"
```

### 5. 干运行模式（预览操作）

```powershell
# 查看将要执行的操作，不实际执行
.\scripts\deployment\complete-sync.ps1 -DryRun
```

### 6. 组合使用

```powershell
# 仅构建镜像，跳过迁移和数据同步
.\scripts\deployment\complete-sync.ps1 -BuildImagesOnly -SkipMigration -SkipDataSync
```

## 📊 执行流程

脚本按以下顺序执行：

1. **读取SSH配置** - 从`remote.ssh`读取服务器信息
2. **测试SSH连接** - 验证连接可用性
3. **同步代码文件** - 使用rsync/scp同步源代码
4. **构建Docker镜像** - 构建并同步镜像到服务器
5. **执行数据库迁移** - 同步迁移文件并执行
6. **数据备份和同步** - 备份本地数据库（可选）
7. **部署服务** - 重启Docker容器

## 🔍 同步内容详情

### 代码同步

**同步的目录**:
- 所有服务目录（api-gateway, workflow-engine等）
- `database/` - 数据库迁移文件
- `shared_libs/` - 共享库
- `scripts/` - 脚本文件
- `docker-compose.yml` - Docker编排配置

**排除的内容**:
- `__pycache__/`, `*.pyc` - Python缓存
- `node_modules/`, `.next/` - Node.js依赖和构建产物
- `venv/` - Python虚拟环境
- `.pytest_cache/` - 测试缓存

### Docker镜像同步

**构建的镜像**:
- `enterprise-ai-api-gateway:latest`
- `enterprise-ai-workflow-engine:latest`
- `enterprise-ai-web-ui:latest`
- 以及其他所有服务的镜像

**同步方式**:
1. 本地构建镜像
2. 保存为tar文件
3. 上传到服务器
4. 在服务器上加载镜像

### 数据库迁移

**同步内容**:
- `database/src/migrations/versions/` - 所有迁移脚本
- `database/alembic.ini` - Alembic配置
- `database/src/migrations/env.py` - 迁移环境配置

**执行方式**:
- 在服务器上执行 `alembic upgrade head`

### 数据同步（可选）

**备份内容**:
- 本地PostgreSQL数据库完整备份

**同步方式**:
- 使用`pg_dump`备份
- 上传备份文件到服务器
- 可在服务器上手动恢复

## ⚠️ 注意事项

### 1. 数据同步风险

**默认跳过数据同步**，避免覆盖生产数据。如果需要同步数据：

```powershell
# 明确启用数据同步（谨慎使用）
.\scripts\deployment\complete-sync.ps1 -SkipDataSync:$false
```

### 2. 数据库迁移

- 迁移执行前会自动同步迁移文件
- 如果迁移失败，需要手动检查并修复
- 建议先在测试环境验证迁移

### 3. 镜像大小

- 镜像可能很大（几百MB到几GB）
- 上传时间取决于网络速度
- 建议使用Docker镜像仓库优化速度

### 4. 网络连接

- 确保SSH连接稳定
- 如果连接中断，可以重新运行脚本（支持增量同步）

## 🐛 故障排除

### SSH连接失败

```powershell
# 检查SSH配置
cat remote.ssh

# 测试SSH连接
ssh -i enterprise_ai_platform.pem -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "echo 'test'"
```

### Docker镜像构建失败

```powershell
# 检查Docker是否运行
docker ps

# 手动构建镜像测试
docker build -t enterprise-ai-api-gateway:latest -f api-gateway/Dockerfile api-gateway
```

### 数据库迁移失败

```powershell
# 在服务器上手动执行迁移
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform/database
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=ai_user
export DB_PASSWORD=ai_password
export DB_NAME=ai_platform
python3 -m alembic upgrade head
```

### 服务启动失败

```powershell
# 在服务器上检查服务状态
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
docker-compose ps
docker-compose logs [service-name]
```

## 📈 性能优化

### 1. 使用Docker镜像仓库

```powershell
# 推送到私有仓库
docker tag enterprise-ai-api-gateway:latest registry.example.com/enterprise-ai-api-gateway:latest
docker push registry.example.com/enterprise-ai-api-gateway:latest
```

### 2. 增量同步

脚本已实现增量同步，只同步变更的文件。

### 3. 并行构建

可以修改脚本使用`Start-Job`并行构建多个镜像。

## 🔒 安全建议

1. **密钥管理**
   - 不要将`.pem`文件提交到Git
   - 使用`.gitignore`排除密钥文件

2. **访问控制**
   - 限制SSH访问IP
   - 定期轮换SSH密钥

3. **数据安全**
   - 默认跳过数据同步
   - 数据迁移前先备份

## 📞 支持

如有问题，请查看：
- [完整同步方案分析](./COMPLETE_SYNC_ANALYSIS.md)
- [部署文档](../deployment/)
- [故障排除指南](#故障排除)






