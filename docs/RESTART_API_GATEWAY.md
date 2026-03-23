# 重启 API Gateway 以应用路由修复

## 修复内容

1. ✅ 添加了 `/api/v1/dynamic-workflow/{path:path}` 路由
2. ✅ 删除了重复的路由定义代码
3. ✅ 配置了流式请求支持

## 重启步骤

### 方法1: Docker Compose（推荐）
```bash
docker-compose restart api-gateway
```

### 方法2: 直接重启服务
```bash
cd api-gateway
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

### 方法3: 如果使用 systemd 或其他进程管理器
```bash
sudo systemctl restart api-gateway
# 或
pm2 restart api-gateway
```

## 验证修复

重启后，检查以下内容：

1. **API Gateway 日志**应该显示：
   ```
   API Gateway started successfully on 0.0.0.0:8080
   ```

2. **测试动态工作流路由**：
   ```bash
   curl -X POST http://localhost:8080/api/v1/dynamic-workflow/execute \
     -H "Content-Type: application/json" \
     -d '{"user_input": "测试", "context": {}}'
   ```

3. **前端测试**：
   - 在聊天界面发送消息
   - 应该能够正常路由到 agent-service
   - 不再出现 404 错误

## 注意事项

- 确保 `agent-service` 服务正在运行
- 确保服务发现配置正确
- 如果仍有问题，检查 API Gateway 日志中的错误信息


