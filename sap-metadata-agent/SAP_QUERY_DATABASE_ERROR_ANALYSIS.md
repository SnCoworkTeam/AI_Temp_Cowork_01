# SAP查询数据库连接错误分析

## 🔴 错误信息

```
HTTP 500: {"detail":"Error executing tool: (psycopg2.OperationalError) connection to server at \"postgres\" (172.28.0.3), port 5432 failed: FATAL:  password authentication failed for user \"postgres\"\n\n(Background on this error at: https://sqlalche.me/e/20/e3q8)"}
```

## 📋 问题分析

### 1. 错误原因

执行SAP查询时，系统试图连接PostgreSQL数据库，但密码认证失败。

**错误详情**：
- **数据库地址**: `postgres` (172.28.0.3)
- **端口**: `5432`
- **用户**: `postgres`
- **错误类型**: `password authentication failed`

### 2. 问题定位

SAP查询工具的执行流程：
1. 用户请求："分析一下销售订单"
2. 系统识别为 `tool_execution`，使用 `sap_query` 工具
3. `sap_query` 工具调用 SAP OData MCP 服务器
4. SAP OData MCP 服务器需要查询元数据，连接PostgreSQL数据库
5. **数据库连接失败** - 密码认证失败

### 3. 可能的原因

1. **数据库密码配置不正确**
   - 环境变量 `DB_PASSWORD` 与数据库实际密码不匹配
   - 配置中心中的数据库密码配置错误

2. **数据库服务未正确启动**
   - PostgreSQL容器未运行
   - 数据库初始化失败

3. **环境变量未正确传递**
   - SAP OData MCP 服务器未获取到正确的数据库配置
   - Docker容器间网络配置问题

4. **数据库配置不一致**
   - 不同服务使用了不同的数据库配置
   - 配置中心与本地环境变量不一致

## 🔧 解决方案

### 方案1: 检查数据库配置（推荐）

#### 1.1 检查环境变量

确认 `.env` 文件或环境变量中的数据库配置：

```bash
# 检查数据库配置
echo $DB_HOST
echo $DB_PORT
echo $DB_USER
echo $DB_PASSWORD
echo $DB_NAME
```

**默认配置**（来自 `env.example`）：
```bash
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=enterprise_ai_platform
```

#### 1.2 检查Docker Compose配置

确认 `docker-compose.yml` 中的数据库配置：

```yaml
postgres:
  environment:
    POSTGRES_DB: ${DB_NAME:-enterprise_ai_platform}
    POSTGRES_USER: ${DB_USER:-postgres}
    POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
```

#### 1.3 检查配置中心

如果使用配置中心，检查数据库配置：

```bash
# 查看配置中心中的数据库配置
curl http://localhost:8090/api/configs?environment=default | grep -i db
```

### 方案2: 验证数据库连接

#### 2.1 直接连接数据库测试

```bash
# 使用psql连接数据库
docker exec -it enterprise-ai-postgres psql -U postgres -d enterprise_ai_platform

# 或者从外部连接
psql -h localhost -p 5432 -U postgres -d enterprise_ai_platform
```

#### 2.2 检查数据库服务状态

```bash
# 检查PostgreSQL容器状态
docker ps | grep postgres

# 检查数据库日志
docker logs enterprise-ai-postgres

# 检查数据库健康状态
docker exec enterprise-ai-postgres pg_isready -U postgres
```

### 方案3: 修复数据库密码

#### 3.1 如果密码不匹配

**选项A: 更新环境变量**

```bash
# 在 .env 文件中设置正确的密码
DB_PASSWORD=your_actual_password
```

**选项B: 重置数据库密码**

```bash
# 进入PostgreSQL容器
docker exec -it enterprise-ai-postgres psql -U postgres

# 修改密码
ALTER USER postgres WITH PASSWORD 'new_password';
```

**选项C: 重新初始化数据库**

```bash
# 停止并删除数据库容器和数据卷
docker-compose down -v

# 重新启动（会使用新的密码）
docker-compose up -d postgres
```

#### 3.2 更新配置中心中的数据库配置

```bash
# 更新数据库密码配置
curl -X POST http://localhost:8090/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "key": "db.password",
    "value": "your_actual_password",
    "description": "PostgreSQL数据库密码",
    "environment": "default"
  }'
```

### 方案4: 检查SAP OData MCP服务器配置

#### 4.1 检查SAP OData MCP服务器的数据库配置

SAP OData MCP服务器可能需要数据库配置来查询元数据。检查：

1. **环境变量配置**
   ```bash
   # 在 sap-odata-to-mcp-server 服务中设置
   DB_HOST=postgres
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=enterprise_ai_platform
   ```

2. **Docker Compose配置**
   确保 `sap-odata-to-mcp-server` 服务有正确的环境变量：
   ```yaml
   sap-odata-to-mcp-server:
     environment:
       DB_HOST: ${DB_HOST:-postgres}
       DB_PORT: ${DB_PORT:-5432}
       DB_USER: ${DB_USER:-postgres}
       DB_PASSWORD: ${DB_PASSWORD:-postgres}
       DB_NAME: ${DB_NAME:-enterprise_ai_platform}
   ```

## 🔍 诊断步骤

### 步骤1: 检查数据库服务

```bash
# 1. 检查PostgreSQL容器是否运行
docker ps | grep postgres

# 2. 检查数据库连接
docker exec enterprise-ai-postgres pg_isready -U postgres

# 3. 检查数据库日志
docker logs enterprise-ai-postgres | tail -50
```

### 步骤2: 测试数据库连接

```bash
# 使用正确的密码测试连接
docker exec -it enterprise-ai-postgres psql -U postgres -d enterprise_ai_platform -c "SELECT version();"
```

### 步骤3: 检查服务配置

```bash
# 检查SAP OData MCP服务器的环境变量
docker exec sap-odata-to-mcp-server env | grep DB_

# 检查其他服务的数据库配置
docker exec mcp-gateway env | grep DB_
```

### 步骤4: 查看错误日志

```bash
# 查看SAP OData MCP服务器日志
docker logs sap-odata-to-mcp-server | tail -100

# 查看MCP Gateway日志
docker logs mcp-gateway | tail -100
```

## 📝 快速修复命令

### 如果密码是默认的 `postgres`

```bash
# 1. 确保 .env 文件中有正确的配置
cat > .env << EOF
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=enterprise_ai_platform
EOF

# 2. 重启相关服务
docker-compose restart sap-odata-to-mcp-server
docker-compose restart mcp-gateway
```

### 如果密码已更改

```bash
# 1. 更新 .env 文件
# 编辑 .env，设置正确的 DB_PASSWORD

# 2. 重启服务
docker-compose restart sap-odata-to-mcp-server
docker-compose restart mcp-gateway
```

## ✅ 验证修复

修复后，测试SAP查询：

```bash
# 通过API测试
curl -X POST http://localhost:8001/api/tools/sap_query/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "table": "I_SalesOrder",
      "query": ""
    }
  }'
```

## 📚 相关文档

- [数据库配置文档](../database/README.md)
- [环境变量配置](../env.example)
- [Docker Compose配置](../docker-compose.yml)
- [SAP查询问题总结](../docs/SAP_QUERY_ISSUE_SUMMARY.md)

## 🎯 预防措施

1. **统一配置管理**
   - 使用配置中心统一管理数据库配置
   - 避免在不同服务中使用不同的配置

2. **环境变量验证**
   - 在服务启动时验证数据库连接
   - 提供清晰的错误信息

3. **配置文档**
   - 维护清晰的配置文档
   - 记录所有环境变量的用途和默认值


