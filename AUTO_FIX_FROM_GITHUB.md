# 🤖 自动从GitHub Actions获取错误并修复

## 🎯 功能

自动从GitHub Actions获取CI/CD执行错误，分析错误类型，自动修复代码，然后提交推送。

## 🚀 快速开始

### 1. 上传脚本到服务器

```powershell
# 在本地执行
scp -i enterprise_ai_platform.pem scripts/cicd/*.sh scripts/cicd/*.py ubuntu@43.143.139.197:/opt/enterprise-ai-platform/scripts/cicd/
```

### 2. 在服务器上设置权限

```bash
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform
chmod +x scripts/cicd/*.sh
chmod +x scripts/cicd/*.py
```

### 3. 执行自动修复

```bash
# 智能自动修复（推荐）
bash scripts/cicd/smart-auto-fix.sh

# 或使用基础版本
bash scripts/cicd/auto-fix-from-github.sh
```

## 📋 工作流程

```
1. 获取最新失败的GitHub Actions运行
   ↓
2. 下载所有作业的日志
   ↓
3. 使用AI分析错误（Python脚本）
   ↓
4. 生成修复建议
   ↓
5. 自动应用修复
   ↓
6. 验证修复（类型检查）
   ↓
7. 提交并推送到Git
   ↓
8. 等待新的GitHub Actions运行
```

## 🔍 支持的自动修复

### TypeScript错误

1. **缺失属性** (如 `display_name`)
   - 自动添加到接口定义

2. **缺失导入** (如 `Table` 图标)
   - 自动添加到导入语句

3. **类型不匹配** (如 `LucideIcon` 不能作为 `ReactNode`)
   - 移除错误的else分支
   - 修复条件渲染

### 构建错误

1. **缺失模块**
   - 识别并提示安装

2. **依赖冲突**
   - 使用 `--legacy-peer-deps`

## 📊 日志和分析

### 日志位置

```
/tmp/github-errors/run-<run-id>/
├── frontend-test.log      # 前端测试日志
├── test.log               # 后端测试日志
├── build-images.log       # 构建日志
├── analysis.txt           # AI分析结果
└── error-analysis.json    # 结构化错误数据
```

### 查看分析结果

```bash
# 查看AI分析
cat /tmp/github-errors/run-<latest>/analysis.txt

# 查看JSON格式的错误数据
cat /tmp/github-errors/run-<latest>/error-analysis.json | jq
```

## 🔄 自动化循环

### 创建监控脚本

创建 `scripts/cicd/monitor-and-fix.sh`:

```bash
#!/bin/bash
# 持续监控并自动修复

while true; do
    echo "检查GitHub Actions状态..."
    
    # 运行自动修复
    bash scripts/cicd/smart-auto-fix.sh
    
    # 等待5分钟
    sleep 300
done
```

### 使用systemd服务

创建 `/etc/systemd/system/auto-fix-cicd.service`:

```ini
[Unit]
Description=Auto Fix CI/CD Errors
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/enterprise-ai-platform
ExecStart=/bin/bash /opt/enterprise-ai-platform/scripts/cicd/smart-auto-fix.sh
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable auto-fix-cicd.service
sudo systemctl start auto-fix-cicd.service
```

## 🛠️ 手动触发修复

```bash
# 修复特定运行
RUN_ID=<运行ID>
bash scripts/cicd/auto-fix-from-github.sh --run-id $RUN_ID

# 只分析不修复
python3 scripts/cicd/ai-fix-helper.py /tmp/github-errors/run-<run-id>
```

## 📝 扩展修复规则

编辑 `scripts/cicd/ai-fix-helper.py` 添加新的修复规则：

```python
# 添加新的错误模式
if '新的错误模式' in message:
    # 应用修复逻辑
    pass
```

## ✅ 优势

1. **自动化**: 无需手动查看日志和修复
2. **智能分析**: 使用AI分析错误模式
3. **快速反馈**: 自动提交修复，触发新运行
4. **可扩展**: 易于添加新的修复规则
5. **日志完整**: 保存所有分析结果

## 🔍 调试

### 查看详细日志

```bash
# 启用调试模式
set -x
bash scripts/cicd/smart-auto-fix.sh
```

### 测试修复逻辑

```bash
# 只分析不修复
python3 scripts/cicd/ai-fix-helper.py /tmp/github-errors/run-<run-id>

# 查看会应用哪些修复
bash scripts/cicd/smart-auto-fix.sh --dry-run
```

---

**状态**: ✅ 自动修复系统已就绪





