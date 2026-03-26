# Neo4j连接配置检查报告

**检查时间**: 2025-12-09  
**应用服务器**: 43.143.139.197  
**Neo4j服务器**: 43.143.90.179:7687

---

## 需要检查的配置

### 1. 环境变量配置 (.env文件)

在应用服务器 `/opt/enterprise-ai-platform/.env` 文件中，需要包含以下Neo4j配置：

```env
# Neo4j图数据库配置
NEO4J_URI=bolt://43.143.90.179:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Neo4j@2024
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
NEO4J_CONNECTION_TIMEOUT=30
```

### 2. Docker Compose配置

如果使用Docker Compose，确保服务环境变量中包含Neo4j配置。

---

## 手动检查步骤

### 步骤1: 检查现有配置

SSH连接到应用服务器：
```bash
ssh -i enterprise_ai_platform.pem root@43.143.139.197
```

检查环境变量：
```bash
cd /opt/enterprise-ai-platform
grep -i neo4j .env
```

### 步骤2: 更新配置（如果未配置）

如果未找到Neo4j配置，执行以下命令：

```bash
cd /opt/enterprise-ai-platform

# 备份现有配置
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 添加Neo4j配置
cat >> .env << 'EOF'
# Neo4j图数据库配置
NEO4J_URI=bolt://43.143.90.179:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Neo4j@2024
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
NEO4J_CONNECTION_TIMEOUT=30
EOF

# 验证配置
grep -i neo4j .env
```

### 步骤3: 测试网络连接

测试从应用服务器到Neo4j服务器的网络连接：

```bash
# 测试端口连接
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/43.143.90.179/7687' && echo "✅ 网络连接成功" || echo "❌ 网络连接失败"

# 或者使用telnet
telnet 43.143.90.179 7687
```

### 步骤4: 测试Neo4j连接

如果服务器上安装了Python和neo4j库：

```bash
python3 << 'EOF'
from neo4j import GraphDatabase

try:
    driver = GraphDatabase.driver(
        'bolt://43.143.90.179:7687',
        auth=('neo4j', 'Neo4j@2024')
    )
    with driver.session() as session:
        result = session.run('RETURN 1 AS test')
        record = result.single()
        print(f"✅ Neo4j连接成功: {record['test']}")
    driver.close()
except Exception as e:
    print(f"❌ Neo4j连接失败: {e}")
EOF
```

---

## 配置更新脚本

如果需要在应用服务器上批量更新配置，可以使用以下脚本：

```bash
#!/bin/bash
# 更新Neo4j配置脚本

APP_SERVER="43.143.139.197"
NEO4J_SERVER="43.143.90.179"
NEO4J_PORT="7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="Neo4j@2024"

ssh -i enterprise_ai_platform.pem root@${APP_SERVER} << EOF
cd /opt/enterprise-ai-platform

# 备份
cp .env .env.backup.\$(date +%Y%m%d_%H%M%S)

# 移除旧配置
sed -i '/^NEO4J_/d' .env

# 添加新配置
cat >> .env << 'NEO4J_EOF'
# Neo4j图数据库配置
NEO4J_URI=bolt://${NEO4J_SERVER}:${NEO4J_PORT}
NEO4J_USER=${NEO4J_USER}
NEO4J_PASSWORD=${NEO4J_PASSWORD}
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_ACQUISITION_TIMEOUT=60
NEO4J_CONNECTION_TIMEOUT=30
NEO4J_EOF

echo "✅ 配置已更新"
grep -i neo4j .env
EOF
```

---

## 验证配置

### 1. 检查环境变量是否生效

重启相关服务后，检查环境变量：

```bash
# 如果使用Docker
docker exec <container_name> env | grep NEO4J

# 如果直接运行Python
python3 -c "import os; print(os.getenv('NEO4J_URI'))"
```

### 2. 测试应用连接

在应用代码中测试连接：

```python
from database.src.core.neo4j_client import Neo4jClient

client = Neo4jClient()
if await client.connect():
    print("✅ Neo4j连接成功")
    result = await client.execute_query("RETURN 1 AS test")
    print(f"测试结果: {result}")
else:
    print("❌ Neo4j连接失败")
```

---

## 常见问题

### 问题1: 网络连接失败

**原因**: 防火墙或安全组未开放端口

**解决方案**:
1. 检查Neo4j服务器(43.143.90.179)的安全组，确保开放7687端口
2. 检查应用服务器(43.143.139.197)的出站规则
3. 测试网络连接: `telnet 43.143.90.179 7687`

### 问题2: 认证失败

**原因**: 用户名或密码错误

**解决方案**:
1. 确认Neo4j密码为 `Neo4j@2024`
2. 检查环境变量中的密码是否正确
3. 尝试在Neo4j Web界面登录验证: http://43.143.90.179:7474

### 问题3: 配置未生效

**原因**: 服务未重启或环境变量未加载

**解决方案**:
1. 重启相关服务: `docker-compose restart`
2. 检查服务日志: `docker logs <service_name>`
3. 确认.env文件路径正确

---

## 总结

✅ **Neo4j服务器已部署**: 43.143.90.179:7687  
⚠️ **应用服务器配置**: 需要检查并更新  
📝 **配置项**: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

**下一步**: 按照上述步骤检查并更新应用服务器的Neo4j配置。



