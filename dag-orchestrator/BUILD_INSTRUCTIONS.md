# DAG Orchestrator 构建说明

## 网络问题处理

如果遇到SSL连接错误（SSLEOFError），可能是VPN或代理导致的。可以尝试以下方法：

### 方法1：在本地先安装依赖，然后构建

```bash
cd dag-orchestrator
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

### 方法2：使用Docker构建参数

```bash
docker build \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  --build-arg PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
  -f Dockerfile.dev \
  -t dag-orchestrator:dev \
  .
```

### 方法3：临时禁用SSL验证（不推荐，仅用于测试）

修改 `Dockerfile.dev`，在pip install命令前添加：

```dockerfile
ENV PIP_TRUSTED_HOST="pypi.tuna.tsinghua.edu.cn mirrors.aliyun.com pypi.org"
ENV PIP_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
```

### 方法4：使用本地pip缓存

```bash
# 在本地先下载依赖
pip download -r requirements.txt -d ./pip_cache

# 然后在Dockerfile中使用本地缓存
COPY pip_cache /pip_cache
RUN pip install --no-index --find-links /pip_cache -r requirements.txt
```

## 正常构建

如果网络正常，直接运行：

```bash
docker-compose build dag-orchestrator
docker-compose up -d dag-orchestrator
```

## 验证服务

```bash
# 检查服务状态
docker-compose ps dag-orchestrator

# 查看日志
docker-compose logs dag-orchestrator

# 测试健康检查
curl http://localhost:8009/api/v1/health
```











































