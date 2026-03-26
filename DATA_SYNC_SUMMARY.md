# 数据同步脚本创建完成

## 已创建的脚本

### 1. 数据同步脚本

#### `scripts/sync_metadata_knowledge_to_server.py`
- **功能**: Python版本的数据同步脚本（跨平台）
- **用途**: 导出PostgreSQL、Chroma向量数据库和文档文件，并上传到服务器
- **使用方法**:
  ```bash
  python scripts/sync_metadata_knowledge_to_server.py --server-host user@server --server-path /opt/enterprise-ai-platform/backups
  ```

#### `scripts/sync_metadata_knowledge_to_server.ps1`
- **功能**: PowerShell版本的数据同步脚本（Windows）
- **用途**: 导出PostgreSQL、Chroma向量数据库和文档文件，并上传到服务器
- **使用方法**:
  ```powershell
  .\scripts\sync_metadata_knowledge_to_server.ps1 -ServerHost "user@192.168.1.100" -ServerPath "/opt/enterprise-ai-platform/backups"
  ```

### 2. 数据恢复脚本

#### `scripts/restore_metadata_knowledge_from_sync.ps1`
- **功能**: 服务器端数据恢复脚本
- **用途**: 从同步包恢复PostgreSQL、Chroma和文档数据
- **使用方法**:
  ```powershell
  .\scripts\restore_metadata_knowledge_from_sync.ps1 -SyncPackage "backups/sync/metadata_knowledge_sync_20231203_120000.tar.gz"
  ```

### 3. 数据状态检查脚本

#### `scripts/check_local_data_status.ps1`
- **功能**: 检查本地Docker中的数据状态
- **用途**: 快速查看PostgreSQL、Chroma和文档数据的状态
- **使用方法**:
  ```powershell
  .\scripts\check_local_data_status.ps1
  ```

### 4. 文档

#### `scripts/DATA_SYNC_README.md`
- **功能**: 完整的使用说明文档
- **内容**: 包括使用方法、注意事项、故障排除等

## 同步的数据内容

1. **PostgreSQL数据库**
   - 元数据服务的所有表数据
   - 知识库的元数据
   - 业务活动、能力单元等数据

2. **Chroma向量数据库**
   - 知识库的向量嵌入数据
   - 文档的向量索引

3. **文档文件**
   - 上传到知识库的原始文档
   - 文档存储目录中的所有文件

## 快速开始

### 检查本地数据状态
```powershell
.\scripts\check_local_data_status.ps1
```

### 同步数据到服务器
```powershell
# 导出并上传
.\scripts\sync_metadata_knowledge_to_server.ps1 -ServerHost "user@server" -ServerPath "/opt/enterprise-ai-platform/backups"

# 只导出，不上传
.\scripts\sync_metadata_knowledge_to_server.ps1 -NoUpload
```

### 在服务器上恢复数据
```powershell
.\scripts\restore_metadata_knowledge_from_sync.ps1 -SyncPackage "backups/sync/metadata_knowledge_sync_YYYYMMDD_HHMMSS.tar.gz"
```

## 注意事项

1. **数据备份**: 恢复前先备份服务器现有数据
2. **服务停止**: 恢复时建议停止相关服务
3. **数据一致性**: 确保本地和服务器使用相同版本的数据库schema
4. **磁盘空间**: 确保有足够的磁盘空间
5. **网络连接**: 上传需要SSH访问权限

## 下一步

1. 运行 `check_local_data_status.ps1` 检查本地数据
2. 运行 `sync_metadata_knowledge_to_server.ps1` 同步数据
3. 在服务器上运行 `restore_metadata_knowledge_from_sync.ps1` 恢复数据

---

**状态**: ✅ **脚本创建完成，可以使用**
