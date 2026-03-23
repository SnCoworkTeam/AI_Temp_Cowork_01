# 邮件参数提取逻辑修复

## 问题描述

用户发送邮件请求：
```
给yubin.liu@pcitc.com发邮件，收件人刘玉斌，主题会议通知，主题关于ai场景的讨论，时间是明天下午3点
```

系统正确识别为邮件工具，但参数提取失败：
- ❌ 错误：`Missing required parameter: body`
- ❌ 主题提取可能只匹配到第一个"主题会议通知"，忽略了"主题关于ai场景的讨论"
- ❌ 正文提取逻辑有问题，移除主题后可能把有用的内容也移除了

## 修复方案

### 1. 改进主题提取（支持多个"主题"关键词）

**修复前**：
- 只匹配第一个"主题"关键词
- 可能提取到不完整的主题

**修复后**：
```python
# 找到所有匹配的主题
all_subjects = []
for pattern in subject_patterns:
    matches = re.finditer(pattern, user_input, re.IGNORECASE)
    for match in matches:
        subject_text = match.group(1).strip()
        if subject_text and subject_text not in all_subjects:
            all_subjects.append(subject_text)

# 如果有多个主题，选择最详细的那个（最长的）
if all_subjects:
    parameters["subject"] = max(all_subjects, key=len)
```

**效果**：
- 对于输入：`主题会议通知，主题关于ai场景的讨论`
- 会提取到：`关于ai场景的讨论`（更详细）

### 2. 智能正文提取（会议邮件）

**修复前**：
- 简单地从用户输入中移除已提取的部分
- 可能移除有用的内容

**修复后**：
```python
if "会议" in user_input:
    body_parts = []
    
    # 提取收件人姓名
    recipient_name_match = re.search(r'收件人\s*([^，,。\n]+)', user_input)
    if recipient_name_match:
        recipient_name = recipient_name_match.group(1).strip()
        body_parts.append(f"尊敬的{recipient_name}，")
    
    # 提取会议主题/讨论内容
    discussion_match = re.search(r'关于\s*([^，,。\n]+)\s*的讨论', user_input)
    if discussion_match:
        discussion_topic = discussion_match.group(1).strip()
        body_parts.append(f"\n\n本次会议将讨论：{discussion_topic}")
    
    # 提取会议时间
    time_match = re.search(r'时间[是：:]\s*([^，,。\n]+)', user_input)
    # ... 提取时间信息
    
    parameters["body"] = ''.join(body_parts).strip()
```

**效果**：
- 对于输入：`给yubin.liu@pcitc.com发邮件，收件人刘玉斌，主题会议通知，主题关于ai场景的讨论，时间是明天下午3点`
- 会生成正文：
  ```
  尊敬的刘玉斌，
  
  本次会议将讨论：ai场景
  
  会议时间：明天 下午 3点
  ```

### 3. 改进非会议邮件的正文提取

**修复前**：
- 简单替换，可能移除有用的内容

**修复后**：
```python
# 移除主题相关关键词和内容（使用正则表达式精确匹配）
body = re.sub(r'主题[：:]\s*[^，,。\n]+', '', body)
body = re.sub(r'标题[：:]\s*[^，,。\n]+', '', body)
body = re.sub(r'关于[：:]\s*[^，,。\n]+', '', body)
body = re.sub(r'收件人\s*[^，,。\n]+', '', body)
body = re.sub(r'给\s*[^，,。\n]+\s*发', '', body)

# 清理多余的空格和标点
body = re.sub(r'[，,]\s*[，,]', '，', body)
body = re.sub(r'\s+', ' ', body).strip()
```

**效果**：
- 更精确地移除命令部分，保留实际内容

## 测试用例

### 测试用例1：会议邮件（多个主题）
```
输入：给yubin.liu@pcitc.com发邮件，收件人刘玉斌，主题会议通知，主题关于ai场景的讨论，时间是明天下午3点

预期结果：
- to_emails: ["yubin.liu@pcitc.com"]
- subject: "关于ai场景的讨论"（选择最详细的主题）
- body: "尊敬的刘玉斌，\n\n本次会议将讨论：ai场景\n\n会议时间：明天 下午 3点"
```

### 测试用例2：简单邮件
```
输入：给yubin.liu@pcitc.com发邮件，主题测试，正文这是一封测试邮件

预期结果：
- to_emails: ["yubin.liu@pcitc.com"]
- subject: "测试"
- body: "这是一封测试邮件"
```

### 测试用例3：邮件（无明确正文）
```
输入：给yubin.liu@pcitc.com发邮件，主题项目进度更新

预期结果：
- to_emails: ["yubin.liu@pcitc.com"]
- subject: "项目进度更新"
- body: "给yubin.liu@pcitc.com发邮件，主题项目进度更新"（清理后保留的内容，或使用用户输入）
```

## 修改的文件

- `agent-service/src/core/orchestration_engine.py`
  - `_extract_email_parameters`方法：改进主题和正文提取逻辑

## 预期效果

1. **更准确的主题提取**：支持多个"主题"关键词，选择最详细的那个
2. **智能正文构建**：对于会议邮件，自动构建结构化的正文内容
3. **更好的内容保留**：精确移除命令部分，保留实际内容
4. **必填参数保证**：确保`to_emails`、`subject`、`body`都有值

## 注意事项

1. **LLM参数提取优先**：如果`intent_analysis.extracted_context.parameters`中有参数，会优先使用
2. **降级处理**：如果所有提取方法都失败，会使用默认值或用户输入
3. **日志记录**：提取的参数会记录到日志中，方便调试

## 后续优化建议

1. **使用LLM提取参数**：让LLM直接提取邮件参数，而不是依赖正则表达式
2. **联系人映射**：实现联系人姓名到邮箱的映射（如"刘玉斌" -> "yubin.liu@pcitc.com"）
3. **时间解析**：更智能地解析时间（如"明天下午3点" -> "2025-01-XX 15:00"）
4. **模板支持**：支持邮件模板，根据邮件类型选择不同的模板


