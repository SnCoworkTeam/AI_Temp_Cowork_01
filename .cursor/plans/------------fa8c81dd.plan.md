<!-- fa8c81dd-17d7-404b-aa1d-d0e9cc63b48b ea73a68f-646c-4bef-91a0-3a847885e260 -->
# 测试覆盖率80%提升执行计划

## 当前状态

- ✅ 所有服务的测试文件已生成（124个文件）
- ✅ 测试文件已提交到Git仓库
- ⚠️ 服务器Docker容器未运行，无法在服务器执行测试
- ✅ 本地测试脚本可用

## 执行策略

采用混合方式：先在本地运行测试并修复错误，然后尝试服务器验证。

## 执行步骤

### 阶段1：本地测试执行和修复（所有服务）

对每个服务（auth-service, knowledge-base, metadata-service, workflow-engine, mcp-gateway, database）执行：

1. **本地运行测试**

- 使用 `tests/run-tests-local.ps1` 或 `py -m pytest` 运行服务测试
- 生成覆盖率报告：`--cov=<service>/src --cov-report=json:.coverage-<service>.json`
- 命令：`cd <service>; py -m pytest tests/unit/ --cov=src --cov-report=json:.coverage.json --cov-report=term-missing`

2. **分析测试结果**

- 检查测试失败原因
- 识别常见错误：导入错误、依赖缺失、Mock配置错误等

3. **自动修复测试错误**

- 运行 `py scripts/test-coverage/auto-fix-tests.py --test-results .coverage-<service>.json`
- 手动修复自动修复脚本无法处理的错误

4. **验证修复**

- 重新运行测试确保修复有效
- 检查覆盖率是否提升

5. **提交修复**

- `git add <service>/tests/; git commit -m "fix: 修复<service>测试错误"; git push origin main`

### 阶段2：覆盖率验证和迭代

1. **检查覆盖率**

- 对每个服务检查覆盖率：`py -c "import json; data=json.load(open('.coverage-<service>.json')); print(f\"Coverage: {data['totals']['percent_covered']:.2f}%\")"`
- 如果覆盖率 < 80%，继续生成更多测试

2. **生成补充测试**

- 运行 `py scripts/test-coverage/improve-coverage.py --service <service-name>` 生成缺失的测试
- 重复阶段1直到达到80%

### 阶段3：服务器验证（可选）

如果Docker问题解决：

1. **上传代码到服务器**

- `ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 10 git pull origin main"`

2. **在服务器Docker中验证**

- `ssh -F remote.ssh -o ConnectTimeout=10 enterprise-ai-server "cd /opt/enterprise-ai-platform; timeout 120 bash scripts/test-coverage/check-coverage-server.sh"`
- 下载覆盖率结果验证

## 关键文件

- [tests/run-tests-local.ps1](tests/run-tests-local.ps1) - 本地测试执行脚本
- [scripts/test-coverage/auto-fix-tests.py](scripts/test-coverage/auto-fix-tests.py) - 自动修复测试错误
- [scripts/test-coverage/improve-coverage.py](scripts/test-coverage/improve-coverage.py) - 生成测试文件
- [pytest.ini](pytest.ini) - pytest配置

## 注意事项

- 所有命令在 `E:\enterprise-ai-platform` 目录执行
- 使用分号 `;` 分隔Windows命令
- 如果命令超时，等待2秒后重试，最多3次
- 优先修复导入错误和依赖问题
- 确保测试使用正确的Mock对象和fixtures

### To-dos

- [ ] 在本地运行auth-service测试，生成覆盖率报告，分析并修复测试错误
- [ ] 在本地运行knowledge-base测试，生成覆盖率报告，分析并修复测试错误
- [ ] 在本地运行metadata-service测试，生成覆盖率报告，分析并修复测试错误
- [ ] 在本地运行workflow-engine测试，生成覆盖率报告，分析并修复测试错误
- [ ] 在本地运行mcp-gateway测试，生成覆盖率报告，分析并修复测试错误
- [ ] 在本地运行database测试，生成覆盖率报告，分析并修复测试错误
- [ ] 验证所有服务覆盖率，如果未达到80%则生成补充测试并重复测试-修复循环
- [ ] 如果Docker问题解决，在服务器上验证最终覆盖率