# 数据同步脚本套件 - 完成总结

## ✅ 已完成的工作

### 1. 核心同步脚本

#### Python版本（跨平台）
- **文件**: `scripts/sync_metadata_knowledge_to_server.py`
- **功能**: 
  - 导出PostgreSQL数据库数据
  - 导出Chroma向量数据库
  - 导出文档文件
  - 创建同步包
  - 上传到服务器（可选）
- **状态**: ✅ 已完成并测试

#### PowerShell版本（Windows）
- **文件**: `scripts/sync_metadata_knowledge_to_server.ps1`
- **功能**: 同Python版本，针对Windows优化
- **状态**: ✅ 已完成

### 2. 数据恢复脚本

- **文件**: `scripts/restore_metadata_knowledge_from_sync.ps1`
- **功能**: 
  - 解压同步包
  - 恢复PostgreSQL数据
  - 恢复Chroma向量数据库
  - 恢复文档文件
  - 支持DryRun预览模式
- **状态**: ✅ 已完成

### 3. 数据状态检查脚本

- **文件**: `scripts/check_local_data_status.ps1`
- **功能**: 
  - 检查PostgreSQL数据状态
  - 检查Chroma向量数据库状态
  - 检查文档文件状态
  - 显示数据统计信息
- **状态**: ✅ 已完成

### 4. 快速测试脚本

- **文件**: `scripts/quick_sync_test.ps1`
- **功能**: 快速测试数据导出功能（不上传）
- **状态**: ✅ 已完成

### 5. 文档

- **`scripts/DATA_SYNC_README.md`**: 完整的使用说明文档
- **`DATA_SYNC_SUMMARY.md`**: 脚本创建总结
- **`DATA_SYNC_QUICK_START.md`**: 快速开始指南
- **`DATA_SYNC_COMPLETE.md`**: 本文档

## 📦 同步的数据内容

### PostgreSQL数据库
- ✅ 元数据服务的所有表数据
- ✅ 知识库的元数据
- ✅ 业务活动、能力单元等数据
- ✅ 用户数据、权限数据等

### Chroma向量数据库
- ✅ 知识库的向量嵌入数据
- ✅ 文档的向量索引
- ✅ 语义搜索索引

### 文档文件
- ✅ 上传到知识库的原始文档
- ✅ 文档存储目录中的所有文件
- ✅ 文档元数据和版本信息

## 🚀 使用方法

### 快速开始

```powershell
# 1. 检查本地数据状态
.\scripts\check_local_data_status.ps1

# 2. 测试导出（不上传）
.\scripts\quick_sync_test.ps1

# 3. 同步到服务器
.\scripts\sync_metadata_knowledge_to_server.ps1 -ServerHost "user@server"

# 4. 在服务器上恢复
.\scripts\restore_metadata_knowledge_from_sync.ps1 -SyncPackage "backups/sync/metadata_knowledge_sync_*.tar.gz"
```

### Python版本

```bash
# 检查帮助
python scripts/sync_metadata_knowledge_to_server.py --help

# 只导出
python scripts/sync_metadata_knowledge_to_server.py --no-upload

# 导出并上传
python scripts/sync_metadata_knowledge_to_server.py --server-host user@server
```

## 📋 同步包结构

```
metadata_knowledge_sync_YYYYMMDD_HHMMSS.tar.gz
├── postgres_YYYYMMDD_HHMMSS.sql.gz      # PostgreSQL数据库备份
├── chroma_YYYYMMDD_HHMMSS.tar.gz        # Chroma向量数据库备份
├── documents_YYYYMMDD_HHMMSS.tar.gz     # 文档文件备份
└── metadata_YYYYMMDD_HHMMSS.json        # 元数据信息
```

## 🔍 验证的Docker资源

已确认以下Docker资源存在：

- ✅ `enterprise-ai-platform_postgres_data` - PostgreSQL数据卷
- ✅ `enterprise-ai-platform_knowledge_base_chroma` - Chroma向量数据库卷
- ✅ `enterprise-ai-platform_knowledge_base_documents` - 文档文件卷

## ⚠️ 重要注意事项

1. **数据备份**: 恢复前先备份服务器现有数据
2. **服务停止**: 恢复时建议停止相关服务
3. **数据一致性**: 确保本地和服务器使用相同版本的数据库schema
4. **磁盘空间**: 确保有足够的磁盘空间
5. **网络连接**: 上传需要SSH访问权限

## 🛠️ 故障排除

### PostgreSQL导出失败
- 检查容器是否运行: `docker-compose ps postgres`
- 检查数据库连接配置
- 确保有足够的磁盘空间

### Chroma/文档导出失败
- 检查Docker volume是否存在: `docker volume ls`
- 检查volume是否有数据
- 确保有足够的磁盘空间

### 上传失败
- 检查SSH连接: `ssh user@server`
- 检查服务器路径是否存在且有写权限
- 检查网络连接和带宽

### 恢复失败
- 检查同步包是否完整
- 检查服务器上的Docker volume是否存在
- 检查数据库连接配置
- 查看恢复日志了解详细错误

## 📊 文件清单

### 脚本文件
- ✅ `scripts/sync_metadata_knowledge_to_server.py`
- ✅ `scripts/sync_metadata_knowledge_to_server.ps1`
- ✅ `scripts/restore_metadata_knowledge_from_sync.ps1`
- ✅ `scripts/check_local_data_status.ps1`
- ✅ `scripts/quick_sync_test.ps1`

### 文档文件
- ✅ `scripts/DATA_SYNC_README.md`
- ✅ `DATA_SYNC_SUMMARY.md`
- ✅ `DATA_SYNC_QUICK_START.md`
- ✅ `DATA_SYNC_COMPLETE.md`

## 🎯 下一步

1. **测试脚本**: 运行 `quick_sync_test.ps1` 测试导出功能
2. **检查数据**: 运行 `check_local_data_status.ps1` 查看本地数据状态
3. **同步数据**: 使用同步脚本将数据同步到服务器
4. **恢复数据**: 在服务器上使用恢复脚本恢复数据

## 📝 相关资源

- 备份脚本: `scripts/backup/backup-postgres.sh`
- 备份脚本: `scripts/backup/backup-vector.sh`
- 同步工具: `mcp-gateway/sync_tools_to_metadata.py`

---

**状态**: ✅ **所有脚本已创建完成，可以使用**

**最后更新**: 2025-12-03


