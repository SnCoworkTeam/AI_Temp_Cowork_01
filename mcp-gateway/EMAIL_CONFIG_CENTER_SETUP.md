# 邮件配置中心设置指南

## 📋 概述

邮件发送工具的SMTP配置已集成到配置中心，支持从配置中心统一管理邮件配置。

## 🔧 配置方式

### 方式1: 通过配置中心API（推荐）

使用提供的脚本将SMTP配置添加到配置中心：

```bash
cd mcp-gateway
python setup_smtp_config.py
```

### 方式2: 手动通过API添加

```bash
# 添加SMTP服务器配置
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "smtp.server",
    "value": "smtp.163.com",
    "description": "SMTP服务器地址（163邮箱）",
    "environment": "default"
  }'

# 添加SMTP端口配置
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "smtp.port",
    "value": 465,
    "description": "SMTP端口（163邮箱使用SSL，端口465）",
    "environment": "default"
  }'

# 添加SMTP用户名配置
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "smtp.username",
    "value": "lyb-005@163.com",
    "description": "SMTP用户名（163邮箱地址）",
    "environment": "default"
  }'

# 添加SMTP密码配置
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "smtp.password",
    "value": "Liu@bner1983",
    "description": "SMTP密码（163邮箱密码）",
    "environment": "default"
  }'

# 添加默认发件人配置
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "smtp.from_email",
    "value": "lyb-005@163.com",
    "description": "默认发件人邮箱地址",
    "environment": "default"
  }'

# 添加SSL配置
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "smtp.use_ssl",
    "value": true,
    "description": "是否使用SSL（163邮箱使用SSL）",
    "environment": "default"
  }'

# 添加TLS配置
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "smtp.use_tls",
    "value": false,
    "description": "是否使用TLS（163邮箱使用SSL，不需要TLS）",
    "environment": "default"
  }'
```

### 方式3: 环境变量（降级方案）

如果配置中心不可用，工具会自动降级到环境变量：

```bash
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=lyb-005@163.com
SMTP_PASSWORD=Liu@bner1983
SMTP_FROM_EMAIL=lyb-005@163.com
SMTP_USE_TLS=false
SMTP_USE_SSL=true
```

## 📊 配置读取优先级

1. **配置中心**（优先）
   - 通过 `ConfigClient` 从配置中心读取
   - 配置键：`smtp.server`, `smtp.port`, `smtp.username`, `smtp.password`, `smtp.from_email`, `smtp.use_tls`, `smtp.use_ssl`

2. **环境变量**（降级方案）
   - 如果配置中心不可用，从环境变量读取
   - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS`, `SMTP_USE_SSL`

3. **配置文件**（最后降级）
   - 从 `mcp-gateway/src/config.py` 的 `Settings` 类读取默认值

## 🔍 配置中心配置项

### 已配置的163邮箱信息

| 配置键 | 值 | 说明 |
|--------|-----|------|
| `smtp.server` | `smtp.163.com` | SMTP服务器地址 |
| `smtp.port` | `465` | SMTP端口（SSL） |
| `smtp.username` | `lyb-005@163.com` | SMTP用户名 |
| `smtp.password` | `Liu@bner1983` | SMTP密码 |
| `smtp.from_email` | `lyb-005@163.com` | 默认发件人 |
| `smtp.use_tls` | `false` | 不使用TLS |
| `smtp.use_ssl` | `true` | 使用SSL |

## ✅ 验证配置

### 1. 检查配置中心中的配置

```bash
# 列出所有配置
curl http://localhost:8090/api/configs?environment=default

# 获取特定配置
curl http://localhost:8090/api/config/smtp.server?environment=default
```

### 2. 测试邮件发送

```bash
cd mcp-gateway
python test_email_simple.py
```

## 🔄 配置更新

配置中心支持配置动态更新，无需重启服务：

1. 通过API更新配置
2. 配置中心会发布配置更新事件
3. 服务可以监听配置更新并自动刷新（需要实现监听逻辑）

## 📝 代码实现

邮件工具已更新为优先从配置中心读取配置：

```python
# 从配置中心或环境变量获取SMTP配置
smtp_config = await _get_smtp_config()

# 使用配置
smtp_server = smtp_config.get("server")
smtp_port = smtp_config.get("port")
# ...
```

## 🎯 优势

1. **集中管理**: 所有配置在配置中心统一管理
2. **环境隔离**: 支持不同环境（dev, test, prod）的配置
3. **版本控制**: 配置中心支持配置版本管理
4. **动态更新**: 支持配置动态更新（需要实现监听）
5. **降级方案**: 配置中心不可用时自动降级到环境变量

## 📚 相关文档

- [配置中心文档](../CONFIG_CENTER_MIGRATION.md)
- [邮件工具使用指南](./EMAIL_TOOL_USAGE.md)
- [163邮箱配置说明](./EMAIL_CONFIG_163.md)


