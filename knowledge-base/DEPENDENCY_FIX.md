# Knowledge Base 依赖问题修复指南

## 问题描述

服务启动时出现以下警告：
```
sentence-transformers not available, using mock embeddings
weaviate-client not available
```

## 原因分析

1. **sentence-transformers 未正确安装**
   - 可能原因：torch 安装失败或版本不兼容
   - sentence-transformers 需要 torch 作为依赖

2. **weaviate-client 未正确安装**
   - 可能原因：包名或导入方式问题
   - weaviate-client 包导入时使用 `import weaviate`

## 解决方案

### 方案1：在容器内重新安装依赖（临时解决）

```bash
# 进入容器
docker exec -it enterprise-ai-knowledge-base bash

# 重新安装依赖
pip install --upgrade pip
pip install sentence-transformers==2.2.2 torch>=2.0.0 transformers>=4.30.0
pip install weaviate-client>=3.25.0

# 验证安装
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
python -c "import weaviate; print('OK')"
```

### 方案2：重建 Docker 镜像（推荐）

```bash
# 停止服务
docker compose stop knowledge-base

# 删除旧镜像
docker compose rm -f knowledge-base

# 重建镜像（强制重新安装依赖）
docker compose build --no-cache knowledge-base

# 启动服务
docker compose up -d knowledge-base

# 查看日志
docker compose logs -f knowledge-base
```

### 方案3：检查并修复 requirements.txt

确保 `knowledge-base/requirements.txt` 包含：

```txt
sentence-transformers==2.2.2
torch>=2.0.0
transformers>=4.30.0
weaviate-client>=3.25.0
```

### 方案4：使用国内镜像加速安装

如果网络问题导致安装失败，可以在 Dockerfile.dev 中使用国内镜像：

```dockerfile
# 在 Dockerfile.dev 中已经配置了清华镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## 验证修复

修复后，检查日志应该不再出现警告：

```bash
docker compose logs knowledge-base | grep -i "sentence-transformers\|weaviate"
```

应该看到：
- ✅ 没有 "not available" 警告
- ✅ 或者看到 "Embedding model loaded" 信息

## 常见问题

### Q1: torch 安装失败

**原因**：torch 包很大，可能需要更多时间或空间

**解决**：
```bash
# 在 Dockerfile.dev 中单独安装 torch
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Q2: 内存不足

**原因**：sentence-transformers 和 torch 需要较多内存

**解决**：
- 增加 Docker 内存限制
- 或使用 CPU 版本的 torch（更小）

### Q3: 版本冲突

**原因**：不同依赖包对 torch 版本要求不同

**解决**：
```txt
# 在 requirements.txt 中固定兼容版本
torch==2.0.1
sentence-transformers==2.2.2
transformers==4.30.2
```

## 预防措施

1. **在 Dockerfile 中添加验证步骤**：
```dockerfile
# 验证关键依赖
RUN python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')" && \
    python -c "import weaviate; print('weaviate OK')" || exit 1
```

2. **使用依赖锁定文件**：
```bash
pip freeze > requirements-lock.txt
```

3. **定期更新依赖**：
```bash
pip list --outdated
```

