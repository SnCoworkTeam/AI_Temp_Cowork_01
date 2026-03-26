# Neo4j数据迁移说明

**状态**: ⚠️ 数据尚未迁移

---

## 当前状态

### Neo4j数据库状态

- **服务器**: 43.143.90.179:7687
- **节点数量**: 0
- **关系数量**: 0
- **状态**: 数据库为空，等待数据导入

### PostgreSQL数据状态

数据在应用服务器 (43.143.139.197) 的PostgreSQL中，需要迁移到Neo4j。

---

## 数据迁移方法

### 方法1: 在应用服务器上运行导入脚本（推荐）

**步骤**:

1. **安装依赖**（在应用服务器上）:
```bash
ssh ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform

# 安装Python依赖
pip3 install neo4j asyncpg
# 或者如果在虚拟环境中
source venv/bin/activate
pip install neo4j asyncpg
```

2. **设置环境变量**:
```bash
export NEO4J_URI=bolt://43.143.90.179:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=Neo4j@2024

# PostgreSQL配置（从.env文件读取或手动设置）
export DB_HOST=postgres  # 或 localhost
export DB_PORT=5432
export DB_USER=ai_user
export DB_PASSWORD=ai_password
export DB_NAME=ai_platform
```

3. **运行导入脚本**:
```bash
cd /opt/enterprise-ai-platform
python3 scripts/import_neo4j_data_simple.py
```

### 方法2: 在Docker容器中运行

如果应用服务器使用Docker，可以在容器中运行：

```bash
# 找到包含数据库访问的容器
docker ps | grep -E 'knowledge|metadata|api'

# 在容器中运行（替换container_name为实际容器名）
docker exec -it <container_name> python3 /opt/enterprise-ai-platform/scripts/import_neo4j_data_simple.py
```

### 方法3: 使用API导入

通过API Gateway调用导入接口（如果已实现）：

```bash
curl -X POST http://43.143.139.197:8080/api/neo4j/import \
  -H "Content-Type: application/json" \
  -d '{"source": "postgresql"}'
```

---

## 需要迁移的数据

### 1. 知识图谱数据

- **表**: `knowledge_graph_nodes`
- **表**: `knowledge_graph_edges`
- **内容**: 知识图谱的节点和关系

### 2. 企业架构数据

- **表**: `business_processes`
- **表**: `application_systems`
- **表**: `data_entities`
- **表**: `technology_components`
- **表**: `architecture_relationships`
- **内容**: 企业架构实体和关系

---

## 验证迁移结果

迁移完成后，验证数据：

```bash
# 在Neo4j服务器上
ssh root@43.143.90.179
docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p 'Neo4j@2024' << 'EOF'
// 统计节点数量
MATCH (n) RETURN count(n) AS node_count;

// 统计关系数量
MATCH ()-[r]->() RETURN count(r) AS relationship_count;

// 查看节点类型
CALL db.labels() YIELD label RETURN label ORDER BY label;

// 查看关系类型
CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType;
EOF
```

---

## 页面访问

### Neo4j Web界面

**地址**: http://43.143.90.179:7474

**登录信息**:
- 用户名: `neo4j`
- 密码: `Neo4j@2024`

### 应用内页面

**地址**: http://43.143.139.197:3000/admin/database/neo4j

**菜单路径**: 管理 → 数据库管理 → 图数据库

---

## 注意事项

1. **数据量**: 如果数据量大，导入可能需要较长时间
2. **网络**: 确保应用服务器可以访问Neo4j服务器 (43.143.90.179:7687)
3. **权限**: 确保Neo4j用户有写入权限
4. **备份**: 导入前建议备份Neo4j数据

---

## 快速导入命令

在应用服务器上执行：

```bash
cd /opt/enterprise-ai-platform
source .env  # 加载环境变量
pip3 install neo4j asyncpg  # 如果未安装
python3 scripts/import_neo4j_data_simple.py
```

---

**报告生成时间**: 2025-12-09



