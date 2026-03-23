# 数据备份和恢复系统

## 概述

本系统提供了完整的数据备份和恢复解决方案，支持PostgreSQL、Redis和向量数据库的备份、恢复和验证。

## 备份脚本

### 1. PostgreSQL备份 (`backup-postgres.sh`)

**功能：**
- 全量备份：完整数据库转储
- 增量备份：基于WAL归档的增量备份
- 日志备份：WAL日志归档

**使用方法：**
```bash
# 全量备份
./backup-postgres.sh full

# 增量备份
./backup-postgres.sh incremental

# 日志备份
./backup-postgres.sh log
```

**环境变量：**
- `DB_HOST`: 数据库主机（默认: localhost）
- `DB_PORT`: 数据库端口（默认: 5432）
- `DB_NAME`: 数据库名称（默认: enterprise_ai）
- `DB_USER`: 数据库用户（默认: postgres）
- `DB_PASSWORD`: 数据库密码
- `BACKUP_DIR`: 备份目录（默认: $PROJECT_ROOT/backups/postgres）
- `COMPRESSION`: 是否压缩（默认: true）
- `ENCRYPTION`: 是否加密（默认: true）
- `ENCRYPTION_KEY`: 加密密钥
- `RETENTION_DAYS`: 本地保留天数（默认: 7）

### 2. Redis备份 (`backup-redis.sh`)

**功能：**
- RDB备份：Redis数据库快照
- AOF备份：Append-Only File备份
- 同时备份RDB和AOF

**使用方法：**
```bash
# RDB备份
./backup-redis.sh rdb

# AOF备份
./backup-redis.sh aof

# 同时备份RDB和AOF
./backup-redis.sh both
```

**环境变量：**
- `REDIS_HOST`: Redis主机（默认: localhost）
- `REDIS_PORT`: Redis端口（默认: 6379）
- `REDIS_PASSWORD`: Redis密码

### 3. 向量数据库备份 (`backup-vector.sh`)

**功能：**
- ChromaDB备份：打包整个数据目录
- Weaviate备份：通过API导出数据

**使用方法：**
```bash
# ChromaDB备份
VECTOR_DB_TYPE=chroma ./backup-vector.sh

# Weaviate备份
VECTOR_DB_TYPE=weaviate ./backup-vector.sh
```

## 恢复脚本

### PostgreSQL恢复 (`restore-postgres.sh`)

**功能：**
- 全量恢复：从备份文件恢复数据库
- 时间点恢复（PITR）：恢复到指定时间点
- 测试恢复：恢复到测试数据库进行验证

**使用方法：**
```bash
# 全量恢复（使用最新备份）
./restore-postgres.sh full

# 全量恢复（指定备份文件）
./restore-postgres.sh full /path/to/backup.sql.gz

# 时间点恢复
./restore-postgres.sh pitr /path/to/backup.sql.gz "2024-01-01 12:00:00"

# 测试恢复
./restore-postgres.sh test /path/to/backup.sql.gz
```

## 定时备份调度

### 调度脚本 (`schedule-backup.sh`)

**备份策略：**

1. **PostgreSQL:**
   - 全量备份：每周日 02:00
   - 增量备份：每天 02:00（除了周日）
   - 日志备份：每6小时（02:00, 08:00, 14:00, 20:00）

2. **Redis:**
   - 全量备份：每周日 02:30
   - 增量备份：每天 03:00

3. **向量数据库:**
   - 全量备份：每周日 04:00
   - 增量备份：每天 05:00

**配置Cron：**
```bash
# 编辑crontab
crontab -e

# 添加以下行（每小时执行一次）
0 * * * * /path/to/scripts/backup/schedule-backup.sh >> /path/to/logs/backup/cron.log 2>&1
```

## 备份验证

### 验证脚本 (`verify-backup.sh`)

**功能：**
- 文件完整性验证
- 校验和验证
- 压缩文件验证
- 加密文件验证
- 内容验证

**使用方法：**
```bash
# 验证所有备份
./verify-backup.sh all

# 验证PostgreSQL备份
./verify-backup.sh postgres

# 验证Redis备份
./verify-backup.sh redis

# 验证向量数据库备份
./verify-backup.sh vector

# 验证特定文件
./verify-backup.sh specific /path/to/backup.sql.gz
```

## 存储配置

### 本地存储
- 位置：`$PROJECT_ROOT/backups/`
- 保留策略：最近7天（可配置）
- 自动清理：超过保留期的备份自动删除

