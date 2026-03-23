# 测试修复实施计划

## 📋 修复目标

修复以下测试文件中的NameError和API不匹配问题：
1. `knowledge-base/tests/unit/test_auto_summarizer.py`
2. `knowledge-base/tests/unit/test_auto_tagger.py`
3. `knowledge-base/tests/unit/test_category_classifier.py`

## 🔧 修复步骤

### 步骤1：修复NameError

**问题：** 在except块中使用了未定义的变量`func_name`和`class_name`

**修复方法：** 使用字符串常量替代

**示例：**
```python
# 修复前
except Exception as e:
    pytest.skip(f"无法导入或初始化{class_name}: {e}")

# 修复后
except Exception as e:
    pytest.skip(f"无法导入或初始化AutoSummarizer: {e}")
```

### 步骤2：修复初始化参数

**问题：** 测试代码传递了错误的初始化参数

**修复方法：** 使用正确的参数

**示例：**
```python
# 修复前
instance = AutoSummarizer(mock_db)

# 修复后
instance = AutoSummarizer(max_summary_length=200)
```

### 步骤3：修复API导入方式

**问题：** 测试期望导入顶层函数，但实际是类方法

**修复方法：** 实例化类后调用方法

**示例：**
```python
# 修复前
from src.core.auto_summarizer import summarize
result = summarize(content)

# 修复后
from src.core.auto_summarizer import AutoSummarizer
summarizer = AutoSummarizer()
result = summarizer.summarize(content)
```

## 📝 具体修复内容

### test_auto_summarizer.py

1. **第37行**：`class_name` → `"AutoSummarizer"`
2. **第34行**：`AutoSummarizer(mock_db)` → `AutoSummarizer(max_summary_length=200)`
3. **第46行**：`func_name` → `"get_auto_summarizer"`
4. **第55行**：`func_name` → `"__init__"`
5. **第60-64行**：改为测试实例方法`summarizer.summarize()`
6. **第69-73行**：改为测试实例方法`summarizer.summarize_chunks()`

### test_auto_tagger.py

1. **第37行**：`class_name` → `"AutoTagger"`
2. **第34行**：`AutoTagger(mock_db)` → `AutoTagger(max_tags=10, min_score=0.1)`
3. **第46行**：`func_name` → `"get_auto_tagger"`
4. **第55行**：`func_name` → `"__init__"`
5. **第60-64行**：改为测试实例方法`tagger.generate_tags()`
6. **第69-73行**：改为测试实例方法`tagger.suggest_tags()`

### test_category_classifier.py

1. **第37行**：`class_name` → `"CategoryClassifier"`
2. **第34行**：`CategoryClassifier(mock_db)` → `CategoryClassifier()`
3. **第46行**：`func_name` → `"get_category_classifier"`
4. **第55行**：`func_name` → `"__init__"`
5. **第60-64行**：改为测试实例方法`classifier.classify()`
6. **第69-73行**：改为测试实例方法`classifier.get_top_categories()`（如果存在）

## ✅ 验证步骤

1. **运行修复后的测试**
   ```bash
   pytest knowledge-base/tests/unit/test_auto_summarizer_fixed.py -v
   pytest knowledge-base/tests/unit/test_auto_tagger_fixed.py -v
   pytest knowledge-base/tests/unit/test_category_classifier_fixed.py -v
   ```

2. **检查测试结果**
   - 确认没有NameError
   - 确认测试可以正常跳过（如果模块不存在）
   - 确认测试可以正常运行（如果模块存在）

3. **替换原测试文件**
   - 备份原文件
   - 用修复后的文件替换原文件
   - 再次运行测试验证

## 🎯 预期结果

修复后，所有测试应该：
- ✅ 不再出现NameError
- ✅ 可以正确初始化对象
- ✅ 可以正确调用实例方法
- ✅ 在模块不存在时优雅地跳过测试

## 📊 修复优先级

1. **高优先级**：修复NameError（导致测试无法运行）
2. **中优先级**：修复初始化参数（导致测试失败）
3. **低优先级**：完善测试逻辑（提高测试覆盖率）




