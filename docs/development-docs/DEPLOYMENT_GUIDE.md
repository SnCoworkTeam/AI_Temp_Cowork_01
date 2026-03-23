# 服务器部署与自动化运维指南

## 📋 目录

1. [服务器部署](#服务器部署)
2. [自动化测试](#自动化测试)
3. [自动化修复Bug](#自动化修复bug)
4. [监控与告警](#监控与告警)
5. [CI/CD配置](#cicd配置)

---

## 🚀 服务器部署

### 1. 服务器准备

#### 1.1 系统要求

```bash
# 操作系统: Ubuntu 20.04+ / CentOS 7+ / Debian 11+
# 最低配置:
- CPU: 4核心
- 内存: 8GB
- 磁盘: 50GB SSD
- 网络: 100Mbps

# 推荐配置:
- CPU: 8核心+
- 内存: 16GB+
- 磁盘: 100GB+ SSD
- 网络: 1Gbps
```

#### 1.2 安装Docker和Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 1.3 安装其他依赖

```bash
# Git
sudo apt-get update
sudo apt-get install -y git

# 可选: Nginx (用于反向代理)
sudo apt-get install -y nginx
```

### 2. 代码部署

#### 2.1 克隆代码

```bash
# 创建项目目录
sudo mkdir -p /opt/enterprise-ai-platform
sudo chown $USER:$USER /opt/enterprise-ai-platform
cd /opt/enterprise-ai-platform

# 克隆代码（替换为你的仓库地址）
git clone https://github.com/PMLiuyubin/enterprise-ai-platform.git .

# 或者从本地同步
# rsync -avz --exclude='.git' /path/to/local/repo/ /opt/enterprise-ai-platform/
```

#### 2.2 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env.prod

# 编辑生产环境配置
nano .env.prod
```

**必需的环境变量：**

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@postgres:5432/enterprise_ai
REDIS_HOST=redis
REDIS_PORT=6379

# 服务端口
MCP_GATEWAY_PORT=8001
WORKFLOW_ENGINE_PORT=8002
AUTH_SERVICE_PORT=8003
KNOWLEDGE_BASE_PORT=8004
WEB_UI_PORT=3000

# 安全配置
JWT_SECRET_KEY=your-super-secret-jwt-key-here
ENCRYPTION_KEY=your-encryption-key-here

# LLM配置（DeepSeek或OpenAI）
OPENAI_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://api.deepseek.com/v1  # DeepSeek使用此URL
LLM_MODEL=deepseek-chat  # 或 gpt-4

# 日志级别
LOG_LEVEL=INFO

# 域名配置（如果有）
DOMAIN=your-domain.com
NEXT_PUBLIC_MCP_GATEWAY_URL=http://your-domain.com:8001
NEXT_PUBLIC_WORKFLOW_ENGINE_URL=http://your-domain.com:8002
```

#### 2.3 部署数据库（如果使用外部数据库，可跳过）

```bash
# 使用Docker Compose部署PostgreSQL和Redis
docker-compose -f docker-compose.db.yml up -d

# 等待数据库启动
sleep 10

# 验证数据库连接
docker-compose -f docker-compose.db.yml ps
```

#### 2.4 构建和启动服务

```bash
# 构建所有服务镜像
docker-compose -f docker-compose.prod.yml build

# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

#### 2.5 运行数据库迁移

```bash
# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec mcp-gateway alembic upgrade head
docker-compose -f docker-compose.prod.yml exec workflow-engine alembic upgrade head
docker-compose -f docker-compose.prod.yml exec auth-service alembic upgrade head
docker-compose -f docker-compose.prod.yml exec knowledge-base alembic upgrade head
```

#### 2.6 验证部署

```bash
# 检查服务健康状态
curl http://localhost:8001/api/health  # MCP Gateway
curl http://localhost:8002/api/health  # Workflow Engine
curl http://localhost:8003/api/health  # Auth Service
curl http://localhost:8004/api/health  # Knowledge Base
curl http://localhost:3000/api/health  # Web UI

# 检查自动化调试系统
curl http://localhost:8001/api/health  # 应该包含auto_debug信息
```

### 3. Nginx反向代理配置（可选）

```bash
# 创建Nginx配置文件
sudo nano /etc/nginx/sites-available/enterprise-ai-platform
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # MCP Gateway
    location /api/mcp/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Workflow Engine
    location /api/workflow/ {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Auth Service
    location /api/auth/ {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Knowledge Base
    location /api/kb/ {
        proxy_pass http://localhost:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Web UI
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/enterprise-ai-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🧪 自动化测试

### 1. 本地测试

```bash
# 安装测试依赖
pip install -r tests/requirements.txt

# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test-integration/  # 集成测试
pytest tests/test-performance/  # 性能测试
pytest tests/test-security/     # 安全测试

# 生成测试报告
pytest --cov=. --cov-report=html --cov-report=term tests/
```

### 2. CI/CD自动化测试

项目已配置GitHub Actions自动测试，每次代码推送都会自动运行：

```bash
# 查看GitHub Actions配置
cat .github/workflows/quality-assurance.yml

# 测试会在以下情况自动触发:
# - 代码推送到main/develop分支
# - 创建Pull Request
# - 手动触发workflow
```

**测试流程包括：**
- 代码静态分析
- 依赖安全检查
- 单元测试
- 集成测试
- 代码覆盖率检查
- 质量门禁验证

### 3. 服务器端自动化测试

创建测试脚本：

```bash
# 创建测试脚本
nano /opt/enterprise-ai-platform/scripts/test-deployment.sh
```

```bash
#!/bin/bash
# 部署验证测试脚本

set -e

BASE_URL="${BASE_URL:-http://localhost}"

echo "开始部署验证测试..."

# 健康检查
echo "1. 检查服务健康状态..."
services=("8001" "8002" "8003" "8004" "3000")
for port in "${services[@]}"; do
    if curl -f "${BASE_URL}:${port}/api/health" > /dev/null 2>&1; then
        echo "✅ 服务 ${port} 健康"
    else
        echo "❌ 服务 ${port} 不健康"
        exit 1
    fi
done

# API端点测试
echo "2. 测试API端点..."
# 添加具体的API测试

# 功能测试
echo "3. 运行功能测试..."
cd /opt/enterprise-ai-platform
pytest tests/test-integration/ -v

echo "✅ 所有测试通过"
```

```bash
# 设置执行权限
chmod +x /opt/enterprise-ai-platform/scripts/test-deployment.sh

# 运行测试
/opt/enterprise-ai-platform/scripts/test-deployment.sh
```

### 4. 定时自动化测试

使用cron定时运行测试：

```bash
# 编辑crontab
crontab -e

# 每天凌晨2点运行测试
0 2 * * * cd /opt/enterprise-ai-platform && /usr/bin/docker-compose -f docker-compose.prod.yml exec -T workflow-engine pytest tests/ >> /var/log/enterprise-ai-test.log 2>&1
```

---

## 🔧 自动化修复Bug

### 1. 启用自动化调试系统

自动化调试系统已经集成到平台中，需要配置启用：

#### 1.1 配置平台集成

```bash
# 编辑配置文件
nano /opt/enterprise-ai-platform/config/platform_integration.yaml
```

确保以下配置正确：
- 服务监控端点
- 管理API端点
- 数据访问权限
- 安全边界设置

#### 1.2 配置决策规则

```bash
# 编辑决策规则
nano /opt/enterprise-ai-platform/config/decision_rules.yaml
```

配置自动执行场景：
- 低风险配置修改
- 已知错误模式的标准修复
- 非业务时间的紧急修复

#### 1.3 启动自动化调试服务

自动化调试系统作为服务的一部分运行，无需单独启动。但需要确保：

```bash
# 检查自动化调试系统是否可用
curl http://localhost:8001/api/health | grep -i "auto_debug"

# 查看自动化调试日志
docker-compose -f docker-compose.prod.yml logs | grep -i "auto_debug"
```

### 2. 测试自动化修复

#### 2.1 模拟错误场景

```bash
# 创建测试脚本
nano /opt/enterprise-ai-platform/scripts/test-auto-fix.sh
```

```bash
#!/bin/bash
# 测试自动化修复功能

# 1. 提交一个测试错误到自动化调试系统
curl -X POST http://localhost:8001/api/auto-debug/submit-error \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "MCP tool execution failed: connection timeout",
    "error_category": "mcp_tool",
    "context": {
      "tool_name": "sap_query",
      "service": "mcp-gateway"
    }
  }'

# 2. 检查调试任务状态
curl http://localhost:8001/api/auto-debug/tasks

# 3. 查看修复建议
curl http://localhost:8001/api/auto-debug/tasks/{task_id}/analysis
```

#### 2.2 监控自动化修复过程

```bash
# 实时查看自动化调试日志
docker-compose -f docker-compose.prod.yml logs -f | grep -i "auto_debug\|auto_fix"

# 查看修复历史
curl http://localhost:8001/api/auto-debug/history
```

### 3. 配置自动修复策略

编辑 `config/debug_workflows.yaml` 配置自动修复工作流：

```yaml
# 错误检测工作流
error_detection:
  triggers:
    - monitoring_alert
    - error_log
  steps:
    - action: collect_error_logs
    - action: analyze_root_cause
    - action: generate_fix_plan
    - action: apply_fix  # 自动应用修复
    - action: validate_fix
```

### 4. 人工决策接口

访问Web UI的决策面板：

```bash
# 访问自动化调试决策面板
# http://your-domain.com/admin/auto-debug/decision-panel
```

功能包括：
- 查看错误分析报告
- 审查修复方案
- 批准/拒绝修复建议
- 跟踪修复效果

---

## 📊 监控与告警

### 1. 服务监控

#### 1.1 健康检查

```bash
# 创建健康检查脚本
nano /opt/enterprise-ai-platform/scripts/health-check.sh
```

```bash
#!/bin/bash
# 健康检查脚本

services=(
  "mcp-gateway:8001"
  "workflow-engine:8002"
  "auth-service:8003"
  "knowledge-base:8004"
  "web-ui:3000"
)

for service in "${services[@]}"; do
  name=$(echo $service | cut -d: -f1)
  port=$(echo $service | cut -d: -f2)
  
  if curl -f http://localhost:${port}/api/health > /dev/null 2>&1; then
    echo "✅ ${name} is healthy"
  else
    echo "❌ ${name} is unhealthy"
    # 发送告警
    # 可以集成邮件、Slack、钉钉等通知
  fi
done
```

#### 1.2 定时监控

```bash
# 添加到crontab
crontab -e

# 每5分钟检查一次
*/5 * * * * /opt/enterprise-ai-platform/scripts/health-check.sh >> /var/log/health-check.log 2>&1
```

### 2. 日志监控

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f mcp-gateway

# 查看错误日志
docker-compose -f docker-compose.prod.yml logs | grep -i error

# 查看自动化调试日志
docker-compose -f docker-compose.prod.yml logs | grep -i "auto_debug"
```

### 3. 性能监控

```bash
# 查看资源使用情况
docker stats

# 查看API响应时间
# 通过自动化调试系统的监控功能
curl http://localhost:8001/api/monitoring/metrics
```

---

## 🔄 CI/CD配置

### 1. GitHub Actions配置

项目已包含以下GitHub Actions工作流：

- **`.github/workflows/quality-assurance.yml`** - 代码质量检查
- **`.github/workflows/code-health.yml`** - 代码健康度检查
- **`.github/workflows/dependency-scan.yml`** - 依赖扫描
- **`.github/workflows/release.yml`** - 发布流程

### 2. 自动部署配置

创建自动部署工作流：

```bash
# 创建部署工作流
nano .github/workflows/deploy.yml
```

```yaml
name: Deploy to Server

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/enterprise-ai-platform
            git pull origin main
            docker-compose -f docker-compose.prod.yml build
            docker-compose -f docker-compose.prod.yml up -d
            ./scripts/test-deployment.sh
```

### 3. 配置GitHub Secrets

在GitHub仓库设置中添加：
- `SERVER_HOST` - 服务器地址
- `SERVER_USER` - SSH用户名
- `SSH_PRIVATE_KEY` - SSH私钥

---

## 📝 维护操作

### 1. 更新服务

```bash
# 拉取最新代码
cd /opt/enterprise-ai-platform
git pull origin main

# 重新构建镜像
docker-compose -f docker-compose.prod.yml build

# 重启服务（零停机）
docker-compose -f docker-compose.prod.yml up -d

# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec mcp-gateway alembic upgrade head
```

### 2. 备份数据

```bash
# 运行备份脚本
./scripts/backup/backup-all.sh

# 备份存储在 scripts/backup/backups/
```

### 3. 查看日志

```bash
# 查看所有日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看最近100行日志
docker-compose -f docker-compose.prod.yml logs --tail=100

# 导出日志
docker-compose -f docker-compose.prod.yml logs > logs_$(date +%Y%m%d).txt
```

### 4. 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart mcp-gateway

# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🆘 故障排查

### 1. 服务无法启动

```bash
# 检查日志
docker-compose -f docker-compose.prod.yml logs [service-name]

# 检查端口占用
netstat -tulpn | grep [port]

# 检查Docker状态
docker ps -a
docker-compose -f docker-compose.prod.yml ps
```

### 2. 数据库连接失败

```bash
# 检查数据库服务
docker-compose -f docker-compose.db.yml ps

# 测试数据库连接
docker-compose -f docker-compose.db.yml exec postgres psql -U postgres -c "SELECT 1"
```

### 3. 自动化调试系统不工作

```bash
# 检查配置文件
cat config/platform_integration.yaml
cat config/debug_workflows.yaml

# 检查日志
docker-compose -f docker-compose.prod.yml logs | grep -i "auto_debug"

# 测试API端点
curl http://localhost:8001/api/auto-debug/health
```

---

## 📚 相关文档

- [快速开始指南](QUICK_START.md)
- [自动化调试系统文档](auto-debug-system.md)
- [代码审查报告](../../CODE_REVIEW_REPORT.md)
- [API文档](../../api-docs/README.md)

---

## ✅ 部署检查清单

部署完成后，请检查：

- [ ] 所有服务正常运行
- [ ] 健康检查通过
- [ ] 数据库迁移完成
- [ ] API端点可访问
- [ ] 前端界面可访问
- [ ] 自动化调试系统启用
- [ ] 监控和告警配置完成
- [ ] 备份策略已配置
- [ ] 日志收集正常
- [ ] 安全配置正确

---

**部署完成后，你的平台就可以：**
- ✅ 自动运行测试
- ✅ 自动检测和修复Bug
- ✅ 监控系统健康状态
- ✅ 自动处理常见错误

祝你部署顺利！🚀

