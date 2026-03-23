# SSH持久化连接 - 快速使用指南

## 🚀 快速开始

### 方法1: 双击运行（最简单）

直接双击 `ssh-connect-persistent.bat` 文件，会打开一个交互式菜单。

### 方法2: PowerShell命令

```powershell
# 打开交互式对话框
.\ssh-connect-persistent.ps1

# 或直接执行命令
.\scripts\deployment\ssh-persistent.ps1 -Action execute -Command "ls -la"
```

## 📋 交互式菜单选项

运行后会显示以下菜单：

```
=== SSH持久化连接管理器 ===
服务器: ubuntu@43.143.139.197:22

请选择操作:
[1] 1. 建立持久连接
[2] 2. 执行命令
[3] 3. 交互式Shell
[4] 4. 查看状态
[5] 5. 断开连接
[Q] Q. 退出
```

## ✨ 主要优势

1. **无需重复登录**: 建立一次连接后，后续命令自动复用
2. **快速执行**: 命令执行速度从3-5秒降低到<1秒
3. **自动管理**: 连接空闲10分钟后自动断开
4. **友好界面**: 提供交互式对话框，操作简单

## 🔧 工作原理

使用SSH的ControlMaster功能：
- 第一个连接作为"主连接"在后台保持
- 后续连接复用主连接，无需重新认证
- 连接信息保存在 `~/.ssh/control-*` 文件中

## 📝 使用示例

### 示例1: 建立连接并执行命令

```powershell
# 1. 打开交互式对话框
.\ssh-connect-persistent.ps1

# 2. 选择 "1. 建立持久连接"
# 3. 选择 "2. 执行命令"
# 4. 输入命令，如: ls -la
```

### 示例2: 命令行方式

```powershell
# 建立连接
.\scripts\deployment\ssh-persistent.ps1 -Action connect

# 执行命令（自动复用连接）
.\scripts\deployment\ssh-persistent.ps1 -Action execute -Command "docker ps"
.\scripts\deployment\ssh-persistent.ps1 -Action execute -Command "pwd"
```

## ⚠️ 注意事项

1. **首次使用**: 第一次建立连接需要正常登录认证
2. **连接超时**: 10分钟无活动后自动断开
3. **手动断开**: 使用菜单选项5或执行 `-Action disconnect`

## 🐛 故障排除

### 连接失败？

1. 检查网络连接
2. 检查SSH密钥文件是否存在
3. 手动删除旧连接文件：
   ```powershell
   Remove-Item ~/.ssh/control-* -Force
   ```

### 路径问题？

确保在项目根目录运行脚本，或使用绝对路径。

## 📚 详细文档

更多信息请查看: `docs/development-docs/SSH_PERSISTENT_CONNECTION.md`

