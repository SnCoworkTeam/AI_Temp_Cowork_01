# Chat Service - AI对话服务

企业AI平台的AI对话服务，提供对话管理、消息处理和AI助手对话功能。

## 🚀 功能特性

- ✅ **对话管理**: 创建、查询、更新、删除对话
- ✅ **消息管理**: 发送和接收消息，查看消息历史
- ✅ **AI对话**: 与AI助手进行对话交互
- ✅ **对话归档**: 支持对话归档和恢复
- ✅ **数据库持久化**: 使用PostgreSQL存储对话和消息数据

## 📋 API端点

### 对话管理

- `POST /api/v1/conversations` - 创建新对话
- `GET /api/v1/conversations` - 获取对话列表（支持分页）
- `GET /api/v1/conversations/{id}` - 获取对话详情
- `PATCH /api/v1/conversations/{id}` - 更新对话
- `DELETE /api/v1/conversations/{id}` - 删除对话

### 消息管理

- `POST /api/v1/conversations/{id}/messages` - 添加消息
- `GET /api/v1/conversations/{id}/messages` - 获取消息列表（支持分页）

### 聊天

- `POST /api/v1/chat` - 与AI助手对话
- `GET /api/v1/chat/history/{id}` - 获取聊天历史

### 健康检查

- `GET /api/health` - 健康检查
- `GET /api/health/ready` - 就绪检查
- `GET /api/health/live` - 存活检查

## 🔧 环境变量

```bash
# 服务配置
HOST=0.0.0.0
PORT=8006
DEBUG=false

# 数据库配置
DB_HOST=postgres
DB_PORT=5432
DB_USER=ai_user
DB_PASSWORD=ai_password
DB_NAME=ai_platform
DATABASE_URL=postgresql://ai_user:ai_password@postgres:5432/ai_platform

# JWT配置（用于认证）
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM配置（可选，用于AI对话）
OPENAI_API_KEY=your_openai_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

## 🏗️ 项目结构

```
chat-service/
├── src/
│   ├── main.py              # FastAPI主应用
│   ├── routes/              # API路由
│   │   ├── chat.py          # 聊天路由
│   │   └── conversations.py # 对话管理路由
│   ├── services/            # 业务服务
│   │   └── conversation_service.py # 对话服务
│   ├── repositories/        # 数据访问层
│   │   └── conversation_repository.py # 对话仓库
│   └── models/              # 数据模型
│       └── conversation_models.py # 对话模型
├── requirements.txt         # Python依赖
└── README.md               # 本文档
```

## 🚀 快速开始

### 使用 Docker Compose

```bash
# 启动服务
docker compose up chat-service

# 查看日志
docker compose logs -f chat-service

# 重启服务
docker compose restart chat-service
```

### 本地开发

```bash
cd chat-service
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8006 --reload
```

服务将在 `http://localhost:8006` 启动

## 📝 使用示例

### 创建对话

```bash
curl -X POST http://localhost:8006/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI助手对话",
    "user_id": "user123"
  }'
```

### 发送消息

```bash
curl -X POST http://localhost:8006/api/v1/conversations/{conversation_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好，AI助手",
    "role": "user"
  }'
```

### AI对话

```bash
curl -X POST http://localhost:8006/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv123",
    "message": "什么是人工智能？"
  }'
```

## 🔗 相关服务

- **API Gateway**: `/api/chat/*` → `chat-service:8006`
- **Auth Service**: 认证和授权
- **Knowledge Base**: 知识库搜索集成
- **Agent Service**: 智能体对话集成

## 📚 技术栈

- **FastAPI**: Web框架
- **SQLAlchemy**: ORM框架
- **PostgreSQL**: 数据库
- **Pydantic**: 数据验证
- **Uvicorn**: ASGI服务器

## 📝 注意事项

1. **端口**: 默认使用端口8006，确保该端口未被占用
2. **数据库**: 需要PostgreSQL数据库运行
3. **认证**: 生产环境需要集成认证服务
4. **AI模型**: 可选，如需AI对话功能需要配置LLM API

## 🎯 后续计划

- [ ] 集成认证服务（JWT验证）
- [ ] 集成实际的AI模型（OpenAI/DeepSeek等）
- [ ] 集成知识库搜索
- [ ] 添加流式响应支持
- [ ] 添加消息编辑和删除功能
- [ ] 添加对话分享功能
