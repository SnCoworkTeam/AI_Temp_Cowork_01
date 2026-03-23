# 上传到服务器 - 操作指南

**版本**: v2.0  
**日期**: 2025-12-02

---

## ✅ 测试完成确认

### 测试结果

- ✅ **总测试数**: 15
- ✅ **通过数**: 15
- ✅ **失败数**: 0
- ✅ **通过率**: 100%

### 代码检查

- ✅ 无语法错误
- ✅ 无linter错误
- ✅ 导入检查通过

---

## 🚀 上传步骤

### 方式1: 使用上传脚本（推荐）

#### Windows PowerShell

```powershell
# 运行上传脚本
powershell -ExecutionPolicy Bypass -File scripts/upload_to_server.ps1

# 按提示输入:
# - 服务器地址: user@192.168.1.100
# - 服务器路径: /opt/enterprise-ai-platform
```

#### Linux/Mac

```bash
# 添加执行权限
chmod +x scripts/upload_to_server.sh

# 运行上传脚本
bash scripts/upload_to_server.sh

# 按提示输入:
# - 服务器地址: user@192.168.1.100
# - 服务器路径: /opt/enterprise-ai-platform
```

### 方式2: 手动上传

#### 使用SCP

```bash
# 上传核心代码文件
scp services/llm_client.py user@server:/opt/enterprise-ai-platform/services/
scp services/semantic_engine_adapter.py user@server:/opt/enterprise-ai-platform/services/
scp services/unified_intent_service.py user@server:/opt/enterprise-ai-platform/services/

# 上传测试文件（可选）
scp tests/test_unified_intent_llm_enhancement.py user@server:/opt/enterprise-ai-platform/tests/

# 上传文档（可选）
scp -r docs/UNIFIED_INTENT_LLM_ENHANCEMENT_PLAN_V2.md user@server:/opt/enterprise-ai-platform/docs/
scp DEPLOYMENT_GUIDE.md user@server:/opt/enterprise-ai-platform/
```

#### 使用Git（如果服务器有Git仓库）

```bash
# 在服务器上
cd /opt/enterprise-ai-platform
git pull origin main
# 或
git checkout <branch-name>
```

---

## ⚙️ 服务器端配置

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
  "service": "unified_intent_service",
  "timestamp": "2025-12-02T..."
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
  "user_input": "我需要创建采购订单...",
  "base_intent": "tool_execution",
  "confidence": 0.90,
  "suggested_activities": [...],
  "execution_suggestions": [...],
  "reasoning": "...",
  "fallback_mode": false,
  "query_time": 0.015
}
```

### 3. 检查日志

```bash
# Docker方式
docker-compose logs -f unified-intent-service

# 或直接查看日志文件
tail -f logs/unified_intent_service.log
```

---

## 🔄 回滚方案

如果部署后出现问题，可以快速回滚：

```bash
# 方式1: 禁用LLM（快速回滚）
export UNIFIED_INTENT_USE_LLM=false
docker-compose restart unified-intent-service

# 方式2: 回滚代码
cd /opt/enterprise-ai-platform
git checkout <previous-commit>
docker-compose restart unified-intent-service

# 方式3: 使用旧版本镜像
docker-compose pull unified-intent-service:previous-version
docker-compose up -d unified-intent-service
```

---

## 📋 部署检查清单

- [ ] 代码已上传到服务器
- [ ] 环境变量已配置
- [ ] 依赖已安装
- [ ] 服务已重启
- [ ] 健康检查通过
- [ ] 功能测试通过
- [ ] 日志正常

---

## ⚠️ 注意事项

1. **API密钥安全**: 
   - 确保API密钥安全存储
   - 不要提交到代码库
   - 使用环境变量或密钥管理服务

2. **网络连接**: 
   - 确保服务器可以访问DeepSeek API
   - 检查防火墙设置

3. **数据库连接**: 
   - 确保数据库连接正常
   - 检查业务活动数据是否存在

4. **监控日志**: 
   - 部署后密切关注日志
   - 检查错误和警告信息
   - 监控性能指标

---

## 📊 预期效果

部署成功后，您应该看到：

1. ✅ **意图识别准确率提升**: 20-30%
2. ✅ **复杂意图支持**: 支持多步骤、多实体意图
3. ✅ **自动参数填充**: 提升用户体验
4. ✅ **高可用性**: 降级机制保证可用性

---

**上传状态**: ✅ 准备就绪  
**测试状态**: ✅ 全部通过  
**部署建议**: ✅ 可以上传到服务器

