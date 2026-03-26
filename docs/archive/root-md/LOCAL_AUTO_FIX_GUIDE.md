# 🖥️ 本地自动修复系统使用指南

## 📋 概述

在本地Windows电脑上运行自动修复系统，可以从GitHub Actions获取错误并自动修复代码。

## 🚀 快速开始

### 方法1: 使用PowerShell脚本（推荐，最简单）

```powershell
# 直接运行
powershell -ExecutionPolicy Bypass -File scripts\cicd\run-local-auto-fix.ps1
```

### 方法2: 使用Python venv

```powershell
# 使用venv运行
powershell -ExecutionPolicy Bypass -File scripts\cicd\run-local-auto-fix.ps1 -UseVenv
```

### 方法3: 使用Docker

```powershell
# 使用Docker运行
powershell -ExecutionPolicy Bypass -File scripts\cicd\run-local-auto-fix.ps1 -UseDocker
```

### 方法4: 直接运行Python脚本

```powershell
# 激活venv（如果需要）
.\venv\Scripts\Activate.ps1

# 运行Python脚本
python scripts\cicd\local-auto-fix.py
```

## 🔧 环境要求

### 必需
- ✅ GitHub CLI (`gh`) - [安装指南](https://cli.github.com/)
- ✅ Git
- ✅ Python 3.8+ (如果使用Python版本)

### 可选
- Docker Desktop (如果使用Docker方式)
- Node.js (用于验证修复)

## 📝 设置步骤

### 1. 安装GitHub CLI

```powershell
# 使用winget安装
winget install GitHub.cli

# 或使用Scoop
scoop install gh
```

### 2. 登录GitHub CLI

```powershell
gh auth login
```

选择：
- GitHub.com
- HTTPS
- 使用浏览器登录或粘贴token

### 3. 验证设置

```powershell
# 检查GitHub CLI
gh auth status

# 检查仓库访问
gh repo view PMLiuyubin/enterprise-ai-platform
```

## 🎯 使用方法

### 基本使用

```powershell
# 在项目根目录执行
cd E:\enterprise-ai-platform

# 运行自动修复
powershell -ExecutionPolicy Bypass -File scripts\cicd\run-local-auto-fix.ps1
```

### 工作流程

1. **获取最新失败运行**
   - 自动查找GitHub Actions中最新失败的运行

2. **下载日志**
   - 下载所有作业的日志到 `%TEMP%\github-errors\`

3. **分析错误**
   - 提取TypeScript错误
   - 识别错误类型

4. **自动修复**
   - 修复 `display_name` 缺失
   - 修复缺失的图标导入
   - 修复类型不匹配

5. **验证修复**
   - 运行TypeScript类型检查
   - 确保修复有效

6. **提交推送**
   - 自动提交修复
   - 推送到GitHub
   - 触发新的工作流

## 📊 日志位置

### Windows
```
%TEMP%\github-errors\run-<run-id>\
├── frontend-test.log
├── test.log
├── build-images.log
└── deploy.log
```

### 查看日志

```powershell
# 查看最新日志目录
Get-ChildItem $env:TEMP\github-errors | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# 查看特定日志
Get-Content $env:TEMP\github-errors\run-<run-id>\frontend-test.log
```

## 🔍 支持的自动修复

### 1. TypeScript类型错误

#### display_name缺失
```typescript
// 自动添加到User接口
export interface User {
  // ...
  display_name?: string
}
```

#### 图标导入缺失
```typescript
// 自动添加到导入
import { Table, Database, ... } from 'lucide-react'
```

#### 类型不匹配
```typescript
// 修复前
{IconComponent ? (
  <IconComponent />
) : (
  <span>{stat.icon}</span>  // ❌ 错误
)}

// 修复后
{IconComponent && (
  <IconComponent />  // ✅ 正确
)}
```

## 🐛 调试

### 查看详细输出

```powershell
# PowerShell脚本
$VerbosePreference = "Continue"
powershell -ExecutionPolicy Bypass -File scripts\cicd\local-auto-fix.ps1

# Python脚本
python scripts\cicd\local-auto-fix.py --verbose
```

### 只分析不修复

编辑脚本，注释掉提交部分，或创建测试版本。

## 🔄 自动化

### 创建定时任务

```powershell
# 使用任务计划程序
# 1. 打开"任务计划程序"
# 2. 创建基本任务
# 3. 触发器: 每天或每小时
# 4. 操作: 启动程序
#    程序: powershell.exe
#    参数: -ExecutionPolicy Bypass -File "E:\enterprise-ai-platform\scripts\cicd\run-local-auto-fix.ps1"
```

### 使用PowerShell后台作业

```powershell
# 启动后台作业
Start-Job -ScriptBlock {
    Set-Location "E:\enterprise-ai-platform"
    powershell -ExecutionPolicy Bypass -File scripts\cicd\run-local-auto-fix.ps1
}

# 查看作业状态
Get-Job

# 查看作业输出
Receive-Job -Id <JobId>
```

## 📋 完整示例

```powershell
# 1. 进入项目目录
cd E:\enterprise-ai-platform

# 2. 运行自动修复
powershell -ExecutionPolicy Bypass -File scripts\cicd\run-local-auto-fix.ps1

# 3. 查看结果
# 脚本会自动：
# - 获取最新失败运行
# - 下载日志
# - 分析错误
# - 修复代码
# - 验证修复
# - 提交推送

# 4. 查看新运行
gh run list --workflow=deploy.yml --limit 1
```

## ✅ 优势

1. **本地执行**: 无需服务器，在本地即可运行
2. **快速反馈**: 立即获取错误并修复
3. **自动化**: 无需手动查看日志和修复
4. **灵活**: 支持多种运行方式（PowerShell/Python/Docker）
5. **可扩展**: 易于添加新的修复规则

## 🔧 故障排除

### GitHub CLI未登录

```powershell
gh auth login
```

### 权限错误

```powershell
# 以管理员身份运行PowerShell
# 或设置执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python未安装

```powershell
# 使用winget安装
winget install Python.Python.3.11
```

---

**状态**: ✅ 本地自动修复系统已就绪，可以在本地Windows电脑上运行





