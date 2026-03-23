# 修复数据库配置问题

## 🔴 问题

`.env` 文件中的数据库配置：
- `DB_USER=ai_user`
- `DB_PASSWORD=ai_password`
- `DB_NAME=ai_platform`

但系统尝试用 `postgres` 用户连接，说明某些服务没有正确读取 `.env` 文件。

## 🔧 解决方案

### 方案1: 确保所有服务都使用 `.env` 文件（推荐）

检查 `docker-compose.yml` 中所有需要数据库连接的服务，确保它们都：
1. 使用 `env_file: - .env`
2. 或者使用 `${DB_USER}` 等变量（而不是硬编码默认值）

### 方案2: 更新 docker-compose.yml 中的默认值

如果某些服务必须使用默认值，确保默认值与 `.env` 文件一致。

### 方案3: 检查哪些服务需要数据库连接

需要数据库连接的服务可能包括：
- `mcp-gateway` - 已检查，有硬编码默认值
- `metadata-service` - 需要检查
- `sap-odata-to-mcp-server` - 可能需要（如果它查询元数据）
- 其他服务

## 📝 修复步骤

1. 检查所有服务的数据库配置
2. 确保使用 `${DB_USER}` 而不是 `${DB_USER:-postgres}`
3. 或者确保默认值与 `.env` 文件一致
4. 重启相关服务


