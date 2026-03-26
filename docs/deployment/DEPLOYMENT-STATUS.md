# 部署状态监控

## 当前状态

- ✅ **SSH 连接**: 已成功连接到服务器 `43.143.139.197`
- ✅ **数据库服务**: PostgreSQL、Redis 已启动并运行正常
- 🔄 **应用服务构建中**: Docker 镜像正在构建（mcp-gateway, workflow-engine, auth-service, knowledge-base, web-ui）

## 监控命令

### 检查服务状态
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker compose ps"
```

### 检查构建进度
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "tail -f /tmp/docker-build.log"
```

### 检查错误日志
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker compose logs --tail=100 2>&1 | grep -iE '(error|failed|exception|traceback)' | head -30"
```

### 检查特定服务日志
```powershell
# MCP Gateway
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker compose logs mcp-gateway --tail=50"

# Workflow Engine
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker compose logs workflow-engine --tail=50"

# Web UI
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker compose logs web-ui --tail=50"
```

## 自动修复循环

如果发现错误，执行以下步骤形成修复闭环：

### 1. 修复本地代码
```powershell
# 在本地修改代码
# 然后提交到 Git
git add .
git commit -m "修复: [描述问题]"
git push origin main
```

### 2. 在服务器上拉取代码
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && git pull origin main"
```

### 3. 重新构建和启动
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker compose down && sudo docker compose up -d --build"
```

### 4. 检查服务状态
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker compose ps"
```

## 健康检查

服务启动后，检查健康状态：

```powershell
# MCP Gateway
curl http://43.143.139.197:8001/api/health

# Workflow Engine
curl http://43.143.139.197:8002/api/health

# Auth Service
curl http://43.143.139.197:8003/health

# Knowledge Base
curl http://43.143.139.197:8004/api/health

# Web UI
curl http://43.143.139.197:3000/api/health
```

## 服务地址

部署成功后，可以通过以下地址访问：

- **Web UI**: http://43.143.139.197:3000
- **MCP Gateway API**: http://43.143.139.197:8001
- **Workflow Engine API**: http://43.143.139.197:8002
- **Auth Service API**: http://43.143.139.197:8003
- **Knowledge Base API**: http://43.143.139.197:8004

## 常见问题

### 问题1: 服务启动失败
**解决方案**: 查看详细日志
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && sudo docker compose logs <service-name>"
```

### 问题2: 端口被占用
**解决方案**: 检查端口占用
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "sudo netstat -tulpn | grep -E '8001|8002|8003|8004|3000'"
```

### 问题3: 环境变量配置错误
**解决方案**: 检查并修复 .env 文件
```powershell
ssh -i "E:\enterprise-ai-platform\enterprise_ai_platform.pem" -o StrictHostKeyChecking=no ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && cat .env"
```

