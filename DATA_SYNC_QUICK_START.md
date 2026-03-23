# 数据同步快速开始指南

## 🚀 快速开始

### 第一步：检查本地数据状态

```powershell
.\scripts\check_local_data_status.ps1
```

这将显示：
- PostgreSQL数据库中的数据表和数据量
- Chroma向量数据库的状态
- 文档文件的数量

### 第二步：导出数据（测试）

```powershell
# 只导出，不上传（用于测试）
.\scripts\sync_metadata_knowledge_to_server.ps1 -NoUpload

# 或使用快速测试脚本
.\scripts\quick_sync_test.ps1
```

导出的文件将保存在 `backups\sync\` 目录下。

### 第三步：同步到服务器

```powershell
# 导出并上传到服务器
.\scripts\sync_metadata_knowledge_to_server.ps1 `
    -ServerHost "user@192.168.1.100" `
    -ServerPath "/opt/enterprise-ai-platform/backups"
```

### 第四步：在服务器上恢复数据

在服务器上运行：

```powershell
# 恢复数据
.\scripts\restore_metadata_knowledge_from_sync.ps1 `
    -SyncPackage "backups/sync/metadata_knowledge_sync_YYYYMMDD_HHMMSS.tar.gz"

# 重启相关服务
docker-compose restart metadata-service knowledge-base
```

## 📋 同步的数据内容

### 1. PostgreSQL数据库
- ✅ 元数据服务的所有表数据
- ✅ 知识库的元数据
- ✅ 业务活动、能力单元等数据
- ✅ 用户数据、权限数据等

### 2. Chroma向量数据库
- ✅ 知识库的向量嵌入数据
- ✅ 文档的向量索引
- ✅ 语义搜索索引

### 3. 文档文件
- ✅ 上传到知识库的原始文档
- ✅ 文档存储目录中的所有文件
- ✅ 文档元数据和版本信息

## 🔍 检查同步包内容

同步包是一个压缩的tar.gz文件，包含：

```
metadata_knowledge_sync_YYYYMMDD_HHMMSS.tar.gz
├── postgres_YYYYMMDD_HHMMSS.sql.gz      # PostgreSQL数据库备份
├── chroma_YYYYMMDD_HHMMSS.tar.gz        # Chroma向量数据库备份
├── documents_YYYYMMDD_HHMMSS.tar.gz     # 文档文件备份
└── metadata_YYYYMMDD_HHMMSS.json        # 元数据信息（包含导出时间、文件列表等）
```

## ⚠️ 重要提示

### 在同步之前

1. **检查本地数据**: 运行 `check_local_data_status.ps1` 确认有数据需要同步
2. **检查磁盘空间**: 确保有足够空间存储导出的文件
3. **检查网络**: 确保可以连接到服务器

### 在恢复之前

1. **备份服务器数据**: 先备份服务器上的现有数据
2. **停止服务**: 建议先停止相关服务
   ```powershell
   docker-compose stop metadata-service knowledge-base
   ```
3. **检查磁盘空间**: 确保服务器有足够空间
4. **检查数据库版本**: 确保本地和服务器使用相同版本的数据库schema

## 🛠️ 故障排除

### 问题：PostgreSQL导出失败

**可能原因**:
- PostgreSQL容器未运行
- 数据库连接配置错误
- 磁盘空间不足

**解决方法**:
```powershell
# 检查PostgreSQL容器
docker-compose ps postgres

# 启动PostgreSQL容器
docker-compose up -d postgres

# 检查数据库连接
docker exec enterprise-ai-postgres psql -U ai_user -d ai_platform -c "SELECT 1;"
```

### 问题：Chroma/文档导出失败

**可能原因**:
- Docker volume不存在
- Volume为空
- 权限问题

**解决方法**:
```powershell
# 检查volume
docker volume ls | Select-String "knowledge"

# 检查volume内容
docker run --rm -v enterprise-ai-platform_knowledge_base_chroma:/data alpine ls -la /data
```

### 问题：上传失败

**可能原因**:
- SSH连接失败
- 服务器路径不存在
- 权限不足

**解决方法**:
```powershell
# 测试SSH连接
ssh user@server

# 检查服务器路径
ssh user@server "ls -la /opt/enterprise-ai-platform/backups"

# 创建目录（如果需要）
ssh user@server "mkdir -p /opt/enterprise-ai-platform/backups"
```

### 问题：恢复失败

**可能原因**:
- 同步包损坏
- 数据库版本不匹配
- 服务正在运行

**解决方法**:
```powershell
# 检查同步包完整性
tar -tzf backups/sync/metadata_knowledge_sync_*.tar.gz

# 停止服务
docker-compose stop metadata-service knowledge-base

# 使用DryRun预览
.\scripts\restore_metadata_knowledge_from_sync.ps1 -SyncPackage "..." -DryRun
```

## 📊 同步包大小估算

- **PostgreSQL**: 通常 10-100 MB（取决于数据量）
- **Chroma**: 通常 50-500 MB（取决于向量数据量）
- **文档**: 取决于文档数量和大小

总大小通常在 100 MB - 1 GB 之间。

## 🔄 自动化同步

### Windows任务计划程序

```powershell
# 创建每天凌晨2点自动同步的任务
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-File C:\path\to\sync_metadata_knowledge_to_server.ps1 -ServerHost user@server"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "SyncMetadataKnowledge" -Action $Action -Trigger $Trigger
```

### Linux Cron

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天凌晨2点）
0 2 * * * /path/to/python /path/to/sync_metadata_knowledge_to_server.py --server-host user@server
```

## 📝 相关文件

- `scripts/sync_metadata_knowledge_to_server.py` - Python同步脚本
- `scripts/sync_metadata_knowledge_to_server.ps1` - PowerShell同步脚本
- `scripts/restore_metadata_knowledge_from_sync.ps1` - 服务器端恢复脚本
- `scripts/check_local_data_status.ps1` - 数据状态检查脚本
- `scripts/quick_sync_test.ps1` - 快速测试脚本
- `scripts/DATA_SYNC_README.md` - 完整文档

## ✅ 验证同步成功

同步完成后，可以通过以下方式验证：

1. **检查同步包**: 确认文件存在且大小合理
2. **检查元数据文件**: 查看 `metadata_*.json` 确认包含的数据类型
3. **在服务器上验证**: 恢复后检查数据是否正确导入

---

**需要帮助？** 查看 `scripts/DATA_SYNC_README.md` 获取详细文档。


