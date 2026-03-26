# DeepSeek API 配置指南

## 概述

DeepSeek 的 API 完全兼容 OpenAI API 格式，可以直接替换 OpenAI API 使用。本指南说明如何在项目中使用 DeepSeek API。

## DeepSeek API 特点

- ✅ **完全兼容 OpenAI API 格式**：无需修改代码逻辑
- ✅ **高性能模型**：DeepSeek-V3 等模型性能优异
- ✅ **成本效益高**：价格相对较低
- ✅ **简单迁移**：只需修改配置即可

## 配置步骤

### 1. 获取 DeepSeek API Key

1. 访问 [DeepSeek 官网](https://www.deepseek.com/)
2. 注册账号并登录
3. 在控制台获取 API Key

### 2. 更新环境变量

编辑 `.env` 文件（或 `env.example`）：

```bash
# 使用 DeepSeek API
OPENAI_API_KEY=sk-your-deepseek-api-key-here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 或者使用 DeepSeek-V3（如果有）
# LLM_MODEL=deepseek-chat-v3
```

### 3. 配置说明

#### OPENAI_API_KEY
- **作用**: LLM API 密钥（DeepSeek 的 API Key）
- **格式**: `sk-` 开头的字符串
- **获取**: 从 DeepSeek 控制台获取

#### LLM_BASE_URL
- **作用**: LLM 服务的基础 URL
- **DeepSeek**: `https://api.deepseek.com`
- **OpenAI**: 留空或使用默认值（`https://api.openai.com/v1`）

#### LLM_MODEL
- **作用**: 使用的模型名称
- **DeepSeek 推荐模型**:
  - `deepseek-chat` - 通用对话模型
  - `deepseek-chat-v2` - 升级版对话模型
  - `deepseek-chat-v3` - 最新版对话模型（如果可用）
- **OpenAI 模型**: `gpt-4`, `gpt-3.5-turbo` 等

## 使用示例

### 在代码中使用

LLM 节点会自动使用配置的 API Key 和 Base URL：

```python
# 工作流中配置 LLM 节点
{
    "type": "llm",
    "name": "AI助手",
    "config": {
        "model": "deepseek-chat",  # 或使用环境变量 LLM_MODEL
        "temperature": 0.7,
        "prompt_template": "请分析以下内容：{input}"
    }
}
```

### 在环境变量中配置

```bash
# .env 文件
OPENAI_API_KEY=sk-your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### Docker Compose 配置

```yaml
services:
  workflow-engine:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LLM_BASE_URL=${LLM_BASE_URL:-https://api.deepseek.com}
      - LLM_MODEL=${LLM_MODEL:-deepseek-chat}
```

## 验证配置

### 1. 检查环境变量

```bash
# 检查环境变量是否正确设置
echo $OPENAI_API_KEY
echo $LLM_BASE_URL
echo $LLM_MODEL
```

### 2. 测试 API 连接

```python
from langchain_openai import ChatOpenAI

# 测试 DeepSeek API
llm = ChatOpenAI(
    model_name="deepseek-chat",
    openai_api_key="sk-your-deepseek-api-key",
    openai_api_base="https://api.deepseek.com"
)

# 测试调用
response = await llm.ainvoke("你好")
print(response.content)
```

### 3. 在工作流中测试

1. 启动服务：
   ```bash
   docker-compose up -d
   ```

2. 创建测试工作流，包含 LLM 节点

3. 执行工作流，验证 LLM 节点正常工作

## 切换回 OpenAI

如果需要切换回 OpenAI：

```bash
# .env 文件
OPENAI_API_KEY=sk-your-openai-api-key
LLM_BASE_URL=  # 留空使用默认 OpenAI API
LLM_MODEL=gpt-4
```

## 常见问题

### Q: DeepSeek API 是否完全兼容 OpenAI API？

A: 是的，DeepSeek API 完全兼容 OpenAI API 格式，包括：
- 请求参数结构
- 响应数据格式
- 错误处理机制
- 认证方式

### Q: 如何知道当前使用的是哪个 API？

A: 查看日志输出，LLM 节点会记录使用的 base URL：
```
Using custom LLM base URL: https://api.deepseek.com
```

### Q: 可以在不同节点使用不同的 API 吗？

A: 可以，在节点配置中指定不同的 `base_url` 和 `api_key`：

```json
{
    "type": "llm",
    "config": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "api_key": "sk-deepseek-key"
    }
}
```

### Q: DeepSeek 的模型有哪些？

A: DeepSeek 提供多个模型：
- `deepseek-chat` - 通用对话模型（推荐）
- `deepseek-chat-v2` - 升级版
- `deepseek-chat-v3` - 最新版（如果可用）
- 其他专用模型（根据 DeepSeek 文档）

### Q: 性能如何？

A: DeepSeek 模型在多个基准测试中表现优异，性能接近或超过 GPT-4，同时成本更低。

## 相关文档

- [快速开始指南](QUICK_START.md)
- [工作流引擎文档](../../workflow-engine/README.md)
- [环境变量配置](../../env.example)

## 参考链接

- [DeepSeek 官网](https://www.deepseek.com/)
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [OpenAI API 兼容性说明](https://platform.deepseek.com/api-docs/)

