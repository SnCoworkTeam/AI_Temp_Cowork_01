# 阶段一第1周测试计划

**测试日期**: 2025-12-01  
**测试目标**: 验证核心数据模型创建和数据库迁移  
**测试范围**: BusinessActivity, CapabilityUnit, ActivityCapabilityMapping 模型和数据库表

---

## 📋 测试目标

### 通过标准

✅ **所有测试必须通过才能进入第2周**

1. ✅ 数据模型定义正确（无语法错误）
2. ✅ 数据库迁移成功执行
3. ✅ 表结构符合设计规范
4. ✅ 索引创建成功
5. ✅ 基础CRUD操作正常

---

## 🔍 测试用例

### 测试1: 数据模型导入测试

**目标**: 验证模型可以正确导入

**测试步骤**:
```python
# tests/test_models_import.py
def test_models_import():
    """测试模型导入"""
    from database.src.models import (
        BusinessActivity,
        CapabilityUnit,
        ActivityCapabilityMapping
    )
    assert BusinessActivity is not None
    assert CapabilityUnit is not None
    assert ActivityCapabilityMapping is not None
```

**预期结果**: ✅ 所有模型成功导入，无错误

### 测试2: 数据库迁移测试

**目标**: 验证迁移脚本可以成功执行

**测试步骤**:
```bash
# 执行迁移
cd database
alembic upgrade head
```

**预期结果**: ✅ 迁移成功，无错误

### 测试3: 表结构验证测试

**目标**: 验证表结构符合设计规范

**测试步骤**:
```python
# tests/test_table_structure.py
def test_table_structure():
    """测试表结构"""
    from database.src.core.database import get_db
    from sqlalchemy import inspect
    
    db = next(get_db())
    inspector = inspect(db.bind)
    
    # 检查business_activities表
    assert 'business_activities' in inspector.get_table_names()
    columns = {col['name']: col for col in inspector.get_columns('business_activities')}
    
    # 验证关键字段
    assert 'id' in columns
    assert 'name' in columns
    assert 'vector_entity_uri' in columns
    assert 'embedding_version' in columns
    assert 'last_vectorized_at' in columns
    
    # 检查capability_units表
    assert 'capability_units' in inspector.get_table_names()
    
    # 检查activity_capability_mappings表
    assert 'activity_capability_mappings' in inspector.get_table_names()
```

**预期结果**: ✅ 所有表存在，关键字段正确

### 测试4: 索引验证测试

**目标**: 验证索引创建成功

**测试步骤**:
```python
# tests/test_indexes.py
def test_indexes():
    """测试索引"""
    from database.src.core.database import get_db
    from sqlalchemy import inspect, text
    
    db = next(get_db())
    inspector = inspect(db.bind)
    
    # 检查business_activities表的索引
    indexes = inspector.get_indexes('business_activities')
    index_names = [idx['name'] for idx in indexes]
    
    assert 'idx_activity_name' in index_names
    assert 'idx_activity_domain_type' in index_names
    assert 'idx_activity_vector_uri' in index_names
```

**预期结果**: ✅ 所有索引创建成功

### 测试5: 基础CRUD操作测试

**目标**: 验证基础CRUD操作正常

**测试步骤**:
```python
# tests/test_crud_operations.py
def test_business_activity_crud():
    """测试业务活动CRUD"""
    from database.src.core.database import get_db
    from database.src.models import BusinessActivity
    from datetime import datetime
    
    db = next(get_db())
    
    # Create
    activity = BusinessActivity(
        id="activity:test:create_po",
        name="测试创建采购订单",
        description="测试描述",
        activity_type="action",
        business_domain="procurement",
        vector_entity_uri="activity://procurement/activity:test:create_po"
    )
    db.add(activity)
    db.commit()
    
    # Read
    retrieved = db.query(BusinessActivity).filter_by(id=activity.id).first()
    assert retrieved is not None
    assert retrieved.name == "测试创建采购订单"
    
    # Update
    retrieved.description = "更新后的描述"
    retrieved.description_updated_at = datetime.now()
    db.commit()
    
    # 验证needs_vector_update
    assert retrieved.needs_vector_update() == True
    
    # Delete
    db.delete(retrieved)
    db.commit()
    
    # 验证删除
    deleted = db.query(BusinessActivity).filter_by(id=activity.id).first()
    assert deleted is None
```

