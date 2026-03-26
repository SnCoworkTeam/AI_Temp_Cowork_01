# 测试覆盖率改进 - 命令循环计划

## 循环流程概述

这是一个可持续的命令循环流程，用于持续改进测试覆盖率。每个循环包含以下步骤：

```
连接服务器 → 检查覆盖率 → 创建测试 → 运行测试 → 修复Bug → 提交代码 → 重复
```

---

## 第一步：连接到服务器

```bash
ssh ai-platform-dev
```

或使用完整连接信息：
```bash
ssh user@your-server-ip
```

---

## 第二步：进入项目目录

```bash
cd /path/to/enterprise-ai-platform
```

---

## 第三步：检查当前覆盖率

### 检查auth-service覆盖率
```bash
cd auth-service
pytest tests/ --cov=app --cov-report=term-missing --cov-report=json
cat coverage.json
cd ..
```

### 检查其他服务覆盖率
```bash
cd [service-name]
pytest tests/ --cov=app --cov-report=term-missing
cd ..
```

---

## 第四步：识别未覆盖的代码

### 查看覆盖率报告
```bash
cd auth-service
pytest tests/ --cov=app --cov-report=html
```

### 查看HTML报告（需要浏览器）
```bash
cd htmlcov
ls -la
```

### 或使用命令行查看未覆盖的行
```bash
pytest tests/ --cov=app --cov-report=term-missing | grep "TOTAL"
pytest tests/ --cov=app --cov-report=term-missing | grep -A 5 "Missing"
```

---

## 第五步：创建测试文件

### 对于新的测试文件
```bash
cd auth-service/tests/unit
touch test_new_feature.py
```

### 编辑测试文件
```bash
vim test_new_feature.py
# 或
nano test_new_feature.py
```

### 测试模板（手动输入到编辑器）
```python
import pytest
from app.module import function_to_test

def test_function_name():
    # Arrange
    input_data = "test"

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result == expected_output

def test_function_edge_case():
    # 测试边界情况
    pass
```

---

## 第六步：运行新测试

### 运行单个测试文件
```bash
cd auth-service
pytest tests/unit/test_new_feature.py -v
```

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行测试并检查覆盖率
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 第七步：修复测试失败

### 如果测试失败，查看详细错误
```bash
pytest tests/unit/test_new_feature.py -vv
```

### 修改源代码文件
```bash
cd app
vim module_file.py
# 修复bug
```

### 或修改测试文件
```bash
cd tests/unit
vim test_new_feature.py
# 修正测试
```

### 重新运行测试
```bash
cd ../..
pytest tests/unit/test_new_feature.py -v
```

---

## 第八步：验证覆盖率提升

### 对比前后覆盖率
```bash
# 运行完整覆盖率检查
pytest tests/ --cov=app --cov-report=term-missing

# 查看特定模块的覆盖率
pytest tests/ --cov=app.module --cov-report=term
```

---

## 第九步：提交更改

### 查看更改
```bash
git status
git diff
```

### 添加文件
```bash
git add auth-service/tests/unit/test_new_feature.py
git add auth-service/app/module_file.py
```

### 提交
```bash
git commit -m "test: add tests for module_file, improve coverage from X% to Y%"
```

### 推送到远程
```bash
git push origin main
```

---

## 第十步：重复循环

回到**第三步**，继续下一个未覆盖的模块。

---

## 快速循环命令序列

以下是一个完整循环的命令序列，可以依次执行：

```bash
# 1. 进入服务目录
cd auth-service

# 2. 检查覆盖率并找出未覆盖的文件
pytest tests/ --cov=app --cov-report=term-missing | tee coverage-report.txt
grep -E "^app/" coverage-report.txt | grep -v "100%" | head -1

# 3. 创建测试文件（根据上一步的输出确定文件名）
cd tests/unit
touch test_target_module.py

# 4. 编辑测试文件
vim test_target_module.py
# [手动编写测试]

# 5. 运行新测试
cd ../..
pytest tests/unit/test_target_module.py -v

# 6. 如果失败，修复代码
# vim app/target_module.py

# 7. 重新运行测试
pytest tests/unit/test_target_module.py -v

# 8. 运行完整测试套件
pytest tests/ --cov=app --cov-report=term-missing

# 9. 提交
cd ..
git add -A
git commit -m "test: improve coverage for target_module"
git push

# 10. 重复
cd auth-service
```

