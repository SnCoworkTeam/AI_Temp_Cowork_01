# 登录问题修复报告

生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## 🔍 问题分析

### 错误信息
```
POST http://localhost:8080/api/auth/login net::ERR_CONNECTION_REFUSED
```

### 根本原因
- web-ui在服务器上运行（43.143.139.197:3000）
- 但环境变量配置为 `http://localhost:8080`
- 浏览器访问服务器上的web-ui时，尝试连接 `localhost:8080`（用户的本地机器）
- 导致连接被拒绝

## ✅ 已修复的问题

### 1. 更新docker-compose.yml配置
已将web-ui的环境变量从 `localhost` 改为服务器IP `43.143.139.197`：

- ✅ `NEXT_PUBLIC_API_GATEWAY_URL`: `http://localhost:8080` → `http://43.143.139.197:8080`
- ✅ `NEXT_PUBLIC_MCP_GATEWAY_URL`: `http://localhost:8001` → `http://43.143.139.197:8001`
- ✅ `NEXT_PUBLIC_WORKFLOW_ENGINE_URL`: `http://localhost:8002` → `http://43.143.139.197:8002`
- ✅ `NEXT_PUBLIC_AUTH_SERVICE_URL`: `http://localhost:8080/api/auth` → `http://43.143.139.197:8080/api/auth`
- ✅ `NEXT_PUBLIC_KNOWLEDGE_BASE_URL`: `http://localhost:8004` → `http://43.143.139.197:8004`
- ✅ `NEXT_PUBLIC_METADATA_SERVICE_URL`: `http://localhost:8005` → `http://43.143.139.197:8005`
- ✅ `NEXT_PUBLIC_CONFIG_CENTER_URL`: `http://localhost:8080/api/config` → `http://43.143.139.197:8080/api/config`
- ✅ `NEXT_PUBLIC_AGENT_SERVICE_URL`: `http://localhost:8010` → `http://43.143.139.197:8010`
- ✅ `NEXT_PUBLIC_AGENT_ORCHESTRATOR_URL`: `http://localhost:8011` → `http://43.143.139.197:8011`

### 2. 上传修复后的配置
- ✅ docker-compose.yml 已上传到服务器

### 3. 重启web-ui服务
- ✅ web-ui 已重启以应用新配置

## 🔧 验证步骤

### 1. 清除浏览器缓存
**重要！** 必须清除缓存才能看到新配置：
- 按 `Ctrl+Shift+Delete`
- 选择"缓存的图片和文件"
- 点击"清除数据"

### 2. 强制刷新页面
- Windows: `Ctrl+F5`
- Mac: `Cmd+Shift+R`

### 3. 使用无痕模式测试
- Chrome/Edge: `Ctrl+Shift+N`
- Firefox: `Ctrl+Shift+P`

### 4. 检查网络请求
打开浏览器开发者工具（F12）→ Network标签，查看登录请求的URL应该是：
- ✅ `http://43.143.139.197:8080/api/auth/login`
- ❌ 不应该再是 `http://localhost:8080/api/auth/login`

## 📝 如果仍然有问题

### 检查服务状态
```bash
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
sudo docker compose ps
```

### 检查API Gateway是否可访问
```bash
# 从服务器内部
curl http://api-gateway:8080/health

# 从外部（应该可以访问）
curl http://43.143.139.197:8080/health
```

### 检查web-ui环境变量
```bash
sudo docker compose exec web-ui printenv | grep NEXT_PUBLIC
```

### 查看web-ui日志
```bash
sudo docker compose logs web-ui --tail=50
```

## ✅ 总结

- ✅ **配置已修复** - 所有URL已从localhost改为服务器IP
- ✅ **配置已上传** - docker-compose.yml已更新到服务器
- ✅ **服务已重启** - web-ui已重启应用新配置
- 💡 **清除缓存** - 必须清除浏览器缓存才能生效

**修复完成！请清除浏览器缓存后重新尝试登录。**

