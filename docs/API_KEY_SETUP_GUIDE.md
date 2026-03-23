# API Key 统一配置指南

## 问题分析

从测试结果来看，主要问题是：
1. **API Key未设置**：导致LLM无法初始化
2. **配置中心可能没有正确读取环境变量**
3. **各服务没有统一从配置中心读取API key**

## 解决方案

### 方案1：通过环境变量设置（推荐）

1. **设置环境变量**：
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="your-api-key-here"
   $env:LLM_BASE_URL="https://api.deepseek.com"
   $env:LLM_MODEL="deepseek-chat"
   
   # Linux/Mac
   export OPENAI_API_KEY="your-api-key-here"
   export LLM_BASE_URL="https://api.deepseek.com"
   export LLM_MODEL="deepseek-chat"
   ```

2. **或者在 .env 文件中设置**（项目根目录）：
   ```env
   OPENAI_API_KEY=your-api-key-here
   LLM_BASE_URL=https://api.deepseek.com
   LLM_MODEL=deepseek-chat
   LLM_TEMPERATURE=0.7
   LLM_MAX_TOKENS=4096
   ```

3. **重启配置中心**（让配置中心从环境变量读取并存储）：
   ```bash
   docker-compose restart config-center
   ```

4. **或者手动设置到配置中心**：
   ```bash
   python setup_api_key.py
   ```

### 方案2：直接通过配置中心API设置

```bash
# 设置API Key
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "llm.api_key",
    "value": "your-api-key-here",
    "description": "LLM API密钥",
    "environment": "default"
  }'

# 设置Base URL
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "llm.base_url",
    "value": "https://api.deepseek.com",
    "description": "LLM服务基础URL",
    "environment": "default"
  }'

# 设置Model
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "llm.model",
    "value": "deepseek-chat",
    "description": "LLM模型名称",
    "environment": "default"
  }'
```

## 配置读取优先级

1. **配置中心**（优先）
   - 各服务启动时从配置中心读取
   - 配置键：`llm.api_key`, `llm.base_url`, `llm.model`

2. **环境变量**（降级方案）
   - 如果配置中心不可用，从环境变量读取
   - `OPENAI_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`

## 验证配置

运行检查脚本：
```bash
python check_api_key_config.py
```

## 重启服务

设置完API key后，需要重启以下服务：
1. **配置中心**（如果通过环境变量设置）
2. **Agent Service**（从配置中心读取API key）
3. **Workflow Engine**（从配置中心读取API key）
4. **MCP Gateway**（确保工具可用）

```bash
docker-compose restart config-center agent-service workflow-engine mcp-gateway
```

## 注意事项

1. **不要硬编码API key**：所有服务都应该从配置中心或环境变量读取
2. **统一管理**：建议使用配置中心统一管理，便于更新和维护
3. **安全性**：生产环境应该使用密钥管理服务（如Vault）而不是环境变量

