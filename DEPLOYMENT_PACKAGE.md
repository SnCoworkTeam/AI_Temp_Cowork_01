# 部署包说明

**版本**: v2.0  
**日期**: 2025-12-02  
**状态**: ✅ 测试完成，可以部署

---

## 📦 部署文件清单

### 核心代码文件

```
services/
  ├── llm_client.py                    # DeepSeek客户端（新增）
  ├── semantic_engine_adapter.py       # 语义引擎适配器（新增）
  └── unified_intent_service.py        # 增强的统一意图服务（已更新）

api/
  ├── unified_intent_api.py            # 统一意图API（已存在）
  └── collaborative_interface_api.py  # 协同界面API（已存在）

tests/
  └── test_unified_intent_llm_enhancement.py  # 测试套件（新增）
```

### 文档文件

```
docs/
  └── UNIFIED_INTENT_LLM_ENHANCEMENT_PLAN_V2.md  # 优化方案文档

DEPLOYMENT_GUIDE.md                    # 部署指南
DEPLOYMENT_CHECKLIST.md                # 部署检查清单
DEPLOYMENT_READY.md                     # 部署就绪确认
FINAL_LLM_ENHANCEMENT_TEST_REPORT.md   # 最终测试报告
LLM_ENHANCEMENT_DEPLOYMENT_SUMMARY.md   # 部署总结
```

### 部署脚本

```
scripts/
  ├── upload_to_server.ps1             # Windows上传脚本
  ├── upload_to_server.sh               # Linux/Mac上传脚本
  └── deploy_unified_intent_llm.sh      # 部署脚本
```

---

## 🚀 快速部署

### 方式1: 使用上传脚本（推荐）

**Windows**:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/upload_to_server.ps1
```

**Linux/Mac**:
```bash
chmod +x scripts/upload_to_server.sh
bash scripts/upload_to_server.sh
```

### 方式2: 手动上传

```bash
# 使用scp上传
scp -r services/llm_client.py services/semantic_engine_adapter.py services/unified_intent_service.py user@server:/opt/enterprise-ai-platform/services/

# 上传API文件（如果需要）
scp -r api/unified_intent_api.py api/collaborative_interface_api.py user@server:/opt/enterprise-ai-platform/api/
```

---

## ⚙️ 服务器端配置

### 1. 环境变量

```bash
# 必需配置
export DEEPSEEK_API_KEY=your-api-key
export LLM_BASE_URL=https://api.deepseek.com
export LLM_MODEL=deepseek-chat

# 可选配置
export UNIFIED_INTENT_USE_LLM=true
export LLM_TEMPERATURE=0.3
export LLM_TIMEOUT=10.0
export LLM_CACHE_TTL=3600
export LLM_FALLBACK_TO_RULES=true
```

### 2. 安装依赖

```bash
pip install httpx langchain-openai
```

### 3. 重启服务

```bash
# Docker方式
docker-compose restart unified-intent-service

# 或systemd方式
systemctl restart unified-intent-service
```

---

## ✅ 验证部署

### 1. 健康检查

```bash
curl http://localhost:8002/health
```

预期响应:
```json
{
  "status": "healthy",
  "service": "unified_intent_service"
}
```

### 2. 功能测试

```bash
curl -X POST http://localhost:8002/api/v1/intent/understand \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我需要创建采购订单，供应商ABC，物料MAT001，数量100"
  }'
```

预期响应:
```json
{
  "base_intent": "tool_execution",
  "confidence": 0.90,
  "suggested_activities": [...],
  "execution_suggestions": [...]
}
```

---

## 🔄 回滚方案

如果部署后出现问题：

```bash
# 快速回滚：禁用LLM
export UNIFIED_INTENT_USE_LLM=false
docker-compose restart unified-intent-service

# 或回滚代码
git checkout <previous-commit>
docker-compose restart unified-intent-service
```

---

**部署状态**: ✅ 准备就绪  
**测试状态**: ✅ 全部通过 (15/15)  
**文档状态**: ✅ 完整


