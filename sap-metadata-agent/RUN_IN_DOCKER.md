# 在Docker容器内运行语义索引构建

## 说明

由于Docker配置了热加载，`sap-metadata-agent`目录下的所有文件都会自动映射到容器内的`/app/scripts`目录。

## 直接运行命令

### 1. 测试单条数据（推荐先测试）

```bash
docker exec -it enterprise-ai-sap-metadata-agent python /app/scripts/build_semantic_in_docker.py --batch-size 1 --no-resume
```

### 2. 小批量测试

```bash
docker exec -it enterprise-ai-sap-metadata-agent python /app/scripts/build_semantic_in_docker.py --batch-size 10 --no-resume
```

### 3. 正式构建（分批处理）

```bash
docker exec -it enterprise-ai-sap-metadata-agent python /app/scripts/build_semantic_in_docker.py --batch-size 50
```

### 4. 从进度恢复（如果中断）

```bash
docker exec -it enterprise-ai-sap-metadata-agent python /app/scripts/build_semantic_in_docker.py --resume
```

## 参数说明

- `--batch-size N`: 每批处理的元数据数量（默认50）
- `--assets-offset N`: 数据资产起始偏移量
- `--entities-offset N`: 业务实体起始偏移量  
- `--resume`: 从进度文件恢复
- `--no-resume`: 从头开始（忽略进度文件）

## 查看进度

进度文件保存在：`/app/scripts/semantic_build_progress.json`

查看进度：
```bash
docker exec -it enterprise-ai-sap-metadata-agent cat /app/scripts/semantic_build_progress.json
```

## 查看日志

```bash
# 实时查看日志
docker logs -f enterprise-ai-sap-metadata-agent

# 查看最近100行
docker logs --tail 100 enterprise-ai-sap-metadata-agent
```

## 优势

✅ **热加载**: 文件修改后容器内自动更新，无需重启  
✅ **环境稳定**: 所有依赖已安装，不会遇到模块缺失  
✅ **网络稳定**: 使用容器服务名访问，避免localhost问题  
✅ **避免Docker API问题**: 不会触发本地Docker API调用  

## 快速开始

```bash
# 1. 确保容器运行
docker-compose ps sap-metadata-agent

# 2. 测试单条
docker exec -it enterprise-ai-sap-metadata-agent python /app/scripts/build_semantic_in_docker.py --batch-size 1 --no-resume

# 3. 如果成功，开始构建
docker exec -it enterprise-ai-sap-metadata-agent python /app/scripts/build_semantic_in_docker.py --batch-size 50
```


