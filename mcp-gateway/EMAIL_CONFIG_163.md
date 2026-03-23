# 163邮箱SMTP配置说明

## ✅ 已配置的163邮箱信息

- **邮箱地址**: lyb-005@163.com
- **密码**: Liu@bner1983
- **SMTP服务器**: smtp.163.com
- **SMTP端口**: 465 (SSL)
- **测试收件人**: yubin.liu@pcitc.com

## 📧 测试结果

✅ **邮件发送测试成功！**

测试时间：2025-11-25 14:23:57
- 发件人：lyb-005@163.com
- 收件人：yubin.liu@pcitc.com
- 主题：测试邮件 - MCP工具测试

## 🔧 配置方式

### 方式1: 环境变量（推荐）

在 `.env` 文件或系统环境变量中设置：

```bash
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=lyb-005@163.com
SMTP_PASSWORD=Liu@bner1983
SMTP_FROM_EMAIL=lyb-005@163.com
SMTP_USE_TLS=false
SMTP_USE_SSL=true
```

### 方式2: 配置文件

在 `mcp-gateway/src/config.py` 中已添加SMTP配置项，可以通过环境变量覆盖。

## 📝 使用示例

### 通过API调用

```bash
curl -X POST http://localhost:8001/api/tools/send_email/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "to_emails": "yubin.liu@pcitc.com",
      "subject": "测试邮件",
      "body": "这是一封测试邮件。"
    }
  }'
```

### 在代码中使用

```python
from mcp_gateway.src.tools.email_tool import execute_send_email

result = await execute_send_email({
    "to_emails": "yubin.liu@pcitc.com",
    "subject": "测试邮件",
    "body": "邮件内容"
})
```

## ⚠️ 注意事项

1. **163邮箱SMTP服务**: 需要确保163邮箱已开启SMTP服务
2. **授权码**: 如果使用授权码而不是登录密码，请使用授权码作为 `SMTP_PASSWORD`
3. **SSL连接**: 163邮箱使用465端口需要SSL连接（`SMTP_USE_SSL=true`）
4. **安全**: 生产环境中，建议将密码存储在安全的密钥管理服务中，而不是直接写在配置文件中

## 🔍 163邮箱SMTP设置

如果遇到认证问题，请检查：

1. 登录163邮箱网页版
2. 进入"设置" -> "POP3/SMTP/IMAP"
3. 开启"SMTP服务"
4. 如果启用了授权码，使用授权码而不是登录密码

## 📚 相关文档

- [邮件工具使用指南](./EMAIL_TOOL_USAGE.md)
- [MCP工具开发文档](../docs/MCP_TOOL_DEVELOPMENT.md)


