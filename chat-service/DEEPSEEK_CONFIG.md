# DeepSeek API 配置指南

本文档说明如何在 Chat Service 中配置和使用 DeepSeek API。

## 📋 配置说明

### 1. 获取 DeepSeek API Key

1. 访问 [DeepSeek 平台](https://platform.deepseek.com)
2. 注册/登录账号
3. 在控制台中创建 API Key
4. 复制 API Key

### 2. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# DeepSeek API 配置（推荐）
DEEPSEEK_API_KEY=your-deepseek-api-key-here
DEEPSEEK_API_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=4096
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TIMEOUT=60.0
```

### 3. 配置参数说明

| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（必需） | - | 从平台获取 |
| `DEEPSEEK_API_URL` | API 端点 | `https://api.deepseek.com/v1` | - |
| `DEEPSEEK_MODEL` | 使用的模型 | `deepseek-chat` | `deepseek-chat`, `deepseek-coder` |
| `DEEPSEEK_MAX_TOKENS` | 最大 token 数 | `4096` | 1-4096 |
| `DEEPSEEK_TEMPERATURE` | 温度参数（控制随机性） | `0.7` | 0.0-2.0 |
| `DEEPSEEK_TIMEOUT` | API 请求超时（秒） | `60.0` | - |

### 4. 向后兼容配置

如果没有设置 `DEEPSEEK_API_KEY`，系统会自动使用以下环境变量（向后兼容）：

- `OPENAI_API_KEY` - API 密钥
- `LLM_BASE_URL` - API 端点
- `LLM_MODEL` - 模型名称

## 🚀 使用方式

### API 端点

**POST** `/api/v1/chat`

**请求体：**
```json
{
  "message": "你好，请介绍一下你自己",
  "conversation_id": "optional-conversation-id",
  "model": "deepseek-chat",
  "metadata": {
    "max_tokens": 2000,
    "temperature": 0.7
  }
}
```

**响应：**
```json
{
  "conversation_id": "conversation-uuid",
  "message": {
    "id": "message-uuid",
    "role": "assistant",
    "content": "你好！我是DeepSeek AI助手...",
    "status": "completed",
    "model": "deepseek-chat",
    "tokens_used": 150,
    "execution_time": 1200
  },
  "suggestions": ["告诉我更多细节", "有什么其他建议吗？"]
}
```

## 🔍 健康检查

**GET** `/health`

返回服务状态和 DeepSeek 配置信息：

```json
{
  "status": "healthy",
  "service": "chat-service",
  "version": "1.0.0",
  "deepseek": {
    "api_key_configured": true,
    "api_key_preview": "sk-1234567...",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "max_tokens": 4096,
    "temperature": 0.7,
    "timeout": 60.0,
    "status": "configured"
  }
}
```

## 📝 功能特性

### ✅ 已实现

- ✅ DeepSeek API 集成
- ✅ 对话历史管理
- ✅ 上下文维护（最近10轮对话）
- ✅ Token 使用统计
- ✅ 执行时间统计
- ✅ 错误处理和降级
- ✅ 配置状态检查

### 🔄 待实现

- ⏳ 流式响应支持
- ⏳ 知识库集成
- ⏳ 多轮对话优化
- ⏳ 对话摘要生成
- ⏳ 消息编辑和删除

## 🛠️ 故障排查

### 问题：API Key 未配置

**症状：** 健康检查显示 `"status": "not_configured"`

**解决：**
1. 检查 `.env` 文件中是否设置了 `DEEPSEEK_API_KEY`
2. 确认 API Key 格式正确（以 `sk-` 开头）
3. 重启服务：`docker compose restart chat-service`

### 问题：API 调用失败

**症状：** 返回错误消息或超时

**解决：**
1. 检查网络连接
2. 验证 API Key 是否有效
3. 检查 API 端点是否正确
4. 查看服务日志：`docker compose logs chat-service`

### 问题：响应超时

**症状：** 请求超时错误

**解决：**
1. 增加 `DEEPSEEK_TIMEOUT` 值
2. 减少 `DEEPSEEK_MAX_TOKENS` 值
3. 检查网络延迟

## 📚 相关文档

- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [Chat Service README](./README.md)
- [项目部署文档](../DEPLOYMENT_SUMMARY.md)


