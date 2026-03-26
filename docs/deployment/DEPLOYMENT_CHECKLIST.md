# 快速部署执行清单

## 前置检查

- [ ] 确认已通过 `remote.ssh` 连接到服务器
- [ ] 确认在项目目录 `/opt/enterprise-ai-platform`

## 执行步骤

### 1. 备份数据库（重要！）

```bash
cd /opt/enterprise-ai-platform
docker-compose exec postgres pg_dump -U postgres enterprise_ai_platform > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. 更新代码

```bash
# 如果使用Git
git pull

# 或者手动上传以下文件到服务器：
# - workflow-engine/src/models/workflow_models.py
# - database/src/models/chat_models.py
# - database/src/models/__init__.py
# - database/src/models/user_models.py
# - database/src/migrations/versions/006_add_conversation_tables.py
# - shared_libs/schemas/chat_schemas.py
# - chat-service/ (整个目录)
# - docker-compose.yml
```

### 3. 运行数据库迁移

```bash
# 连接到数据库并执行迁移
docker-compose exec postgres psql -U postgres -d enterprise_ai_platform <<EOF
-- 创建conversations表
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL DEFAULT '新对话',
    description TEXT,
    is_archived BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS ix_conversations_is_archived ON conversations(is_archived);
CREATE INDEX IF NOT EXISTS ix_conversations_created_at ON conversations(created_at);

-- 创建枚举类型
DO \$\$ BEGIN
    CREATE TYPE messagerole AS ENUM ('user', 'assistant', 'system');
EXCEPTION
    WHEN duplicate_object THEN null;
END \$\$;

DO \$\$ BEGIN
    CREATE TYPE messagestatus AS ENUM ('pending', 'processing', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END \$\$;

-- 创建messages表
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role messagerole NOT NULL,
    content TEXT NOT NULL,
    status messagestatus NOT NULL DEFAULT 'completed',
    model VARCHAR(100),
    tokens_used INTEGER,
    execution_time INTEGER,
    tool_calls JSONB,
    sources JSONB,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS ix_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS ix_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages(created_at);
EOF
```

### 4. 构建和启动chat-service

```bash
# 构建服务
docker-compose build chat-service

# 启动服务
docker-compose up -d chat-service

# 等待服务启动（约30秒）
sleep 30
```

### 5. 重启workflow-engine

```bash
# 重启workflow-engine以应用模型修复
docker-compose restart workflow-engine

# 等待服务启动
sleep 15
```

### 6. 验证服务状态

```bash
# 检查所有服务状态
docker-compose ps

# 检查chat-service健康状态
curl http://localhost:8006/health

# 检查workflow-engine健康状态
curl http://localhost:8002/api/health

# 查看chat-service日志
docker-compose logs --tail=50 chat-service
```

### 7. 功能测试

```bash
# 测试1: 创建对话
curl -X POST http://localhost:8006/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "测试对话", "description": "功能验证"}'

# 测试2: 发送聊天消息
curl -X POST http://localhost:8006/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，AI助手！"}'

# 测试3: 测试工作流保存
curl -X POST http://localhost:8002/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": {
      "name": "测试工作流",
      "description": "验证修复",
      "nodes": [{
        "id": "node-1",
        "type": "start",
        "name": "开始",
        "position": {"x": 100, "y": 100},
        "data": {}
      }],
      "connections": [],
      "start_node_id": "node-1"
    },
    "overwrite": false
  }'
```

## 预期结果

✅ 所有服务状态显示为 "Up (healthy)"
✅ 健康检查返回 200 OK
✅ 测试1返回 201 Created with conversation_id
✅ 测试2返回 200 OK with AI response
✅ 测试3返回 201 Created with workflow_id

## 回滚步骤（如果出现问题）

```bash
# 停止chat-service
docker-compose stop chat-service

# 回滚数据库（如果需要）
docker-compose exec postgres psql -U postgres enterprise_ai_platform < backup_YYYYMMDD_HHMMSS.sql

# 恢复workflow-engine到之前的版本
git checkout <previous-commit> workflow-engine/src/models/workflow_models.py
docker-compose restart workflow-engine
```

## 故障排查

### 如果chat-service无法启动

```bash
# 查看详细日志
docker-compose logs chat-service

# 检查数据库连接
docker-compose exec postgres psql -U postgres -d enterprise_ai_platform -c "\dt"

# 检查端口占用
netstat -tulpn | grep 8006
```

### 如果workflow-engine出现问题

```bash
# 查看日志
docker-compose logs workflow-engine

# 检查模型导入
docker-compose exec workflow-engine python -c "from src.models.workflow_models import WorkflowNode; print('OK')"
```

### 如果数据库迁移失败

```bash
# 检查表是否存在
docker-compose exec postgres psql -U postgres -d enterprise_ai_platform -c "\dt conversations"

# 手动创建表（如果需要）
docker-compose exec postgres psql -U postgres -d enterprise_ai_platform -f /path/to/006_add_conversation_tables.sql
```

## 联系支持

如遇到问题：
1. 保存错误日志：`docker-compose logs > error_logs.txt`
2. 记录执行的步骤
3. 提供服务状态：`docker-compose ps > service_status.txt`

---

**执行人员**: _____________
**执行日期**: _____________
**执行结果**: [ ] 成功 [ ] 失败
**备注**: _____________
