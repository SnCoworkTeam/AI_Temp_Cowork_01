# 核心服务测试指南

## 脚本功能

`scripts/cicd/test-core-services-first.py` 现在只负责：

1. **启动CI/CD工作流** - 自动触发GitHub Actions测试
2. **等待测试完成** - 监控工作流执行状态
3. **下载错误日志** - 自动下载失败的作业日志
4. **分析错误** - 提取并显示错误信息（不自动修复）
5. **提交代码** - 如果有代码修改，自动提交到Git

## 工作流程

```
启动工作流 → 等待完成 → 检查状态
                              ↓
                        有失败？
                              ↓
                    下载日志 → 分析错误 → 显示错误
                              ↓
                        有代码修改？
                              ↓
                    提交代码 → 等待新工作流
```

## 修复流程

1. **脚本自动下载日志** - 日志保存在 `%TEMP%\github-errors\run-{run_id}-frontend.log`
2. **脚本显示错误信息** - 在控制台显示发现的错误
3. **手动修复代码** - 根据错误信息手动修复代码
4. **脚本自动提交** - 修复后脚本会自动检测并提交代码

## 运行脚本

```powershell
python scripts\cicd\test-core-services-first.py
```

## 查看日志

日志文件位置：
- Windows: `%TEMP%\github-errors\run-{run_id}-frontend.log`
- Linux/Mac: `/tmp/github-errors/run-{run_id}-frontend.log`

## 核心服务优先级

脚本会优先测试以下核心服务：

1. **web-ui** - 前端服务（最重要）
2. **api-gateway** - API网关
3. **auth-service** - 认证服务
4. **workflow-engine** - 工作流引擎

## 注意事项

- 脚本会持续运行，直到所有核心服务测试通过
- 每次修复后会自动提交代码并触发新的测试
- 如果连续2次所有测试通过，脚本会自动停止
- 脚本不会自动修复代码，需要手动修复





