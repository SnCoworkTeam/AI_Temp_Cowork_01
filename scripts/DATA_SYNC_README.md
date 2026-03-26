# 元数据和知识库数据同步说明

## 概述

这些脚本用于将本地Docker环境中的元数据和知识库数据同步到服务器。

## 数据内容

同步的数据包括：

1. **PostgreSQL数据库数据**
   - 元数据服务的所有表数据
   - 知识库的元数据
   - 业务活动、能力单元等数据

2. **Chroma向量数据库**
   - 知识库的向量嵌入数据
   - 文档的向量索引

3. **文档文件**
   - 上传到知识库的原始文档
   - 文档存储目录中的所有文件

## 使用方法

### 本地导出和上传

#### PowerShell (Windows)

```powershell
# 导出并上传到服务器
.\scripts\sync_metadata_knowledge_to_server.ps1 -ServerHost "user@192.168.1.100" -ServerPath "/opt/enterprise-ai-platform/backups"

# 只导出，不上传
.\scripts\sync_metadata_knowledge_to_server.ps1 -NoUpload

# 指定输出目录
.\scripts\sync_metadata_knowledge_to_server.ps1 -OutputDir "backups\custom" -NoUpload
```

#### Python (跨平台)

```bash
# 导出并上传到服务器
python scripts/sync_metadata_knowledge_to_server.py --server-host user@192.168.1.100 --server-path /opt/enterprise-ai-platform/backups

# 只导出，不上传
python scripts/sync_metadata_knowledge_to_server.py --no-upload

# 指定输出目录
python scripts/sync_metadata_knowledge_to_server.py --output-dir backups/custom --no-upload
```

### 服务器端恢复

在服务器上运行恢复脚本：

```powershell
# 恢复数据
.\scripts\restore_metadata_knowledge_from_sync.ps1 -SyncPackage "backups/sync/metadata_knowledge_sync_20231203_120000.tar.gz"

# 预览操作（不实际执行）
.\scripts\restore_metadata_knowledge_from_sync.ps1 -SyncPackage "backups/sync/metadata_knowledge_sync_20231203_120000.tar.gz" -DryRun

# 指定数据库配置
.\scripts\restore_metadata_knowledge_from_sync.ps1 `
    -SyncPackage "backups/sync/metadata_knowledge_sync_20231203_120000.tar.gz" `
    -DbHost "postgres" `
    -DbPort "5432" `
    -DbName "ai_platform" `
    -DbUser "ai_user" `
    -DbPassword "ai_password"
```

## 同步包结构

同步包是一个压缩的tar.gz文件，包含：

```
metadata_knowledge_sync_YYYYMMDD_HHMMSS.tar.gz
├── postgres_YYYYMMDD_HHMMSS.sql.gz      # PostgreSQL数据库备份
├── chroma_YYYYMMDD_HHMMSS.tar.gz       # Chroma向量数据库备份
├── documents_YYYYMMDD_HHMMSS.tar.gz    # 文档文件备份
└── metadata_YYYYMMDD_HHMMSS.json       # 元数据信息
```

## 注意事项

1. **数据备份**: 在恢复数据之前，建议先备份服务器上的现有数据
2. **服务停止**: 恢复数据时，建议先停止相关服务（metadata-service, knowledge-base）
3. **数据一致性**: 确保本地和服务器使用相同版本的数据库schema
4. **磁盘空间**: 确保服务器有足够的磁盘空间存储恢复的数据
5. **网络连接**: 上传需要SSH访问权限和足够的网络带宽

## 故障排除

### PostgreSQL导出失败

- 检查PostgreSQL容器是否运行: `docker-compose ps postgres`
- 检查数据库连接配置是否正确
- 确保有足够的磁盘空间

### Chroma/文档导出失败

- 检查Docker volume是否存在: `docker volume ls`
- 检查volume是否有数据: `docker volume inspect <volume_name>`
- 确保有足够的磁盘空间

### 上传失败

- 检查SSH连接: `ssh user@server`
- 检查服务器路径是否存在且有写权限
- 检查网络连接和带宽

### 恢复失败

- 检查同步包是否完整（文件大小、校验和）
- 检查服务器上的Docker volume是否存在
- 检查数据库连接配置
- 查看恢复日志了解详细错误信息

## 自动化同步

可以设置定时任务自动同步数据：

### Windows (任务计划程序)

```powershell
# 创建定时任务，每天凌晨2点同步
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\path\to\sync_metadata_knowledge_to_server.ps1 -ServerHost user@server"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "SyncMetadataKnowledge" -Action $Action -Trigger $Trigger
```

### Linux (cron)

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天凌晨2点同步）
0 2 * * * /path/to/python /path/to/sync_metadata_knowledge_to_server.py --server-host user@server
```

## 相关文件

- `sync_metadata_knowledge_to_server.py` - Python同步脚本
- `sync_metadata_knowledge_to_server.ps1` - PowerShell同步脚本
- `restore_metadata_knowledge_from_sync.ps1` - 服务器端恢复脚本
- `scripts/backup/backup-postgres.sh` - PostgreSQL备份脚本
- `scripts/backup/backup-vector.sh` - 向量数据库备份脚本

