# 在Docker容器内构建语义索引指南

## 为什么在Docker容器内构建？

在Docker容器内执行语义索引构建有以下优势：

1. ✅ **环境一致**: 所有依赖都已安装，不会遇到模块缺失问题
2. ✅ **网络稳定**: 使用容器服务名（如`knowledge-base:8004`）访问，网络更稳定
3. ✅ **避免Docker API问题**: 不会触发本地Docker API版本错误
4. ✅ **隔离性好**: 不受本地环境变量和配置影响
5. ✅ **易于管理**: 可以随时查看容器日志和状态

## 使用方法

### 方法1: 使用便捷脚本（推荐）

**Windows (PowerShell):**
```powershell
cd sap-metadata-agent
.\build_semantic_docker.ps1

# 指定批次大小
.\build_semantic_docker.ps1 --batch-size 100

# 从进度恢复
.\build_semantic_docker.ps1 --resume
```

**Linux/Mac:**
```bash
cd sap-metadata-agent
chmod +x build_semantic_docker.sh
./build_semantic_docker.sh

# 指定批次大小
./build_semantic_docker.sh --batch-size 100

# 从进度恢复
./build_semantic_docker.sh --resume
```

### 方法2: 直接使用docker exec

```bash
# 基本用法
docker exec -it enterprise-ai-sap-metadata-agent python /app/build_semantic_in_docker.py

# 指定批次大小
docker exec -it enterprise-ai-sap-metadata-agent python /app/build_semantic_in_docker.py --batch-size 100

# 从进度恢复
docker exec -it enterprise-ai-sap-metadata-agent python /app/build_semantic_in_docker.py --resume

# 从头开始（忽略进度文件）
docker exec -it enterprise-ai-sap-metadata-agent python /app/build_semantic_in_docker.py --no-resume
```

### 方法3: 进入容器后执行

```bash
# 进入容器
docker exec -it enterprise-ai-sap-metadata-agent bash

# 在容器内执行
cd /app
python build_semantic_in_docker.py --batch-size 50
```

## 参数说明

- `--batch-size N`: 每批处理的元数据数量（默认50）
- `--assets-offset N`: 数据资产起始偏移量（默认0）
- `--entities-offset N`: 业务实体起始偏移量（默认0）
- `--resume`: 从进度文件恢复构建
- `--no-resume`: 不从进度文件恢复（从头开始）

## 进度文件

构建进度会自动保存到容器内的 `/app/semantic_build_progress.json` 文件。

如果构建中断，可以使用 `--resume` 参数继续构建。

## 查看日志

```bash
# 查看容器日志
docker logs -f enterprise-ai-sap-metadata-agent

# 查看最近的日志
docker logs --tail 100 enterprise-ai-sap-metadata-agent
```

## 环境变量

容器内会自动使用以下环境变量（在docker-compose.yml中配置）：

- `METADATA_SERVICE_URL`: 元数据服务URL（默认: `http://metadata-service:8005`）
- `KNOWLEDGE_BASE_URL`: 知识库服务URL（默认: `http://knowledge-base:8004`）
- `SEMANTIC_BATCH_SIZE`: 批次大小（默认: 50）

## 优势对比

| 特性 | 本地执行 | Docker容器内执行 |
|------|---------|-----------------|
| 环境依赖 | 需要安装所有依赖 | ✅ 依赖已安装 |
| 网络访问 | 使用localhost | ✅ 使用容器服务名 |
| Docker API问题 | ❌ 可能遇到 | ✅ 不会遇到 |
| 环境变量影响 | ❌ 可能受影响 | ✅ 隔离环境 |
| 日志查看 | 控制台输出 | ✅ 可通过docker logs查看 |

## 故障排除

### 问题1: 容器未运行

```bash
# 启动容器
docker-compose up -d sap-metadata-agent

# 检查容器状态
docker ps | grep sap-metadata-agent
```

### 问题2: 无法连接到服务

```bash
# 检查服务是否运行
docker ps | grep -E "metadata-service|knowledge-base"

# 检查网络连接（在容器内）
docker exec -it enterprise-ai-sap-metadata-agent ping metadata-service
docker exec -it enterprise-ai-sap-metadata-agent ping knowledge-base
```

### 问题3: 进度文件丢失

如果进度文件丢失，可以手动指定偏移量：

```bash
docker exec -it enterprise-ai-sap-metadata-agent python /app/build_semantic_in_docker.py \
  --assets-offset 1000 \
  --entities-offset 0 \
  --no-resume
```

## 最佳实践

1. **小批量开始**: 先用小批次（如10-20）测试，确认正常后再增加
2. **定期检查**: 使用`--resume`参数定期检查进度
3. **监控资源**: 监控容器CPU和内存使用情况
4. **保存日志**: 将重要构建过程的日志保存下来

## 示例

```bash
# 1. 测试单批（10条）
docker exec -it enterprise-ai-sap-metadata-agent python /app/build_semantic_in_docker.py --batch-size 10 --no-resume

# 2. 如果测试成功，开始正式构建（50条/批）
docker exec -it enterprise-ai-sap-metadata-agent python /app/build_semantic_in_docker.py --batch-size 50

# 3. 如果中断，继续构建
docker exec -it enterprise-ai-sap-metadata-agent python /app/build_semantic_in_docker.py --resume
```

## 相关文件

- `build_semantic_in_docker.py` - 容器内构建脚本
- `build_semantic_docker.sh` - Linux/Mac便捷脚本
- `build_semantic_docker.ps1` - Windows便捷脚本
- `docker-compose.yml` - Docker Compose配置


