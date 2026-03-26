# DeepSeek API 测试说明

## 快速开始

### 方法1: 使用PowerShell脚本（推荐）

```powershell
cd workflow-engine
.\test_deepseek.ps1
```

### 方法2: 手动设置环境变量

在PowerShell中运行：

```powershell
# 设置DeepSeek API密钥
$env:OPENAI_API_KEY = "your-deepseek-api-key-here"

# 设置DeepSeek API地址
$env:LLM_BASE_URL = "https://api.deepseek.com/v1"

# 设置模型名称
$env:LLM_MODEL = "deepseek-chat"

# 运行测试
cd workflow-engine
python test_llm_api.py
```

### 方法3: 更新.env文件

编辑项目根目录的 `.env` 文件，确保以下配置正确：

```env
OPENAI_API_KEY=your-deepseek-api-key-here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

然后运行：

```powershell
cd workflow-engine
python test_llm_api.py
```

## 测试内容

测试脚本会验证：

1. ✅ **环境变量加载** - 检查API密钥和配置是否正确加载
2. ✅ **LLM节点初始化** - 验证节点创建和配置验证
3. ✅ **真实API调用** - 调用DeepSeek API并验证响应
4. ✅ **非Mock响应** - 确保返回的是真实API响应，不是Mock数据
5. ✅ **执行历史** - 验证执行历史记录功能
6. ✅ **错误处理** - 测试错误处理机制

## 预期输出

成功运行后，您应该看到：

```
============================================================
测试真实LLM API调用
============================================================

调试信息:
   OPENAI_API_KEY: 已设置 (XX 字符)
   LLM_BASE_URL: https://api.deepseek.com/v1
   LLM_MODEL: deepseek-chat

✓ 找到API密钥: sk-xxxxx...xxxx

   模型: deepseek-chat
   Base URL: https://api.deepseek.com/v1
   使用 DeepSeek API

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
   ✓ 错误处理正常

============================================================
✓ 真实LLM API调用验证通过！
============================================================
```

## 故障排除

### 问题1: 环境变量未设置

**错误信息:**
```
⚠ 警告: 未找到有效的API密钥
```

**解决方法:**
- 确保在PowerShell中设置了环境变量
- 或更新.env文件中的配置

### 问题2: API调用失败

**可能原因:**
- API密钥无效
- 网络连接问题
- API服务不可用

**解决方法:**
- 检查API密钥是否正确
- 检查网络连接
- 验证DeepSeek API服务状态

### 问题3: .env文件编码问题

**错误信息:**
```
UnicodeDecodeError: 'utf-8' codec can't decode
```

**解决方法:**
- 将.env文件保存为UTF-8编码
- 或使用PowerShell直接设置环境变量

## 注意事项

1. **API费用**: 真实API调用会产生费用，请谨慎使用
2. **密钥安全**: 不要将API密钥提交到代码仓库
3. **测试环境**: 建议使用测试环境的API密钥

## 获取DeepSeek API密钥

1. 访问 [DeepSeek官网](https://www.deepseek.com/)
2. 注册账号并登录
3. 进入API管理页面
4. 创建新的API密钥
5. 复制密钥并设置到环境变量中

