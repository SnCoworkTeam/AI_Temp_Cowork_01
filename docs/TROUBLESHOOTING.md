# 故障排查指南

## Docker 日志错误

### 错误信息
```
error from daemon in stream: Error grabbing logs: invalid character '\x00' looking for beginning of value
```

### 原因
这是 Docker 日志解析错误，通常发生在：
1. 服务输出了二进制数据或空字符到 stdout/stderr
2. Docker 日志驱动尝试解析 JSON 格式时遇到非文本内容
3. 日志缓冲区包含损坏的数据

### 解决方案

#### 方案1：使用不同的日志查看方式（推荐）

```bash
# 使用 docker logs 而不是 docker-compose logs
docker logs enterprise-ai-memory-service --tail=50

# 或者查看特定服务的日志
docker logs enterprise-ai-memory-service -f

# 查看所有服务的日志（分别查看）
docker ps --format "{{.Names}}" | ForEach-Object { docker logs $_ --tail=20 }
```

#### 方案2：清理并重启服务

```bash
# 停止服务
docker-compose stop memory-service

# 清理日志
docker-compose rm -f memory-service

# 重新启动
docker-compose up -d memory-service

# 查看日志
docker-compose logs -f memory-service
```

#### 方案3：配置日志驱动（如果需要）

创建 `docker-compose.override.yml` 文件：

```yaml
version: '3.8'

services:
  memory-service:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        tag: "{{.Name}}"
```

然后重启服务：
```bash
docker-compose up -d memory-service
```

#### 方案4：检查服务输出

检查是否有服务输出了二进制数据：

```bash
# 检查服务是否正常运行
docker-compose ps

# 测试服务健康状态
curl http://localhost:8013/api/v1/health

# 查看服务标准输出（绕过日志驱动）
docker exec enterprise-ai-memory-service ps aux
```

### 验证服务状态

```bash
# 检查所有服务状态
docker-compose ps

# 检查特定服务健康
curl http://localhost:8013/api/v1/health

# 查看服务进程
docker exec enterprise-ai-memory-service ps aux
```

### 注意事项

1. **这个错误通常不影响服务运行** - 只是查看日志时的问题
2. **服务可能正常运行** - 检查服务健康状态确认
3. **使用 docker logs 代替 docker-compose logs** - 通常可以避免这个问题
4. **如果频繁出现** - 检查服务代码是否有二进制输出

### 相关命令

```bash
# 查看服务状态
docker-compose ps

# 查看特定服务日志（推荐方式）
docker logs enterprise-ai-memory-service --tail=50 -f

# 重启服务
docker-compose restart memory-service

# 查看服务健康检查
docker inspect enterprise-ai-memory-service | grep -A 10 Health
```






























