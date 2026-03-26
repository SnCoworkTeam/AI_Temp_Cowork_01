# Middleware模式

## 概述

Middleware模式用于在请求处理链中插入横切关注点，如认证、日志、错误处理等。

## 实现示例

```python
from fastapi import Request
from fastapi.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 验证token
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        # 继续处理请求
        response = await call_next(request)
        return response
```

## 使用场景

- 认证和授权
- 请求日志
- 错误处理
- 速率限制
- CORS处理

## 优势

- 关注点分离
- 代码复用
- 易于维护
- 可组合性









