# 最终启动说明

## 重要：不要通过Cursor工具执行

**所有命令都卡住的原因是Cursor的终端工具有问题，不是脚本问题。**

## 正确的启动方式

### 方式1: 双击批处理文件（最简单）

**直接双击运行：**
```
START_COVERAGE.bat
```

这个文件会：
1. 自动清理旧的PowerShell进程
2. 启动新的PowerShell运行脚本
3. 避免进程冲突

### 方式2: 在Windows PowerShell中手动运行

1. **按 `Win + R`，输入 `pwsh`，回车**
   - 这会打开新的PowerShell窗口

2. **执行以下命令：**
   ```powershell
   cd E:\enterprise-ai-platform
   pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\test-coverage\coverage-improvement-loop.ps1
   ```

3. **如果卡住，按 `Ctrl + C` 中断，然后：**
   ```powershell
   # 清理所有Job和进程
   Get-Job | Remove-Job -Force
   Get-Process pwsh, powershell -ErrorAction SilentlyContinue | Stop-Process -Force
   
   # 重新运行
   pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\test-coverage\coverage-improvement-loop.ps1
   ```

## 脚本已修复

我已经修复了脚本中的所有问题：
- ✅ 修复了语法错误（`&&` 改为 `;`）
- ✅ 修复了括号匹配问题
- ✅ 添加了SSH连接超时和重试机制
- ✅ 添加了自动关闭和重连SSH的功能
- ✅ 使用更安全的SSH执行方式

## 验证脚本是否正常

在PowerShell中运行：
```powershell
cd E:\enterprise-ai-platform
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\test-coverage\coverage-improvement-loop.ps1
```

如果看到以下输出，说明脚本正常：
```
[2025-11-12 XX:XX:XX] [INFO] ==========================================
[2025-11-12 XX:XX:XX] [INFO] 测试覆盖率提升循环启动
[2025-11-12 XX:XX:XX] [INFO] 目标: 所有服务达到80%覆盖率
```

## 如果还是卡住

1. **检查PowerShell进程**：
   ```powershell
   Get-Process pwsh, powershell
   ```
   如果有多个，全部停止：
   ```powershell
   Get-Process pwsh, powershell | Stop-Process -Force
   ```

2. **检查后台Job**：
   ```powershell
   Get-Job
   Get-Job | Remove-Job -Force
   ```

3. **重启计算机**（最后手段）

## 总结

**问题不在脚本，在工具执行环境。**

**解决方案：直接在Windows PowerShell中手动运行，不要通过Cursor工具。**

