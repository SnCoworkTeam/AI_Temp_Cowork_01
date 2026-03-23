# 部署脚本

本目录包含所有本地执行的部署脚本文件。

## 脚本分类

### PowerShell 上传脚本
- `上传*.ps1` - 各种文件的上传脚本
- `上传修复*.ps1` - 修复文件的上传脚本

### 其他脚本
- `启动所有服务.ps1` - 启动所有服务的脚本
- `快速检查服务.ps1` - 快速检查服务状态的脚本
- `整理项目文档.ps1` - 整理项目文档的脚本

## 使用说明

### 执行 PowerShell 脚本

在本地 Windows PowerShell 中执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\docs\deployment\scripts\<script-name>.ps1
```

### 上传文件脚本

大多数上传脚本用于将修复后的文件上传到服务器：

```powershell
# 示例：上传修复后的 docker-compose.yml
powershell -ExecutionPolicy Bypass -File .\docs\deployment\scripts\上传修复command-PYTHONPATH.ps1
```

## 脚本列表

### 上传脚本
- `上传docker-compose.yml.ps1` - 上传 docker-compose.yml
- `上传修复base.py.ps1` - 上传修复后的 base.py
- `上传修复main.py.ps1` - 上传修复后的 main.py
- `上传修复requirements.txt.ps1` - 上传修复后的 requirements.txt
- `上传修复所有metadata模型.ps1` - 上传所有修复后的模型文件
- 等等...

### 其他脚本
- `启动所有服务.ps1` - 启动所有服务
- `快速检查服务.ps1` - 快速检查服务状态

## 注意事项

1. 执行脚本前，确保已配置正确的 SSH 密钥路径
2. 确保服务器地址和路径正确
3. 某些脚本需要管理员权限

