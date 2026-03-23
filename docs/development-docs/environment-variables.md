# 环境变量配置指南

本文档详细说明企业AI平台所有服务的环境变量配置。

## 目录

- [通用配置](#通用配置)
- [服务配置](#服务配置)
- [数据库配置](#数据库配置)
- [Redis配置](#redis配置)
- [AI服务配置](#ai服务配置)
- [前端配置](#前端配置)
- [配置示例](#配置示例)

## 通用配置

### 调试和日志

```bash
# 调试模式（开发环境）
DEBUG=true

# 日志级别 (critical, error, warning, info, debug, trace)
# 注意：uvicorn 需要小写
LOG_LEVEL=info
```

## 服务配置

### MCP Gateway (端口: 8001)

```bash
# 服务配置
HOST=0.0.0.0
PORT=8001

# CORS配置（逗号分隔）
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# 服务间通信
WORKFLOW_ENGINE_URL=http://workflow-engine:8002
KNOWLEDGE_BASE_URL=http://knowledge-base:8004
METADATA_SERVICE_URL=http://metadata-service:8005
```

### Workflow Engine (端口: 8002)

```bash
# 服务配置
HOST=0.0.0.0
PORT=8002

# CORS配置
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# 服务间通信
MCP_GATEWAY_URL=http://mcp-gateway:8001
KNOWLEDGE_BASE_URL=http://knowledge-base:8004
METADATA_SERVICE_URL=http://metadata-service:8005
```

### Auth Service (端口: 8003)

```bash
# 服务配置
PORT=8003

# SSO配置
SSO_CLIENT_ID=your_client_id
SSO_CLIENT_SECRET=your_client_secret
SSO_AUTHORIZATION_URL=https://sso.example.com/oauth2/authorize
SSO_TOKEN_URL=https://sso.example.com/oauth2/token
SSO_USERINFO_URL=https://sso.example.com/oauth2/userinfo
SSO_REDIRECT_URI=http://localhost:8003/auth/sso/callback
SSO_SCOPES=openid profile email

# JWT配置
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 缓存配置（秒）
CACHE_SESSION_TTL=1800      # 30分钟
CACHE_ACCESS_TOKEN_TTL=3600  # 1小时
CACHE_REFRESH_TOKEN_TTL=604800  # 7天
```

### Knowledge Base (端口: 8004)

```bash
# 服务配置
PORT=8004

# 向量存储配置
VECTOR_STORE_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db

# 嵌入模型配置
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
EMBEDDING_DIMENSION=384

# 文档处理配置
MAX_FILE_SIZE=104857600  # 100MB
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
DOCUMENT_STORAGE_DIR=./documents
```

### Metadata Service (端口: 8005)

```bash
# 服务配置
PORT=8005

# 搜索配置
SEARCH_MAX_RESULTS=100
SEARCH_DEFAULT_LIMIT=20

# 血缘配置
LINEAGE_MAX_DEPTH=10
LINEAGE_CACHE_TTL=3600

# 质量配置
QUALITY_CHECK_INTERVAL=3600
QUALITY_CACHE_TTL=1800
```

## 数据库配置

### PostgreSQL

```bash
# 数据库连接
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=enterprise_ai_platform

# 连接池配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# SQLAlchemy配置
DB_ECHO=false  # 是否打印SQL语句
```

## Redis配置

```bash
# Redis连接
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 连接池配置
REDIS_MAX_CONNECTIONS=50
```

## AI服务配置

### OpenAI

```bash
# OpenAI API配置
OPENAI_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4
# LLM_BASE_URL 不设置，使用OpenAI官方API
```

### DeepSeek

```bash
# DeepSeek API配置（完全兼容OpenAI API格式）
OPENAI_API_KEY=sk-your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

### LangChain

```bash
# LangChain配置
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_TRACING_V2=false  # 是否启用追踪
```

## 前端配置

### Web UI (端口: 3000)

```bash
# 后端服务URL（浏览器访问）
NEXT_PUBLIC_MCP_GATEWAY_URL=http://localhost:8001
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=http://localhost:8002
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8003
NEXT_PUBLIC_KNOWLEDGE_BASE_URL=http://localhost:8004
NEXT_PUBLIC_METADATA_SERVICE_URL=http://localhost:8005

# 认证配置
NEXT_PUBLIC_SSO_ENABLED=true
NEXT_PUBLIC_SSO_CLIENT_ID=your_client_id
```

## 配置示例

### 开发环境 (.env)

完整开发环境配置示例：

```bash
# 通用配置
DEBUG=true
LOG_LEVEL=info

# 数据库配置
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=enterprise_ai_platform

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379

# MCP Gateway
PORT=8001
CORS_ORIGINS=http://localhost:3000

# Workflow Engine
PORT=8002
OPENAI_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# Auth Service
PORT=8003
JWT_SECRET_KEY=dev-secret-key

# Knowledge Base
PORT=8004
VECTOR_STORE_TYPE=chroma

# Metadata Service
PORT=8005

# Web UI
NEXT_PUBLIC_MCP_GATEWAY_URL=http://localhost:8001
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=http://localhost:8002
```

### 生产环境

生产环境配置注意事项：

1. **安全性**:
   - 设置强密码
   - 使用环境变量管理密钥
   - 启用HTTPS

2. **性能**:
   - 调整连接池大小
   - 配置缓存TTL
   - 优化日志级别

3. **监控**:
   - 启用日志收集
   - 配置告警
   - 设置健康检查

## 配置验证

### 检查配置

```bash
# 使用项目提供的检查脚本
./check-env.ps1  # Windows
./check-env.sh   # Linux/Mac
```

### 常见问题

1. **端口冲突**: 确保所有端口未被占用
2. **服务连接**: 检查服务间通信URL是否正确
3. **环境变量**: 确保所有必需变量已设置
4. **日志级别**: 注意uvicorn需要小写日志级别

## 相关文档

- [项目主文档](../../README.md)
- [快速开始指南](./QUICK_START.md)
- [部署指南](./DEPLOYMENT_GUIDE.md)
- [各服务README](../README.md)

