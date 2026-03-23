# JWT令牌黑名单测试指南

## 📋 快速开始

### 1. 运行数据库迁移

```bash
cd database
alembic upgrade head
```

### 2. 验证表结构

```sql
-- 连接到数据库
psql -U postgres -d enterprise_ai_platform

-- 检查表
\d token_blacklist

-- 检查索引
\di token_blacklist*
```

### 3. 运行测试

```bash
cd auth-service
pytest tests/test_token_blacklist.py -v
```

---

## 🧪 测试用例说明

### 测试用例1: 添加令牌到黑名单

**目的**: 验证令牌可以成功添加到黑名单

**步骤**:
1. 创建测试令牌
2. 添加到黑名单
3. 验证令牌已在黑名单中

**预期结果**: 令牌成功添加到黑名单，查询返回True

### 测试用例2: 验证令牌时检查黑名单

**目的**: 验证已撤销的令牌无法通过验证

**步骤**:
1. 创建有效令牌
2. 验证令牌（应该通过）
3. 添加到黑名单
4. 再次验证令牌（应该失败）

**预期结果**: 第一次验证通过，第二次验证失败

### 测试用例3: 登出时撤销令牌

**目的**: 验证登出时令牌被正确撤销

**步骤**:
1. 用户登录获取令牌
2. 用户登出
3. 验证令牌已在黑名单中

**预期结果**: 登出后令牌被添加到黑名单

### 测试用例4: 密码更改后撤销令牌

**目的**: 验证密码更改后所有令牌被撤销

**步骤**:
1. 用户登录获取令牌
2. 用户更改密码
3. 验证旧令牌无法使用

**预期结果**: 密码更改后旧令牌无法使用

### 测试用例5: 性能测试

**目的**: 验证黑名单查询性能

**步骤**:
1. 添加测试令牌到黑名单
2. 执行多次查询
3. 计算平均查询时间

**预期结果**: 平均查询时间 < 100ms

### 测试用例6: 并发测试

**目的**: 验证并发场景下的黑名单操作

**步骤**:
1. 添加多个令牌到黑名单
2. 并发检查这些令牌
3. 验证所有结果正确

**预期结果**: 所有并发查询返回正确结果

---

## 🔍 手动测试步骤

### 1. 使用curl测试登出功能

```bash
# 1. 登录获取令牌
curl -X POST http://localhost:8003/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# 保存返回的access_token

# 2. 使用令牌访问受保护资源
curl -X GET http://localhost:8003/auth/me \
  -H "Authorization: Bearer <access_token>"

# 3. 登出
curl -X POST http://localhost:8003/auth/logout \
  -H "Authorization: Bearer <access_token>"

# 4. 再次使用令牌访问（应该失败）
curl -X GET http://localhost:8003/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 2. 使用Python脚本测试

```python
import requests
import json

BASE_URL = "http://localhost:8003"

# 登录
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "testuser", "password": "testpass"}
)
tokens = response.json()
access_token = tokens["access_token"]

# 访问受保护资源
response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(f"Before logout: {response.status_code}")

# 登出
response = requests.post(
    f"{BASE_URL}/auth/logout",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(f"Logout: {response.status_code}")

# 再次访问（应该失败）
response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(f"After logout: {response.status_code}")  # 应该是401
```

---

## 📊 健康检查

### 检查黑名单服务健康状态

```bash
curl http://localhost:8003/health/blacklist
```

**预期响应**:
```json
{
  "status": "healthy",
  "service": "token_blacklist",
  "components": {
    "redis": "healthy",
    "database": "healthy",
    "repository": "healthy"
  },
  "timestamp": "2024-01-XXT..."
}
```

---

## 🔧 故障排查

### 问题1: 迁移失败

**错误**: `relation "token_blacklist" does not exist`

**解决方案**:
1. 检查迁移脚本是否正确
2. 确认数据库连接配置
3. 手动运行迁移: `alembic upgrade head`

### 问题2: Redis连接失败

**错误**: `Redis connection failed`

**解决方案**:
1. 检查Redis服务是否运行
2. 验证Redis配置（REDIS_HOST, REDIS_PORT）
3. 检查网络连接

### 问题3: 令牌验证失败

**错误**: 已撤销的令牌仍然可以通过验证

**可能原因**:
1. 黑名单检查未启用（未使用verify_token_async）
2. 数据库会话未传递
3. Redis缓存未同步

**解决方案**:
1. 确保使用`verify_token_async()`并传递`db_session`
2. 检查黑名单记录是否已创建
3. 清除Redis缓存并重试

---

## 📈 性能监控

### 监控指标

建议监控以下指标：
- 黑名单查询次数
- 平均查询时间
- Redis缓存命中率
- 数据库查询性能
- 令牌撤销频率

### 日志查看

```bash
# 查看黑名单相关日志
tail -f logs/auth-service.log | grep -i blacklist

# 查看错误日志
tail -f logs/auth-service.log | grep -i error
```

---

## ✅ 验证清单

- [ ] 数据库迁移成功执行
- [ ] 表结构和索引正确创建
- [ ] 基本功能测试通过
- [ ] 性能测试通过
- [ ] 并发测试通过
- [ ] 健康检查端点正常
- [ ] 日志记录正常
- [ ] 错误处理正常

---

**测试指南版本**: 1.0  
**最后更新**: 2024-01-XX