### 云存储

#### AWS S3
```bash
export CLOUD_STORAGE_TYPE=s3
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export S3_BUCKET=your_bucket_name
```

#### 阿里云OSS
```bash
export CLOUD_STORAGE_TYPE=oss
export OSS_ACCESS_KEY_ID=your_access_key
export OSS_ACCESS_KEY_SECRET=your_secret_key
export OSS_BUCKET=your_bucket_name
export OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

## 加密和压缩

### 加密
- 算法：AES-256-CBC
- 密钥：通过 `ENCRYPTION_KEY` 环境变量设置
- 注意：请妥善保管加密密钥，丢失密钥将无法恢复备份

### 压缩
- 格式：Gzip
- 默认启用
- 可通过 `COMPRESSION=false` 禁用

## 监控告警

### 告警配置

#### 邮件告警
```bash
export ALERT_EMAIL=admin@example.com
```

#### Webhook告警
```bash
export ALERT_WEBHOOK=https://your-webhook-url.com/backup-alert
```

### 告警类型
1. **备份失败告警**
   - 备份执行失败时自动发送
   - 包含错误信息和时间戳

2. **存储空间告警**
   - 当存储空间使用率超过阈值时发送
   - 默认阈值：80%（可通过 `STORAGE_THRESHOLD` 配置）

3. **备份完整性告警**
   - 验证失败时发送
   - 包含失败的备份文件信息

## 恢复测试

### 定期恢复测试

建议每周执行一次恢复测试，确保备份可用：

```bash
# 测试PostgreSQL恢复
./restore-postgres.sh test

# 测试Redis恢复
# 需要在测试环境中手动执行
```

### RTO和RPO监控

**RTO (Recovery Time Objective) - 恢复时间目标**
- 目标：< 1小时
- 监控：记录恢复开始到完成的时间

**RPO (Recovery Point Objective) - 数据恢复点目标**
- 目标：< 1小时数据丢失
- 保障：通过每6小时的日志备份实现

## 使用示例

### 完整备份流程

```bash
# 1. 设置环境变量
export DB_PASSWORD=your_password
export ENCRYPTION_KEY=your_encryption_key
export CLOUD_STORAGE_TYPE=s3
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export S3_BUCKET=your_bucket

# 2. 执行全量备份
./backup-postgres.sh full
./backup-redis.sh rdb
./backup-vector.sh

# 3. 验证备份
./verify-backup.sh all

# 4. 测试恢复（可选）
./restore-postgres.sh test
```

### 紧急恢复流程

```bash
# 1. 找到最新的备份文件
BACKUP_FILE=$(find backups/postgres -name "postgres_full_*.sql.gz" | sort -r | head -1)

# 2. 验证备份
./verify-backup.sh specific "$BACKUP_FILE"

# 3. 执行恢复
./restore-postgres.sh full "$BACKUP_FILE"
```

## 注意事项

1. **权限：** 确保脚本有执行权限
   ```bash
   chmod +x scripts/backup/*.sh
   ```

2. **依赖：** 确保安装了必要的工具
   - PostgreSQL: `pg_dump`, `pg_restore`, `pg_isready`
   - Redis: `redis-cli`
   - 压缩: `gzip`, `gunzip`
   - 加密: `openssl`
   - 云存储: `aws-cli` 或 `ossutil`

3. **安全：**
   - 加密密钥请妥善保管
   - 不要在代码中硬编码密码
   - 使用环境变量或密钥管理服务

4. **存储：**
   - 定期检查备份目录空间
   - 监控云存储使用情况
   - 设置备份保留策略

5. **测试：**
   - 定期执行恢复测试
   - 验证备份完整性
   - 记录RTO和RPO指标

## 故障排查

### 常见问题

1. **备份失败：连接错误**
   - 检查数据库服务是否运行
   - 验证连接参数是否正确
   - 检查网络连接

2. **备份失败：权限错误**
   - 确保数据库用户有备份权限
   - 检查文件系统权限

3. **恢复失败：备份文件损坏**
   - 使用验证脚本检查备份
   - 尝试使用其他备份文件
   - 检查磁盘空间和I/O

4. **加密/解密失败**
   - 验证加密密钥是否正确
   - 检查openssl是否安装
   - 确认备份文件格式

## 维护计划

- **每日：** 检查备份日志，确认备份成功
- **每周：** 执行恢复测试，验证备份可用性
- **每月：** 检查存储空间，清理旧备份
- **每季度：** 审查备份策略，优化备份计划









