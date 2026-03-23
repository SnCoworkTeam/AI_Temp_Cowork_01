# 知识库数据丢失排查指南

## 问题描述

用户反映原来创建的知识库都不见了，怀疑数据丢失。

## 可能的原因

### 1. 502 错误导致无法访问数据（最可能）

**症状**：
- 前端显示 502 Bad Gateway 错误
- 无法连接到后端服务
- 数据可能还在数据库中，但无法查询

**排查步骤**：
1. 检查后端服务是否运行
2. 检查数据库连接
3. 直接查询数据库确认数据是否存在

### 2. 数据库连接问题

**可能原因**：
- 数据库服务未运行
- 数据库连接配置错误
- 数据库迁移未执行
- 连接到了错误的数据库

### 3. 数据确实被删除

**可能原因**：
- 误操作删除
- 数据库迁移导致数据丢失
- 数据库重置或恢复

### 4. 查询过滤问题

**可能原因**：
- 默认状态过滤导致数据被隐藏
- 分页问题导致数据未显示
- 搜索条件过滤了数据

## 排查步骤

### 步骤 1: 检查后端服务状态

```bash
# 检查知识库服务是否运行
curl http://localhost:8004/api/health

# 检查 API Gateway（如果使用）
curl http://localhost:8080/health
```

### 步骤 2: 直接查询数据库

使用诊断脚本检查数据库：

```bash
# 运行诊断脚本
python check_knowledge_bases.py
```

或者直接使用 SQL：

```sql
-- 连接到数据库
psql -U postgres -d enterprise_ai

-- 查询知识库总数
SELECT COUNT(*) FROM knowledge_bases;

-- 查询所有知识库
SELECT id, name, status, created_at, updated_at 
FROM knowledge_bases 
ORDER BY created_at DESC;

-- 按状态统计
SELECT status, COUNT(*) 
FROM knowledge_bases 
GROUP BY status;
```

### 步骤 3: 检查数据库连接配置

检查环境变量和配置文件：

```bash
# 检查环境变量
echo $DATABASE_URL

# 检查 .env 文件
cat knowledge-base/.env
cat database/.env
```

### 步骤 4: 检查数据库迁移历史

```bash
# 查看迁移历史
cd database
alembic history

# 检查当前版本
alembic current
```

### 步骤 5: 检查后端日志

查看知识库服务的日志：

```bash
# 如果使用 Docker
docker logs knowledge-base

# 如果直接运行
# 查看控制台输出或日志文件
```

## 解决方案

### 方案 1: 修复 502 错误（如果数据还在）

如果数据还在数据库中，只是无法访问：

1. **启动后端服务**：
   ```bash
   cd knowledge-base
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
   ```

2. **检查 API Gateway 配置**（如果使用）：
   - 确保 API Gateway 正在运行
   - 检查路由配置是否正确

3. **检查环境变量**：
   - 确保 `DATABASE_URL` 正确
   - 确保数据库服务正在运行

### 方案 2: 恢复数据（如果数据丢失）

如果数据确实丢失了：

1. **从备份恢复**：
   ```bash
   # 如果有数据库备份
   pg_restore -U postgres -d enterprise_ai backup.dump
   ```

2. **检查是否有其他数据源**：
   - 检查其他环境（开发/测试/生产）
   - 检查是否有导出文件

3. **重新创建知识库**：
   - 如果无法恢复，需要重新创建

### 方案 3: 修复数据库连接

如果数据库连接有问题：

1. **检查数据库服务**：
   ```bash
   # 检查 PostgreSQL 是否运行
   sudo systemctl status postgresql
   # 或
   docker ps | grep postgres
   ```

2. **测试数据库连接**：
   ```python
   from sqlalchemy import create_engine
   engine = create_engine('postgresql://postgres:postgres@localhost:5432/enterprise_ai')
   conn = engine.connect()
   print("连接成功！")
   ```

3. **检查数据库权限**：
   ```sql
   -- 检查用户权限
   \du
   
   -- 检查数据库权限
   \l
   ```

## 预防措施

### 1. 定期备份数据库

```bash
# 创建备份
pg_dump -U postgres enterprise_ai > backup_$(date +%Y%m%d).sql

# 或使用 Docker
docker exec postgres pg_dump -U postgres enterprise_ai > backup.sql
```

### 2. 添加数据保护

- 实现软删除（标记删除而不是真正删除）
- 添加数据审计日志
- 实现数据恢复功能

### 3. 监控和告警

- 监控数据库连接状态
- 监控数据变化
- 设置异常告警

## 快速检查清单

- [ ] 后端服务是否运行？
- [ ] 数据库服务是否运行？
- [ ] 数据库连接配置是否正确？
- [ ] 数据库中是否有数据？（运行诊断脚本）
- [ ] API Gateway 是否正常运行？（如果使用）
- [ ] 是否有数据库备份？
- [ ] 后端日志是否有错误信息？

## 诊断脚本使用

运行诊断脚本快速检查：

```bash
# 确保在项目根目录
python check_knowledge_bases.py
```

脚本会检查：
1. 知识库总数
2. 按状态统计
3. 列出所有知识库
4. 检查表结构
5. 检查数据库连接

## 联系支持

如果以上步骤都无法解决问题，请：
1. 收集诊断脚本的输出
2. 收集后端服务日志
3. 收集数据库查询结果
4. 记录错误信息和时间


