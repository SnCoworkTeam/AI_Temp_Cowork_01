# Docker构建问题排查指南

## 🔍 问题现象

Docker构建一直卡在0%，没有进展。

## 🎯 可能原因

1. **网络问题** - 无法拉取基础镜像 `python:3.11-slim`
2. **Docker Desktop问题** - API响应慢
3. **构建缓存问题** - 旧的构建缓存导致卡住

## ✅ 解决方案

### 方案1：手动拉取基础镜像（推荐）

```powershell
# 1. 先手动拉取基础镜像
docker pull python:3.11-slim

# 2. 验证镜像是否拉取成功
docker images python:3.11-slim

# 3. 然后再构建服务
docker-compose build vector-coordinator-service
```

### 方案2：清理构建缓存

```powershell
# 清理所有构建缓存
docker builder prune -a

# 清理未使用的镜像
docker image prune -a

# 然后重新构建
docker-compose build --no-cache vector-coordinator-service
```

### 方案3：使用本地测试（不依赖Docker）

如果Docker构建一直有问题，可以先本地测试代码：

```powershell
# 进入服务目录
cd vector-coordinator-service

# 安装依赖（本地）
pip install -r requirements.txt

# 运行本地测试
python test_local.py

# 如果测试通过，说明代码没问题，只是Docker构建的问题
```

### 方案4：简化Dockerfile测试

创建一个最小化的Dockerfile测试：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN echo "Test build"
CMD ["python", "--version"]
```

如果这个简单构建也卡住，说明是Docker本身的问题。

## 🚀 快速验证步骤

1. **测试Docker是否正常**
   ```powershell
   docker run hello-world
   ```

2. **测试网络连接**
   ```powershell
   docker pull python:3.11-slim
   ```

3. **如果网络正常，检查构建日志**
   ```powershell
   docker-compose build vector-coordinator-service --progress=plain 2>&1 | Tee-Object build.log
   ```

## 📝 临时解决方案

如果Docker构建一直有问题，可以：

1. **先本地测试代码** - 使用 `test_local.py`
2. **确认代码没问题后** - 再解决Docker构建问题
3. **或者使用现有服务** - 先测试阶段0的功能

## 🔧 检查清单

- [ ] Docker Desktop是否正常运行？
- [ ] 网络连接是否正常？（VPN已开启）
- [ ] 基础镜像能否手动拉取？
- [ ] 是否有足够的磁盘空间？
- [ ] Docker Desktop资源是否充足？






