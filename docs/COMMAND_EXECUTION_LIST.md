# 测试覆盖率提升 - 命令执行清单

## ⚠️ 重要提示
**这些命令必须在原生Windows PowerShell或CMD中执行，不要通过Cursor的终端工具执行！**

## 执行方式
1. 按 `Win + R`，输入 `pwsh` 或 `cmd`，回车
2. 切换到项目目录：`cd E:\enterprise-ai-platform`
3. 按顺序执行以下命令

---

## 阶段1: 检查覆盖率（已完成 ✅）

```bash
# 已在Cursor中完成，跳过
```

---

## 阶段2: auth-service 测试覆盖率提升

### 2.1 生成测试文件（已完成 ✅）
```bash
py scripts/test-coverage/improve-coverage.py --service auth-service
```
**结果**: 已生成15个测试文件

### 2.2 提交测试文件
```bash
git add auth-service/tests/unit/test_*.py
git commit -m "test: 添加auth-service测试文件以提升覆盖率"
git push origin main
```

### 2.3 在服务器上拉取代码
```bash
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 10 git pull origin main"
```

### 2.4 在服务器Docker中执行测试
```bash
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 120 bash scripts/test-coverage/run-tests-in-docker.sh"
```

### 2.5 下载测试结果
```bash
scp -F remote.ssh enterprise-ai-server:/tmp/.test-results.json .test-results.json
```

### 2.6 自动修复测试错误
```bash
py scripts/test-coverage/auto-fix-tests.py --test-results .test-results.json
```

### 2.7 提交修复后的文件
```bash
git add .
git commit -m "fix: 修复auth-service测试错误"
git push origin main
```

### 2.8 验证覆盖率
```bash
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 120 bash scripts/test-coverage/check-coverage-server.sh"
```

### 2.9 检查覆盖率结果
```bash
scp -F remote.ssh enterprise-ai-server:/tmp/.coverage-status.json .coverage-status.json
py -c "import json; data=json.load(open('.coverage-status.json')); print('auth-service覆盖率:', data['services']['auth-service']['coverage'], '%')"
```

**如果覆盖率 < 80%，重复步骤 2.1-2.9**

---

## 阶段3-7: 其他服务（knowledge-base, metadata-service, workflow-engine, mcp-gateway, database）

对每个服务重复阶段2的步骤，将 `auth-service` 替换为对应的服务名：

```bash
# 示例：knowledge-base
py scripts/test-coverage/improve-coverage.py --service knowledge-base
git add knowledge-base/tests/unit/test_*.py
git commit -m "test: 添加knowledge-base测试文件"
git push origin main
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 10 git pull origin main"
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 120 bash scripts/test-coverage/run-tests-in-docker.sh"
scp -F remote.ssh enterprise-ai-server:/tmp/.test-results.json .test-results.json
py scripts/test-coverage/auto-fix-tests.py --test-results .test-results.json
git add .; git commit -m "fix: 修复knowledge-base测试错误"; git push origin main
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 120 bash scripts/test-coverage/check-coverage-server.sh"
```

---

## 最终验证

```bash
ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 120 bash scripts/test-coverage/check-coverage-server.sh"
scp -F remote.ssh enterprise-ai-server:/tmp/.coverage-status.json .coverage-status.json
py -c "import json; data=json.load(open('.coverage-status.json')); print('所有服务覆盖率:'); [print(f\"  {k}: {v['coverage']}%\") for k,v in data['services'].items()]; print('\\n全部达到80%:', data['all_above_80'])"
```

---

## 注意事项

1. **所有SSH命令都设置了10秒连接超时** (`-o ConnectTimeout=10`)
2. **远程命令都设置了执行超时** (`timeout 10` 或 `timeout 120`)
3. **如果命令卡住，按 `Ctrl + C` 中断，然后重试**
4. **如果SSH连接失败，等待几秒后重试**
5. **每次执行前确保在正确的目录** (`E:\enterprise-ai-platform`)