**预期结果**: ✅ 所有CRUD操作成功

### 测试6: 向量更新检查测试

**目标**: 验证向量更新检查逻辑

**测试步骤**:
```python
# tests/test_vector_update_check.py
def test_vector_update_check():
    """测试向量更新检查"""
    from database.src.models import BusinessActivity
    from datetime import datetime, timedelta
    
    # 测试1: 新活动需要更新
    activity1 = BusinessActivity(
        id="activity:test:new",
        name="新活动",
        vector_entity_uri="activity://test/activity:test:new"
    )
    assert activity1.needs_vector_update() == True
    
    # 测试2: 已向量化，描述未更新
    activity2 = BusinessActivity(
        id="activity:test:updated",
        name="已更新活动",
        vector_entity_uri="activity://test/activity:test:updated",
        last_vectorized_at=datetime.now(),
        description_updated_at=datetime.now() - timedelta(days=1)
    )
    assert activity2.needs_vector_update() == False
    
    # 测试3: 描述已更新，需要重新向量化
    activity3 = BusinessActivity(
        id="activity:test:needs_update",
        name="需要更新活动",
        vector_entity_uri="activity://test/activity:test:needs_update",
        last_vectorized_at=datetime.now() - timedelta(days=1),
        description_updated_at=datetime.now()
    )
    assert activity3.needs_vector_update() == True
```

**预期结果**: ✅ 向量更新检查逻辑正确

---

## 📊 测试执行

### 执行步骤（自动启动Docker服务）

**方式1: 使用PowerShell脚本（推荐）**
```powershell
# Windows PowerShell
.\scripts\run_stage1_week1_tests.ps1
```

**方式2: 使用Bash脚本**
```bash
# Linux/Mac/Git Bash
chmod +x scripts/run_stage1_week1_tests.sh
./scripts/run_stage1_week1_tests.sh
```

**方式3: 直接运行Python测试（自动启动Docker）**
```bash
# 测试脚本会自动启动Docker服务
python -m pytest tests/test_stage1_week1_with_docker.py -v --tb=short -s
```

### 测试脚本功能

测试脚本会自动执行以下步骤：

1. **启动Docker服务**
   - 自动启动 `postgres` 服务
   - 等待服务就绪（最多30次重试，每次间隔2秒）

2. **检查数据库连接**
   - 验证数据库连接可用
   - 最多重试10次，每次间隔2秒

3. **执行数据库迁移**
   - 自动执行 `alembic upgrade head`
   - 验证迁移成功

4. **运行所有测试用例**
   - 模型导入测试
   - 数据库迁移测试
   - 表结构验证测试
   - 索引验证测试
   - CRUD操作测试
   - 向量更新检查测试

5. **生成测试报告**
   - 显示测试结果
   - 明确是否可以进入第2周

### 验证测试结果

- ✅ 所有测试用例通过
- ✅ 无错误或警告
- ✅ 测试覆盖率 > 80%

---

## ✅ 测试通过标准

**必须满足以下所有条件才能进入第2周**:

1. ✅ 所有6个测试用例通过
2. ✅ 数据库迁移成功执行
3. ✅ 表结构验证通过
4. ✅ 索引验证通过
5. ✅ CRUD操作测试通过
6. ✅ 向量更新检查逻辑正确

---

## 📝 测试报告模板

```markdown
# 阶段一第1周测试报告

**测试日期**: YYYY-MM-DD
**测试人员**: XXX
**测试环境**: 开发环境

## 测试结果

| 测试用例 | 状态 | 备注 |
|---------|------|------|
| 数据模型导入测试 | ✅/❌ | |
| 数据库迁移测试 | ✅/❌ | |
| 表结构验证测试 | ✅/❌ | |
| 索引验证测试 | ✅/❌ | |
| 基础CRUD操作测试 | ✅/❌ | |
| 向量更新检查测试 | ✅/❌ | |

## 问题记录

1. [问题描述]
   - 影响: [高/中/低]
   - 状态: [已修复/待修复]

## 测试结论

✅ **通过** / ❌ **不通过**

**是否进入第2周**: [是/否]

**备注**: [其他说明]
```

---

**文档版本**: v1.0  
**最后更新**: 2025-12-01