---

## 多服务循环

### 服务列表
```bash
# 按优先级排序
services=(
    "auth-service"
    "api-gateway"
    "knowledge-base"
    "metadata-service"
    "mcp-gateway"
    "workflow-engine"
)
```

### 循环所有服务
```bash
# Service 1: auth-service
cd auth-service
pytest tests/ --cov=app --cov-report=term-missing
# [创建测试，运行，提交]
cd ..

# Service 2: api-gateway
cd api-gateway
pytest tests/ --cov=app --cov-report=term-missing
# [创建测试，运行，提交]
cd ..

# Service 3: knowledge-base
cd knowledge-base
pytest tests/ --cov=app --cov-report=term-missing
# [创建测试，运行，提交]
cd ..

# 以此类推...
```

---

## 常用命令备忘

### SSH相关
```bash
# 连接
ssh ai-platform-dev

# 断开但保持进程
Ctrl+Z
bg
disown

# 使用screen保持会话
screen -S coverage-work
# 分离: Ctrl+A, D
# 重新连接: screen -r coverage-work
```

### Git相关
```bash
# 查看状态
git status

# 查看差异
git diff

# 添加所有更改
git add -A

# 提交
git commit -m "message"

# 推送
git push

# 拉取最新代码
git pull
```

### 测试相关
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/unit/test_file.py -v

# 运行特定测试函数
pytest tests/unit/test_file.py::test_function -v

# 覆盖率
pytest tests/ --cov=app --cov-report=term-missing

# 详细输出
pytest tests/ -vv

# 停止在第一个失败
pytest tests/ -x

# 显示打印输出
pytest tests/ -s
```

### 文件编辑
```bash
# Vim
vim file.py
# 插入模式: i
# 退出不保存: :q!
# 保存退出: :wq

# Nano
nano file.py
# 保存: Ctrl+O
# 退出: Ctrl+X
```

---

## 循环示例：完整流程

```bash
# === 循环 1 ===
cd enterprise-ai-platform/auth-service
pytest tests/ --cov=app --cov-report=term-missing | grep -v "100%"
# 识别: app/models/user.py 需要测试
cd tests/unit
vim test_user_models.py
# [编写测试]
cd ../..
pytest tests/unit/test_user_models.py -v
# [如果失败，修复]
pytest tests/ --cov=app --cov-report=term-missing
git add -A
git commit -m "test: add user model tests"
git push

# === 循环 2 ===
cd ../auth-service  # 或下一个服务
pytest tests/ --cov=app --cov-report=term-missing | grep -v "100%"
# 识别: app/services/auth.py 需要测试
cd tests/unit
vim test_auth_service.py
# [编写测试]
cd ../..
pytest tests/unit/test_auth_service.py -v
pytest tests/ --cov=app --cov-report=term-missing
git add -A
git commit -m "test: add auth service tests"
git push

# === 重复... ===
```

---

## 目标追踪

### 每日目标
- [ ] 完成3-5个测试文件
- [ ] 覆盖率提升5-10%
- [ ] 修复所有相关bug
- [ ] 提交所有更改

### 每周目标
- [ ] auth-service 达到80%覆盖率
- [ ] 其他核心服务达到70%覆盖率
- [ ] 所有测试通过
- [ ] 文档更新

---

## 注意事项

1. **每次循环前先拉取最新代码**
   ```bash
   git pull
   ```

2. **测试失败时不要急于提交**
   ```bash
   # 确保所有测试通过
   pytest tests/ -v
   ```

3. **保持提交粒度小而频繁**
   ```bash
   # 每完成一个测试文件就提交
   git commit -m "test: add specific test"
   ```

4. **使用screen避免SSH断开**
   ```bash
   screen -S test-work
   ```

5. **定期检查总体进度**
   ```bash
   # 每天结束时运行
   pytest tests/ --cov=app --cov-report=term | grep "TOTAL"
   ```

---

## 开始循环

现在可以开始第一个循环：

```bash
ssh ai-platform-dev
cd enterprise-ai-platform/auth-service
pytest tests/ --cov=app --cov-report=term-missing
```

然后按照上述步骤，持续循环改进！
