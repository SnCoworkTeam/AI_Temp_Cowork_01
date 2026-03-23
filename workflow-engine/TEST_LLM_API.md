# LLM API 调用测试说明

## 测试目的

验证 LLM 节点是否真正调用真实 API，而不是使用 Mock 实现。

## 运行测试

### 1. 设置 API 密钥

在运行测试前，需要设置环境变量：

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
# 或者使用 DeepSeek
$env:OPENAI_API_KEY = "your-deepseek-key"
$env:LLM_BASE_URL = "https://api.deepseek.com/v1"
$env:LLM_MODEL = "deepseek-chat"
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="your-api-key-here"
# 或者使用 DeepSeek
export OPENAI_API_KEY="your-deepseek-key"
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"
```

### 2. 运行测试

```bash
cd workflow-engine
python test_llm_api.py
```

## 测试内容

### 1. LLM 节点初始化测试
- 测试无 API 密钥时的节点创建
- 测试有 API 密钥时的节点创建
- 测试配置验证功能

### 2. 真实 API 调用测试
- 验证节点配置
- 执行 LLM 节点
- 验证响应内容（确保不是 Mock）
- 验证执行历史记录
- 测试错误处理

## 预期结果

### 成功情况
```
✓ 节点配置验证通过
✓ LLM节点执行完成
✓ 获取到LLM输出
✓ 输出内容有效（非Mock）
✓ 找到执行历史记录
✓ 错误处理正常
```

### 失败情况
如果检测到 Mock 响应：
```
✗ 检测到Mock响应，API调用可能失败
```

## 验证要点

1. **非 Mock 响应**: 输出内容不应包含 `[Mock]` 字符串
2. **有效内容**: 输出内容不应为空
3. **执行历史**: 应该记录节点执行历史
4. **错误处理**: 无效 API 密钥应该被正确处理

## 注意事项

1. **API 费用**: 真实 API 调用会产生费用，请谨慎使用
2. **API 限制**: 注意 API 的速率限制
3. **测试密钥**: 建议使用测试环境的 API 密钥

## 测试结果示例

### 有 API 密钥的情况
```
============================================================
测试真实LLM API调用
============================================================

✓ 找到API密钥: sk-12345678...
   模型: gpt-3.5-turbo

1. 验证节点配置...
   ✓ 节点配置验证通过

2. 执行LLM节点...
   提示词: Say 'hello world' in JSON format
   ✓ LLM节点执行完成

3. 验证响应内容...
   ✓ 获取到LLM输出
   输出内容: {"message": "hello world"}...
   ✓ 输出内容有效（非Mock）

4. 验证执行历史...
   ✓ 找到执行历史记录: 1 条

5. 测试错误处理...
   ✓ 错误处理正常（抛出异常: AuthenticationError）

============================================================
✓ 真实LLM API调用验证通过！
============================================================
```

### 无 API 密钥的情况
```
============================================================
测试真实LLM API调用
============================================================

⚠ 警告: 未找到有效的API密钥
   请设置环境变量 OPENAI_API_KEY 或 TEST_OPENAI_API_KEY
   跳过真实API调用测试
```

## 故障排除

### 问题1: 导入错误
如果遇到 `cannot import name 'settings'` 错误，测试脚本会自动使用简化版本的 LLMNode。

### 问题2: LangChain 不可用
确保已安装 LangChain：
```bash
pip install langchain langchain-openai
```

### 问题3: API 调用失败
检查：
- API 密钥是否正确
- 网络连接是否正常
- API 服务是否可用
- 是否有足够的 API 配额

