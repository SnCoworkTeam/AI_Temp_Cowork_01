# 邮件参数类型修复

## 问题描述

用户发送邮件请求时，出现错误：
```
Parameter 'to_emails' must be of type '['string', 'array']', got 'str'
```

**根本原因**：
- `send_email` 函数期望 `to_emails` 参数是 `List[str]` 类型
- 但在 `_extract_email_parameters` 中，当只有一个邮箱时，代码设置为字符串：
  ```python
  parameters["to_emails"] = emails[0] if len(emails) == 1 else emails
  ```
- 虽然 `execute_send_email` 中有处理逻辑来转换字符串到列表，但参数验证可能在转换之前就发生了

## 修复方案

### 1. 确保 `to_emails` 始终是列表类型

**修复前**：
```python
if emails:
    parameters["to_emails"] = emails[0] if len(emails) == 1 else emails
```

**修复后**：
```python
if emails:
    # 确保 to_emails 始终是列表类型
    parameters["to_emails"] = emails if isinstance(emails, list) else [emails]
```

### 2. 修复从 `extracted_params` 获取时的类型转换

**修复前**：
```python
if "to_emails" not in parameters and extracted_params.get("to_emails"):
    parameters["to_emails"] = extracted_params["to_emails"]
```

**修复后**：
```python
if "to_emails" not in parameters and extracted_params.get("to_emails"):
    to_emails_value = extracted_params["to_emails"]
    # 确保 to_emails 始终是列表类型
    if isinstance(to_emails_value, str):
        parameters["to_emails"] = [to_emails_value]
    elif isinstance(to_emails_value, list):
        parameters["to_emails"] = to_emails_value
    else:
        parameters["to_emails"] = [str(to_emails_value)]
```

### 3. 修复默认值设置

**修复前**：
```python
if not parameters.get("to_emails"):
    parameters["to_emails"] = "yubin.liu@pcitc.com"  # ❌ 字符串
```

**修复后**：
```python
if not parameters.get("to_emails"):
    parameters["to_emails"] = ["yubin.liu@pcitc.com"]  # ✅ 列表
else:
    # 确保 to_emails 是列表类型
    to_emails_value = parameters.get("to_emails")
    if isinstance(to_emails_value, str):
        parameters["to_emails"] = [to_emails_value]
    elif not isinstance(to_emails_value, list):
        parameters["to_emails"] = [str(to_emails_value)]
```

## 修改的文件

- `agent-service/src/core/orchestration_engine.py`
  - `_extract_email_parameters` 方法：确保 `to_emails` 始终是列表类型

## 预期效果

1. **类型正确**：`to_emails` 参数始终是 `List[str]` 类型
2. **兼容性**：支持从字符串或列表转换
3. **错误减少**：避免参数类型验证错误

## 测试场景

### 场景1：单个邮箱
```
输入：给yubin.liu@pcitc.com发邮件
预期：parameters["to_emails"] = ["yubin.liu@pcitc.com"]  # ✅ 列表
```

### 场景2：多个邮箱
```
输入：给yubin.liu@pcitc.com和test@example.com发邮件
预期：parameters["to_emails"] = ["yubin.liu@pcitc.com", "test@example.com"]  # ✅ 列表
```

### 场景3：从LLM提取的参数
```
extracted_params = {"to_emails": "yubin.liu@pcitc.com"}
预期：parameters["to_emails"] = ["yubin.liu@pcitc.com"]  # ✅ 转换为列表
```


