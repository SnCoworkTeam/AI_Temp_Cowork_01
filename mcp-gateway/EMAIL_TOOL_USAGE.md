# 邮件发送工具使用指南

## 📋 概述

`send_email` 是一个MCP工具，用于发送电子邮件。支持文本和HTML格式，可以添加附件、抄送和密送。

## 🔧 配置

在使用邮件工具之前，需要配置SMTP服务器信息。可以通过环境变量或配置文件设置：

### 必需配置

```bash
# SMTP服务器地址
SMTP_SERVER=smtp.gmail.com

# SMTP端口（通常587用于TLS，465用于SSL）
SMTP_PORT=587

# SMTP用户名（通常是邮箱地址）
SMTP_USERNAME=your-email@gmail.com

# SMTP密码（对于Gmail，需要使用应用专用密码）
SMTP_PASSWORD=your-app-password
```

### 可选配置

```bash
# 默认发件人邮箱（如果不指定from_email参数）
SMTP_FROM_EMAIL=your-email@gmail.com

# 是否使用TLS（默认true）
SMTP_USE_TLS=true

# 是否使用SSL（默认false，如果使用465端口，设置为true）
SMTP_USE_SSL=false
```

### Gmail配置示例

对于Gmail，需要：
1. 启用两步验证
2. 生成应用专用密码（不是普通密码）
3. 使用以下配置：

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

### 其他常见SMTP服务器配置

#### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

#### 企业邮箱（Exchange）
```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

#### 自定义SMTP服务器
```bash
SMTP_SERVER=mail.yourcompany.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

## 📝 工具定义

### 工具名称
`send_email`

### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `to_emails` | string/array | ✅ | 收件人邮箱地址。可以是字符串（多个邮箱用逗号或分号分隔）或数组 |
| `subject` | string | ✅ | 邮件主题 |
| `body` | string | ✅ | 邮件正文内容 |
| `body_type` | string | ❌ | 正文类型：`text`（纯文本）或`html`（HTML格式），默认`text` |
| `from_email` | string | ❌ | 发件人邮箱地址（可选，默认使用配置的发件人） |
| `cc_emails` | string/array | ❌ | 抄送邮箱地址 |
| `bcc_emails` | string/array | ❌ | 密送邮箱地址 |
| `attachments` | array | ❌ | 附件列表 |
| `reply_to` | string | ❌ | 回复邮箱地址 |

### 附件格式

每个附件对象包含：
- `filename`: 附件文件名（必需）
- `content`: 附件内容，可以是字符串或base64编码（必需）
- `content_type`: 附件内容类型，默认`application/octet-stream`（可选）

## 💡 使用示例

### 示例1: 发送简单文本邮件

```python
{
    "tool_name": "send_email",
    "parameters": {
        "to_emails": "user@example.com",
        "subject": "测试邮件",
        "body": "这是一封测试邮件。"
    }
}
```

### 示例2: 发送HTML格式邮件

```python
{
    "tool_name": "send_email",
    "parameters": {
        "to_emails": ["user1@example.com", "user2@example.com"],
        "subject": "HTML邮件",
        "body": "<h1>标题</h1><p>这是HTML格式的邮件内容。</p>",
        "body_type": "html"
    }
}
```

### 示例3: 发送带抄送和密送的邮件

```python
{
    "tool_name": "send_email",
    "parameters": {
        "to_emails": "user@example.com",
        "cc_emails": "cc1@example.com,cc2@example.com",
        "bcc_emails": ["bcc@example.com"],
        "subject": "带抄送的邮件",
        "body": "邮件正文"
    }
}
```

### 示例4: 发送带附件的邮件

```python
{
    "tool_name": "send_email",
    "parameters": {
        "to_emails": "user@example.com",
        "subject": "带附件的邮件",
        "body": "请查看附件。",
        "attachments": [
            {
                "filename": "report.txt",
                "content": "这是附件内容",
                "content_type": "text/plain"
            },
            {
                "filename": "data.json",
                "content": '{"key": "value"}',
                "content_type": "application/json"
            }
        ]
    }
}
```

### 示例5: 通过API调用

```bash
curl -X POST http://localhost:8001/api/tools/send_email/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "to_emails": "user@example.com",
      "subject": "API测试邮件",
      "body": "这是通过API发送的邮件。"
    }
  }'
```

## 📤 返回结果

### 成功响应

```json
{
    "success": true,
    "message": "邮件发送成功",
    "to": ["user@example.com"],
    "subject": "测试邮件",
    "sent_at": "2025-01-27T10:30:00",
    "recipient_count": 1
}
```

### 失败响应

```json
{
    "success": false,
    "error": "SMTP认证失败: ...",
    "error_code": "SMTP_AUTH_ERROR"
}
```

## ⚠️ 错误代码

| 错误代码 | 说明 | 解决方案 |
|---------|------|---------|
| `SMTP_AUTH_ERROR` | SMTP认证失败 | 检查用户名和密码是否正确 |
| `SMTP_ERROR` | SMTP服务器错误 | 检查SMTP服务器地址和端口 |
| `EMAIL_SEND_ERROR` | 其他发送错误 | 查看错误详情 |

## 🔒 安全注意事项

1. **密码安全**: 不要在代码中硬编码密码，使用环境变量或密钥管理服务
2. **应用专用密码**: 对于Gmail等邮箱，使用应用专用密码而不是账户密码
3. **TLS/SSL**: 建议始终使用TLS或SSL加密连接
4. **附件大小**: 注意附件大小限制，避免发送过大的附件
5. **收件人验证**: 在生产环境中，建议验证收件人邮箱格式

## 🧪 测试

### 测试配置

在测试环境中，可以使用测试SMTP服务器，如：
- [Mailtrap](https://mailtrap.io/) - 用于开发和测试
- [MailHog](https://github.com/mailhog/MailHog) - 本地测试服务器

### 测试示例

```python
# 使用Mailtrap测试
SMTP_SERVER=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=your-mailtrap-username
SMTP_PASSWORD=your-mailtrap-password
```

## 📚 相关文档

- [Python smtplib文档](https://docs.python.org/3/library/smtplib.html)
- [email包文档](https://docs.python.org/3/library/email.html)
- [MCP工具开发指南](../docs/MCP_TOOL_DEVELOPMENT.md)

## 🐛 故障排除

### 问题1: SMTP认证失败

**原因**: 用户名或密码错误，或未启用应用专用密码

**解决方案**:
- 检查用户名和密码是否正确
- 对于Gmail，确保使用应用专用密码
- 检查是否启用了两步验证

### 问题2: 连接超时

**原因**: SMTP服务器地址或端口错误，或防火墙阻止

**解决方案**:
- 检查SMTP服务器地址和端口
- 检查网络连接和防火墙设置
- 尝试使用不同的端口（587或465）

### 问题3: 邮件被标记为垃圾邮件

**原因**: SPF、DKIM或DMARC配置问题

**解决方案**:
- 配置SPF记录
- 配置DKIM签名
- 配置DMARC策略
- 使用企业邮箱服务

## 📞 支持

如有问题，请查看：
- 工具日志：`mcp-gateway/logs/`
- 系统文档：`docs/`
- 问题反馈：创建Issue


