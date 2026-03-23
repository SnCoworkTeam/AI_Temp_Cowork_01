# Docker启动指南

## 🔍 问题诊断

检测到Docker API错误：
```
request returned Internal Server Error for API route and version
```

## ✅ 解决方案

### 方案1：重启Docker Desktop（推荐）

1. **完全关闭Docker Desktop**
   - 右键点击系统托盘中的Docker图标
   - 选择 "Quit Docker Desktop"
   - 等待完全退出

2. **重新启动Docker Desktop**
   - 从开始菜单启动Docker Desktop
   - 等待Docker完全启动（系统托盘图标不再闪烁）

3. **验证Docker状态**
   ```powershell
   docker ps
   ```

### 方案2：检查Docker Desktop设置

1. 打开Docker Desktop
2. 进入 Settings > General
3. 确保 "Use the WSL 2 based engine" 已启用（如果使用WSL）
4. 点击 "Apply & Restart"

### 方案3：使用Docker CLI直接启动

如果Docker Desktop已启动但API有问题，可以尝试：

```powershell
# 检查Docker服务状态
docker info

# 如果正常，直接启动服务
docker-compose up -d vector-coordinator-service
```

## 🚀 启动向量协调服务

Docker Desktop正常后，执行：

```powershell
# 1. 构建服务（首次需要）
docker-compose build vector-coordinator-service

# 2. 启动服务
docker-compose up -d vector-coordinator-service

# 3. 查看日志
docker-compose logs -f vector-coordinator-service

# 4. 检查服务状态
docker-compose ps vector-coordinator-service
```

## 📝 测试服务

服务启动后，测试：

```powershell
# 健康检查
curl http://localhost:8020/health

# 或使用PowerShell
Invoke-WebRequest -Uri http://localhost:8020/health
```

## ⚠️ 常见问题

1. **Docker Desktop未启动**
   - 确保Docker Desktop正在运行
   - 检查系统托盘中的Docker图标

2. **WSL2问题**（如果使用WSL）
   - 确保WSL2已安装并更新
   - 运行：`wsl --update`

3. **端口冲突**
   - 检查8020端口是否被占用
   - 运行：`netstat -ano | findstr :8020`






