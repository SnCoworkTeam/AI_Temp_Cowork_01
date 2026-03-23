# 配置SAP数据库连接

## 快速配置

要启用从SAP ERP数据库直接发现所有表的元数据，需要配置以下环境变量：

### 方法1: 修改 .env 文件

在项目根目录的 `.env` 文件中添加：

```bash
# SAP数据库连接配置
SAP_DB_TYPE=hdb                    # 'hdb' (HANA) 或 'mssql' (SQL Server)
SAP_DB_HOST=your-sap-db-host        # 数据库主机地址
SAP_DB_PORT=33015                  # 端口 (HANA: 33015, SQL Server: 1433)
SAP_DB_NAME=your-database          # 数据库名称
SAP_DB_USER=your-username          # 数据库用户名
SAP_DB_PASSWORD=your-password      # 数据库密码
```

### 方法2: 修改 docker-compose.yml

在 `docker-compose.yml` 中的 `sap-metadata-agent` 服务下添加环境变量：

```yaml
sap-metadata-agent:
  environment:
    - SAP_DB_TYPE=hdb
    - SAP_DB_HOST=your-sap-db-host
    - SAP_DB_PORT=33015
    - SAP_DB_NAME=your-database
    - SAP_DB_USER=your-username
    - SAP_DB_PASSWORD=your-password
```

### 方法3: 使用配置中心

如果使用配置中心，配置以下键：

- `sap.db_type`
- `sap.db_host`
- `sap.db_port`
- `sap.db_name`
- `sap.db_user`
- `sap.db_password`

## 配置示例

### SAP HANA 配置

```bash
SAP_DB_TYPE=hdb
SAP_DB_HOST=sap-hana.example.com
SAP_DB_PORT=33015
SAP_DB_NAME=SYSTEMDB
SAP_DB_USER=SAPR3
SAP_DB_PASSWORD=YourPassword123
```

### SQL Server 配置

```bash
SAP_DB_TYPE=mssql
SAP_DB_HOST=sap-sql.example.com
SAP_DB_PORT=1433
SAP_DB_NAME=SAP
SAP_DB_USER=sa
SAP_DB_PASSWORD=YourPassword123
```

## 验证配置

配置完成后，重启服务并检查日志：

```bash
# 重启服务
docker-compose restart sap-metadata-agent

# 查看日志
docker-compose logs sap-metadata-agent | grep -i "database"
```

应该看到：
```
SAP database client connected successfully
```

## 开始构建

配置完成后，使用新的构建脚本同时发现数据库和OData：

```bash
cd sap-metadata-agent
python build_with_database.py
```

或者使用API：

```bash
curl -X POST http://localhost:8015/api/sap-metadata/discover \
  -H "Content-Type: application/json" \
  -d '{
    "include_database": true,
    "include_odata": true,
    "build_semantic_index": true,
    "sync_to_metadata_service": true
  }'
```

## 注意事项

1. **数据库权限**: 确保数据库用户有读取表结构和数据的权限
2. **网络连接**: 确保Docker容器能够访问SAP数据库
3. **防火墙**: 检查防火墙规则，允许数据库端口访问
4. **性能**: 大型SAP系统可能有数千个表，发现过程需要时间

## 故障排查

如果连接失败，检查：

1. 数据库服务是否运行
2. 主机地址和端口是否正确
3. 用户名和密码是否正确
4. 网络连接是否正常
5. 防火墙规则是否允许访问

查看详细错误信息：

```bash
docker-compose logs sap-metadata-agent
```



