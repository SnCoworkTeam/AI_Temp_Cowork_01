# 认证服务 (Auth Service)

支持SSL单点登录（SSO）的认证服务，基于OAuth 2.0/OpenID Connect协议。

## 功能特性

- ✅ OAuth 2.0/OpenID Connect集成
- ✅ JWT令牌管理（访问令牌和刷新令牌）
- ✅ Redis缓存用户会话和令牌
- ✅ 统一的用户权限模型
- ✅ 认证中间件
- ✅ 令牌刷新机制
- ✅ 安全的会话管理

## 架构

### 核心组件

1. **SSO客户端** (`src/sso/sso_client.py`)
   - OAuth 2.0授权流程
   - 令牌交换
   - 用户信息获取

2. **JWT管理器** (`src/sso/jwt_manager.py`)
   - 生成访问令牌和刷新令牌
   - 验证令牌
   - 撤销令牌

3. **缓存管理器** (`src/sso/cache_manager.py`)
   - Redis连接管理
   - 用户会话缓存
   - 令牌缓存

4. **认证中间件** (`src/middleware/auth_middleware.py`)
   - JWT令牌验证
   - 用户信息注入
   - 角色权限检查

## API端点

### 认证端点

- `GET /auth/sso/login` - 发起SSO登录
- `GET /auth/sso/callback` - SSO回调处理
- `POST /auth/refresh` - 刷新访问令牌
- `POST /auth/logout` - 登出并清理缓存

### 用户端点

- `GET /users/me` - 获取当前用户信息（需要认证）

### 健康检查

- `GET /health` - 健康检查
- `GET /health/ready` - 就绪检查
- `GET /health/live` - 存活检查

## 配置

### 环境变量

```bash
# 服务配置
PORT=8003
DEBUG=false

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

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 缓存配置（秒）
CACHE_SESSION_TTL=1800      # 30分钟
CACHE_ACCESS_TOKEN_TTL=3600  # 1小时
CACHE_REFRESH_TOKEN_TTL=604800  # 7天
```

## 缓存策略

### 用户会话缓存
- **TTL**: 30分钟
- **键格式**: `session:{session_id}`
- **用途**: 存储用户会话信息

### 访问令牌缓存
- **TTL**: 1小时
- **键格式**: `access_token:{token}`
- **用途**: 快速验证令牌有效性

### 刷新令牌缓存
- **TTL**: 7天
- **键格式**: `refresh_token:{token}`
- **用途**: 刷新访问令牌

## 使用示例

### 1. 发起SSO登录

```bash
curl -X GET "http://localhost:8003/auth/sso/login"
# 会重定向到SSO提供者的授权页面
```

### 2. 刷新令牌

```bash
curl -X POST "http://localhost:8003/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your_refresh_token"
  }'
```

### 3. 获取当前用户信息

```bash
curl -X GET "http://localhost:8003/users/me" \
  -H "Authorization: Bearer your_access_token"
```

### 4. 登出

```bash
curl -X POST "http://localhost:8003/auth/logout" \
  -H "Authorization: Bearer your_access_token"
```

## 安全注意事项

1. **JWT密钥**: 生产环境必须使用强密钥
2. **HTTPS**: 生产环境必须使用HTTPS
3. **Cookie安全**: 设置`secure`和`httponly`标志
4. **状态参数**: 使用随机状态参数防止CSRF攻击
5. **令牌撤销**: 支持令牌撤销机制

## 开发

### 本地运行

```bash
cd auth-service
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8003
```

### Docker运行

```bash
# 开发环境
docker-compose up auth-service

# 生产环境
docker build -f Dockerfile -t auth-service .
docker run -p 8003:8003 auth-service
```

## 依赖

- FastAPI
- PyJWT
- httpx (OAuth客户端)
- redis (缓存)
- python-jose (JWT支持)

## 端口说明

⚠️ **注意**: 默认使用端口8003，因为8002已被workflow-engine使用。如需使用8002，请修改配置并确保workflow-engine使用其他端口。









