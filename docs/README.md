# 项目文档目录

本目录包含项目的所有文档和脚本文件，按功能分类组织。

## 目录结构

```
docs/
├── troubleshooting/          # 故障排查文档
│   ├── README.md            # 故障排查文档说明
│   ├── 修复*.txt            # 各种问题修复步骤
│   ├── 排查*.txt            # 问题排查指南
│   ├── 检查*.txt            # 系统检查命令
│   ├── 验证*.txt            # 修复验证步骤
│   └── *.md                 # 问题分析文档
│
├── deployment/               # 部署相关文档
│   ├── commands/            # 部署命令文档（服务器端执行）
│   │   ├── README.md        # 部署命令说明
│   │   ├── 启动*.txt        # 服务启动命令
│   │   ├── 快速*.txt        # 快速启动脚本
│   │   ├── 修复*.txt        # 修复命令（上传后执行）
│   │   └── 服务器*.txt      # 服务器端命令
│   │
│   ├── scripts/             # 部署脚本（本地执行）
│   │   ├── README.md        # 部署脚本说明
│   │   ├── 上传*.ps1        # PowerShell上传脚本
│   │   └── *.ps1            # 其他PowerShell脚本
│   │
│   ├── *.md                 # 部署相关Markdown文档
│   └── README.md            # 部署文档说明
│
└── quick-start/             # 快速开始指南（预留目录）
```

## 文档说明

### troubleshooting/ - 故障排查文档

包含所有问题修复和排查相关的文档：
- 修复步骤文档
- 问题排查指南
- 错误解决方案

### deployment/commands/ - 部署命令文档

包含服务器端执行的命令文档：
- 服务启动命令
- 服务器修复命令
- 快速启动脚本

### deployment/scripts/ - 部署脚本

包含本地执行的脚本文件：
- PowerShell 上传脚本
- 自动化部署脚本
- 文件上传脚本

### deployment/ - 部署文档

包含部署相关的 Markdown 文档：
- 部署指南
- 部署状态
- GitHub 上传指南

## 使用说明

1. **查找故障排查文档**：查看 `troubleshooting/` 目录
2. **查找部署命令**：查看 `deployment/commands/` 目录
3. **查找部署脚本**：查看 `deployment/scripts/` 目录
4. **查找快速启动指南**：查看 `quick-start/` 目录

## 注意事项

- 所有文档已按功能分类整理
- 脚本文件已移动到 `deployment/scripts/` 目录
- 命令文档已移动到 `deployment/commands/` 目录
- 故障排查文档已移动到 `troubleshooting/` 目录
