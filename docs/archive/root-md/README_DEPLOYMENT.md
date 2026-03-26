# 统一意图识别LLM增强 - 部署说明

**版本**: v2.0  
**部署日期**: 2025-12-02

---

## ✅ 测试完成确认

### 测试结果

- ✅ **总测试数**: 15
- ✅ **通过数**: 15
- ✅ **失败数**: 0
- ✅ **通过率**: 100%

### 功能验证

- ✅ LLM客户端功能正常
- ✅ 语义引擎适配器正常
- ✅ LLM意图分析正常
- ✅ 动态融合策略正常
- ✅ 降级机制正常
- ✅ 端到端流程正常

### 性能验证

- ✅ 平均响应时间: 14.6ms
- ✅ 性能要求: 满足（< 3秒）

---

## 🚀 部署步骤

### 步骤1: 上传代码到服务器

**Windows**:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/upload_to_server.ps1
```

**Linux/Mac**:
```bash
bash scripts/upload_to_server.sh
```

### 步骤2: 服务器端配置

```bash
# SSH登录服务器
ssh user@server

# 进入项目目录
cd /opt/enterprise-ai-platform

# 设置环境变量
export DEEPSEEK_API_KEY=your-api-key
export LLM_BASE_URL=https://api.deepseek.com
export LLM_MODEL=deepseek-chat
export UNIFIED_INTENT_USE_LLM=true

# 安装依赖
pip install httpx langchain-openai

# 重启服务
docker-compose restart unified-intent-service
```

### 步骤3: 验证部署

```bash
# 健康检查
curl http://localhost:8002/health

# 功能测试
curl -X POST http://localhost:8002/api/v1/intent/understand \
  -H "Content-Type: application/json" \
  -d '{"user_input": "创建采购订单"}'
```

---

## 📋 部署检查清单

- [ ] 代码已上传到服务器
- [ ] 环境变量已配置
- [ ] 依赖已安装
- [ ] 服务已重启
- [ ] 健康检查通过
- [ ] 功能测试通过

---

## ⚠️ 注意事项

1. **API密钥安全**: 确保API密钥安全存储
2. **网络连接**: 确保服务器可以访问DeepSeek API
3. **数据库连接**: 确保数据库连接正常
4. **监控日志**: 部署后密切关注日志

---

## 🔄 回滚方案

如果部署后出现问题：

```bash
export UNIFIED_INTENT_USE_LLM=false
docker-compose restart unified-intent-service
```

---

**部署状态**: ✅ 准备就绪  
**测试状态**: ✅ 全部通过  
**文档状态**: ✅ 完整

