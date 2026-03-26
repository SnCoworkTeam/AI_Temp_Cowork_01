# 生产发布

## 概述

生产发布是将代码部署到生产环境的正式流程。

## 发布准备

### 发布前检查
- [ ] 预发布验证通过
- [ ] 变更请求批准
- [ ] 回滚计划准备
- [ ] 监控告警配置
- [ ] 团队通知完成
- [ ] 维护窗口确认

### 发布计划
- **发布时间**: YYYY-MM-DD HH:MM
- **维护窗口**: XX:XX - XX:XX
- **预计时长**: XX分钟
- **发布负责人**: [姓名]

## 发布流程

### 1. 发布前准备
```bash
# 备份数据库
./scripts/backup/backup-postgres.sh

# 备份Redis
./scripts/backup/backup-redis.sh

# 检查环境
./scripts/release/pre-release-check.sh
```

### 2. 构建发布包
```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml build

# 标记镜像
docker tag mcp-gateway:latest mcp-gateway:v1.0.0
```

### 3. 部署到生产
```bash
# 部署服务（使用蓝绿部署或滚动更新）
./scripts/release/deploy-production.sh

# 或使用Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### 4. 数据库迁移
```bash
# 运行数据库迁移
docker-compose exec mcp-gateway alembic upgrade head
```

### 5. 验证部署
```bash
# 健康检查
curl https://api.example.com/api/health

# 功能验证
./scripts/release/verify-production.sh
```

## 发布检查清单

### 部署检查
- [ ] 镜像构建成功
- [ ] 服务启动成功
- [ ] 数据库迁移成功
- [ ] 配置加载成功

### 功能检查
- [ ] 健康检查通过
- [ ] API端点正常
- [ ] 前端页面正常
- [ ] 核心功能正常

### 性能检查
- [ ] 响应时间正常
- [ ] 错误率正常
- [ ] 资源使用正常

### 监控检查
- [ ] 监控数据正常
- [ ] 告警配置正常
- [ ] 日志收集正常

## 发布后验证

### 立即验证（0-5分钟）
- 服务健康状态
- 核心功能可用性
- 错误日志检查

### 短期验证（5-30分钟）
- 完整功能测试
- 性能指标检查
- 用户反馈收集

### 长期验证（30分钟-24小时）
- 稳定性监控
- 性能趋势分析
- 用户行为分析

## 发布通知

### 内部通知
- 开发团队
- 运维团队
- 产品团队
- 测试团队

### 外部通知（如需要）
- 用户公告
- 系统维护通知
- 功能更新说明

## 发布记录

### 记录内容
- 发布时间
- 发布版本
- 发布内容
- 发布结果
- 问题记录

### 记录格式
参见 `release-notes/` 目录

## 发布后监控

### 监控指标
- 服务健康状态
- API响应时间
- 错误率
- 资源使用率
- 用户活动

### 告警响应
- 立即响应严重告警
- 1小时内响应重要告警
- 24小时内响应一般告警

## 发布完成

### 完成条件
- 所有验证通过
- 监控指标正常
- 无严重问题
- 团队确认

### 完成步骤
1. 更新发布状态
2. 生成发布报告
3. 更新文档
4. 通知团队









