# 上传完成确认

**上传日期**: 2025-12-02  
**版本**: v2.0

---

## ✅ 上传文件清单

### 核心代码文件

- ✅ `services/llm_client.py` - DeepSeek客户端
- ✅ `services/semantic_engine_adapter.py` - 语义引擎适配器
- ✅ `services/unified_intent_service.py` - 增强的统一意图服务

### 文件大小

- `llm_client.py`: 6.5KB
- `semantic_engine_adapter.py`: 3.2KB
- `unified_intent_service.py`: 31.4KB

---

## 🚀 服务器端操作步骤

### 1. SSH登录服务器

```bash
ssh user@server
```

### 2. 进入项目目录

```bash
cd /opt/enterprise-ai-platform
```

### 3. 设置环境变量

```bash
# 编辑环境变量文件
nano .env
# 或
vim .env

# 添加以下配置
DEEPSEEK_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
UNIFIED_INTENT_USE_LLM=true
LLM_TEMPERATURE=0.3
LLM_TIMEOUT=10.0
LLM_CACHE_TTL=3600
LLM_FALLBACK_TO_RULES=true
```

### 4. 安装依赖

```bash
# 激活虚拟环境（如果有）
source venv/bin/activate

# 安装依赖
pip install httpx langchain-openai
```

### 5. 重启服务

```bash
# Docker方式
docker-compose restart unified-intent-service

# 或systemd方式
systemctl restart unified-intent-service

# 或直接运行
python -m uvicorn api.unified_intent_api:app --host 0.0.0.0 --port 8002
```

### 6. 验证部署

```bash
# 健康检查
curl http://localhost:8002/health

# 功能测试
curl -X POST http://localhost:8002/api/v1/intent/understand \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我需要创建采购订单，供应商ABC，物料MAT001，数量100"
  }'
```

---

## ✅ 验证检查清单

- [ ] 文件已上传到服务器
- [ ] 环境变量已配置
- [ ] 依赖已安装
- [ ] 服务已重启
- [ ] 健康检查通过
- [ ] 功能测试通过
- [ ] 日志正常

---

## 🔄 回滚方案

如果部署后出现问题：

```bash
# 快速回滚：禁用LLM
export UNIFIED_INTENT_USE_LLM=false
docker-compose restart unified-intent-service
```

---

**上传状态**: ✅ 完成  
**部署状态**: ⏳ 待服务器端配置

