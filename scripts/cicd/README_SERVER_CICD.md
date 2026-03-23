# 🚀 服务器端CI/CD完整方案

## 📋 概述

在服务器 `43.143.139.197` 上直接运行完整的CI/CD流程，包括：
- ✅ 后端测试
- ✅ 前端测试和构建
- ✅ Docker镜像构建
- ✅ 部署
- ✅ 验证

## 🔧 快速开始

### 1. 上传脚本到服务器

```powershell
# 在本地执行
scp -i enterprise_ai_platform.pem scripts/cicd/*.sh ubuntu@43.143.139.197:/opt/enterprise-ai-platform/scripts/cicd/
```

### 2. 在服务器上设置权限

```bash
# SSH到服务器
ssh -i enterprise_ai_platform.pem ubuntu@43.143.139.197

# 设置执行权限
cd /opt/enterprise-ai-platform
chmod +x scripts/cicd/*.sh
```

### 3. 执行CI/CD流程

```bash
# 运行完整CI/CD流程
bash scripts/cicd/server-cicd-pipeline.sh
```

## 📊 执行流程

### 阶段1: 环境准备
- 拉取最新代码
- 检查Docker服务
- 验证环境

### 阶段2: 后端测试
- 启动测试依赖（PostgreSQL, Redis）
- 运行单元测试
- 运行集成测试
- 运行前端API集成测试

### 阶段3: 前端测试
- 安装依赖
- Lint检查
- TypeScript类型检查
- 构建前端

### 阶段4: Docker镜像构建
- 构建所有核心服务镜像
- 验证构建结果

### 阶段5: 部署
- 运行数据库迁移
- 启动所有服务
- 健康检查

### 阶段6: 验证
- 检查服务状态
- 验证API端点
- 生成报告

## 📝 日志和报告

### 日志位置
```
/tmp/cicd-logs/<timestamp>/
├── backend-tests.log      # 后端测试日志
├── frontend-tests.log     # 前端测试日志
├── docker-build.log       # Docker构建日志
├── verification.log       # 验证日志
├── cicd-report.txt        # 实时报告
└── full-report.txt        # 完整报告
```

### 查看日志

```bash
# 查看最新日志目录
ls -lt /tmp/cicd-logs/ | head -5

# 查看完整报告
cat /tmp/cicd-logs/<latest>/full-report.txt

# 查看特定阶段日志
cat /tmp/cicd-logs/<latest>/frontend-tests.log
```

## 🔄 自动化循环执行

### 创建定时任务（Cron）

```bash
# 编辑crontab
crontab -e

# 每天凌晨2点执行
0 2 * * * /opt/enterprise-ai-platform/scripts/cicd/server-cicd-pipeline.sh >> /tmp/cicd-cron.log 2>&1

# 每6小时执行一次
0 */6 * * * /opt/enterprise-ai-platform/scripts/cicd/server-cicd-pipeline.sh >> /tmp/cicd-cron.log 2>&1
```

### 使用systemd服务

创建 `/etc/systemd/system/server-cicd.service`:

```ini
[Unit]
Description=Server CI/CD Pipeline
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/opt/enterprise-ai-platform
ExecStart=/bin/bash /opt/enterprise-ai-platform/scripts/cicd/server-cicd-pipeline.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

创建定时器 `/etc/systemd/system/server-cicd.timer`:

```ini
[Unit]
Description=Run Server CI/CD Pipeline
Requires=server-cicd.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用定时器：
```bash
sudo systemctl enable server-cicd.timer
sudo systemctl start server-cicd.timer
```

## 🐛 错误处理

### 查看失败原因

```bash
# 查看最新报告
cat /tmp/cicd-logs/$(ls -t /tmp/cicd-logs/ | head -1)/full-report.txt

# 查看错误日志
grep -i "error\|failed\|fail" /tmp/cicd-logs/$(ls -t /tmp/cicd-logs/ | head -1)/*.log
```

### 常见问题修复

#### 1. 前端构建失败

```bash
cd /opt/enterprise-ai-platform/web-ui
npm ci --legacy-peer-deps
npm run build
```

#### 2. Docker构建失败

```bash
cd /opt/enterprise-ai-platform
docker-compose build <服务名>
```

#### 3. 服务启动失败

```bash
# 查看服务日志
docker-compose logs <服务名>

# 重启服务
docker-compose restart <服务名>
```

## 📧 通知配置（可选）

### 发送邮件通知

在脚本末尾添加：

```bash
# 如果失败，发送邮件
if [ $? -ne 0 ]; then
    echo "CI/CD失败" | mail -s "CI/CD失败报告" admin@example.com < "$REPORT_FILE"
fi
```

### 发送Webhook通知

```bash
# 发送到Slack/Discord等
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"CI/CD执行完成: $([ $? -eq 0 ] && echo '成功' || echo '失败')\"}"
```

## 🔍 监控和告警

### 检查CI/CD状态

```bash
# 查看最后一次执行时间
ls -lt /tmp/cicd-logs/ | head -1

# 检查是否成功
grep "CI/CD流程" /tmp/cicd-logs/$(ls -t /tmp/cicd-logs/ | head -1)/full-report.txt
```

### 设置告警

```bash
# 如果24小时内没有新的成功执行，发送告警
LAST_SUCCESS=$(find /tmp/cicd-logs -name "full-report.txt" -exec grep -l "全部通过" {} \; | xargs ls -t | head -1)
if [ -z "$LAST_SUCCESS" ] || [ $(find "$LAST_SUCCESS" -mtime +1) ]; then
    echo "警告: CI/CD超过24小时未成功执行" | mail -s "CI/CD告警" admin@example.com
fi
```

## ✅ 优势

1. **快速反馈**: 在服务器上直接执行，无需等待GitHub Actions
2. **完整控制**: 可以自定义测试流程和部署步骤
3. **资源利用**: 充分利用服务器资源
4. **日志集中**: 所有日志保存在服务器上，方便查看
5. **自动化**: 可以设置定时执行

## 📋 与GitHub Actions的对比

| 特性 | 服务器端CI/CD | GitHub Actions |
|------|-------------|----------------|
| 执行速度 | 快（本地执行） | 中等（需要启动runner） |
| 资源消耗 | 使用服务器资源 | 使用GitHub资源 |
| 日志访问 | 直接访问 | 需要通过API |
| 自定义性 | 高 | 中等 |
| 成本 | 服务器成本 | GitHub Actions分钟数 |

---

**状态**: ✅ 服务器端CI/CD方案已就绪





