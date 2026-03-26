# 测试NameError批量修复计划

## 📋 问题范围

根据grep搜索结果，发现大量测试文件存在NameError问题：

### 受影响文件统计

- **knowledge-base/tests/unit/**: 约147处NameError
- **metadata-service/tests/unit/**: 约122处NameError
- **database/tests/unit/**: 约158处NameError

**总计：约427处NameError需要修复**

## 🔧 修复策略

### 策略1：手动修复关键文件（已完成）

已修复用户明确提到的关键文件：
- ✅ `knowledge-base/tests/unit/test_chunk_repository.py`
- ✅ `knowledge-base/tests/unit/test_config.py`
- ✅ `knowledge-base/tests/unit/test_database.py`
- ✅ `knowledge-base/tests/unit/test_document_metadata.py`
- ✅ `knowledge-base/tests/unit/test_core_components.py`

### 策略2：批量修复脚本（推荐）

创建Python脚本自动修复所有文件：
- 从测试函数名提取函数/类名
- 从import语句提取函数/类名
- 替换所有func_name和class_name

### 策略3：正则表达式批量替换（快速但需谨慎）

使用PowerShell或sed批量替换，但需要确保替换正确。

## 📝 修复模式

### 模式1：func_name修复

**查找模式：**
```python
pytest.skip(f"无法导入{func_name}: {e}")
```

**修复方法：**
从测试函数名或import语句提取函数名：
- `test_get_by_id` → `get_by_id`
- `test_create_chunk` → `create_chunk`
- `from module import function_name` → `function_name`

### 模式2：class_name修复

**查找模式：**
```python
pytest.skip(f"无法导入或初始化{class_name}: {e}")
```

**修复方法：**
从测试函数名或import语句提取类名：
- `test_documentmetadata_initialization` → `DocumentMetadata`
- `from module import ClassName` → `ClassName`

### 模式3：转义序列修复

**查找模式：**
```python
"src\core\module.py"
```

**修复方法：**
```python
"src/core/module.py"
```

## 🛠️ 实施步骤

### 步骤1：修复关键文件（已完成）✅

### 步骤2：运行批量修复脚本

```bash
# 使用Python脚本
python scripts/fix-test-nameerrors.py

# 或使用PowerShell脚本
.\scripts\fix-all-test-nameerrors.ps1
```

### 步骤3：验证修复

```bash
# 运行测试验证
pytest knowledge-base/tests/unit/ -v --no-cov
pytest metadata-service/tests/unit/ -v --no-cov
pytest database/tests/unit/ -v --no-cov
```

### 步骤4：处理其他问题

- 安装pydantic-settings（已完成）✅
- 修复patch路径问题（test_core_components.py已修复）✅
- 修复方法名不一致（test_core_components.py已修复）✅

## 📊 修复进度

### 已完成
- ✅ 5个关键文件修复
- ✅ pydantic-settings依赖安装
- ✅ patch路径和方法名修复

### 待完成
- ⏳ 批量修复其他测试文件（约422处）

## 🎯 优先级

1. **高优先级**：已修复的关键文件验证
2. **中优先级**：批量修复其他测试文件
3. **低优先级**：完善测试逻辑




