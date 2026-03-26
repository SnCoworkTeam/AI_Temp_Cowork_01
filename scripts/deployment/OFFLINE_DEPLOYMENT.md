# 离线部署指南

## 概述

当服务器无法连接Docker Hub时，可以使用离线部署方式：
1. 在本地（有网络）导出所有Docker镜像
2. 将镜像文件上传到服务器
3. 在服务器上导入镜像并启动服务

## 步骤

### 步骤1: 在本地导出镜像

```bash
# 确保已安装Docker并可以访问Docker Hub
cd /path/to/enterprise-ai-platform

# 运行导出脚本
bash scripts/deployment/export-images.sh
```

这将：
- 从所有docker-compose文件读取镜像列表
- 拉取所有需要的镜像（如果本地没有）
- 导出镜像为tar.gz文件
- 创建导入脚本和清单文件

输出目录结构：
```
docker-images-export/
├── images/                    # 镜像文件目录
│   ├── postgres_15.tar.gz
│   ├── redis_7-alpine.tar.gz
│   └── ...
├── images-manifest.txt        # 镜像清单
├── load-images.sh             # 导入脚本
└── README.md                  # 说明文档
```

### 步骤2: 上传到服务器

#### 方式1: 使用scp（推荐）

```bash
# 压缩整个目录
cd /path/to/enterprise-ai-platform
tar -czf docker-images-export.tar.gz docker-images-export/

# 上传到服务器
scp docker-images-export.tar.gz user@server:/tmp/

# 在服务器上解压
ssh user@server
cd /tmp
tar -xzf docker-images-export.tar.gz
```

#### 方式2: 使用Git LFS（如果镜像文件很大）

```bash
# 安装Git LFS
git lfs install

# 添加镜像文件到Git LFS
cd docker-images-export
git lfs track "*.tar.gz"
git add .gitattributes
git add images/*.tar.gz
git commit -m "Add Docker images for offline deployment"
git push

# 在服务器上
git lfs pull
```

#### 方式3: 使用rsync（适合大文件）

```bash
rsync -avz --progress docker-images-export/ user@server:/tmp/docker-images-export/
```

### 步骤3: 在服务器上导入镜像

```bash
# 进入镜像目录
cd /tmp/docker-images-export

# 运行导入脚本
bash load-images.sh
```

这将：
- 读取镜像清单
- 解压并导入所有镜像
- 验证导入结果

### 步骤4: 部署项目

```bash
# 1. 确保项目代码已克隆
cd /opt/enterprise-ai-platform

# 2. 使用离线模式部署
bash scripts/deployment/deploy-server.sh --offline
```

离线模式特点：
- 跳过所有镜像拉取操作
- 直接使用本地已导入的镜像
- 构建应用镜像（如果需要）
- 启动所有服务

## 完整示例

### 本地操作

```bash
# 1. 导出镜像
cd /path/to/enterprise-ai-platform
bash scripts/deployment/export-images.sh

# 2. 压缩
tar -czf docker-images-export.tar.gz docker-images-export/

# 3. 上传（假设服务器IP为192.168.1.100）
scp docker-images-export.tar.gz root@192.168.1.100:/tmp/
```

### 服务器操作

```bash
# 1. 解压镜像
cd /tmp
tar -xzf docker-images-export.tar.gz

# 2. 导入镜像
cd docker-images-export
bash load-images.sh

# 3. 克隆项目代码（如果还没有）
cd /opt
git clone https://github.com/PMLiuyubin/enterprise-ai-platform.git
cd enterprise-ai-platform

# 4. 配置环境变量
cp env.example .env
# 编辑 .env 文件

# 5. 离线部署
bash scripts/deployment/deploy-server.sh --offline
```

## 镜像列表

导出的镜像包括：

**数据库服务:**
- `postgres:15` - PostgreSQL数据库
- `redis:7-alpine` - Redis缓存
- `rediscommander/redis-commander:latest` - Redis管理界面

**应用服务:**
- 从 `docker-compose.yml` 和 `docker-compose.prod.yml` 中读取的所有镜像

## 注意事项

1. **镜像大小**: 镜像文件可能很大（几GB），确保有足够的磁盘空间
2. **网络要求**: 本地需要有网络连接来拉取镜像
3. **版本一致性**: 确保导出的镜像版本与docker-compose文件中的版本一致
4. **存储空间**: 服务器需要足够的空间存储镜像文件和解压后的镜像

## 故障排查

### 问题1: 导出镜像失败

```bash
# 检查Docker是否运行
docker ps

# 检查镜像是否存在
docker images

# 手动拉取镜像
docker pull postgres:15
```

### 问题2: 导入镜像失败

```bash
# 检查磁盘空间
df -h

# 检查Docker是否运行
docker ps

# 手动导入单个镜像
gunzip -c images/postgres_15.tar.gz | docker load
```

### 问题3: 部署时找不到镜像

```bash
# 检查镜像是否已导入
docker images

# 检查镜像标签
docker images | grep postgres

# 如果标签不匹配，手动打标签
docker tag registry.cn-hangzhou.aliyuncs.com/acs/postgres:15 postgres:15
```

## 更新镜像

如果需要更新镜像：

```bash
# 1. 在本地重新导出
bash scripts/deployment/export-images.sh

# 2. 上传新镜像到服务器

# 3. 在服务器上重新导入
bash load-images.sh

# 4. 重启服务
docker compose down
docker compose up -d
```

## 相关文档

- [部署指南](DEPLOYMENT_GUIDE.md)
- [Docker镜像加速器配置](README.md#docker镜像加速器)
- [防火墙配置](FIREWALL_FIX.md)

