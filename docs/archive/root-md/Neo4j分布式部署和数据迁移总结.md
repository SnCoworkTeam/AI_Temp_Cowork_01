# Neo4j分布式部署和数据迁移总结

**部署时间**: 2025-12-09  
**状态**: ✅ 部署完成，待数据迁移

---

## 部署架构

### 服务器分布

```
┌─────────────────────────────────┐
│  应用服务器                      │
│  43.143.139.197                 │
│  - Web UI (3000)                │
│  - API Gateway (8080)            │
│  - 业务服务                      │
│  - PostgreSQL                   │
└──────────────┬──────────────────┘
               │
               │ 网络连接
               │
┌──────────────▼──────────────────┐
│  Neo4j服务器                     │
│  43.143.90.179                  │
│  - Neo4j (7474, 7687)           │
│  - 图数据库                      │
└─────────────────────────────────┘
```

---

## 部署状态

### ✅ Neo4j服务器 (43.143.90.179)

- **服务状态**: ✅ 运行正常 (healthy)
- **Web界面**: http://43.143.90.179:7474/browser/
- **Bolt连接**: bolt://43.143.90.179:7687
- **用户名**: neo4j
- **密码**: Neo4j@2024
- **数据状态**: ⚠️ 数据库为空（0个节点，0个关系）

### ✅ 应用服务器 (43.143.139.197)

- **Neo4j配置**: ✅ 已配置
  ```env
  NEO4J_URI=bolt://43.143.90.179:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=Neo4j@2024
  NEO4J_DATABASE=neo4j
  ```
- **前端页面**: ✅ 已创建 `/admin/database/neo4j`
- **菜单配置**: ✅ 已添加"图数据库"菜单项

---

## 访问方式

### 1. Neo4j Web界面（直接访问）

**地址**: http://43.143.90.179:7474/browser/

**登录信息**:
- 用户名: `neo4j`
- 密码: `Neo4j@2024`

### 2. 应用内页面（嵌入访问）

**地址**: http://43.143.139.197:3000/admin/database/neo4j

**菜单路径**: 
```
管理 → 数据库管理 → 图数据库
```

**功能**:
- 嵌入Neo4j Browser界面
- 显示连接信息
- 支持在新窗口打开

---

## 数据迁移

### 当前状态

- **PostgreSQL数据**: 在应用服务器上
- **Neo4j数据**: 数据库为空，需要迁移

### 需要迁移的数据

1. **知识图谱数据**
   - `knowledge_graph_nodes` - 知识图谱节点
   - `knowledge_graph_edges` - 知识图谱边

2. **企业架构数据**
   - `business_processes` - 业务流程
   - `application_systems` - 应用系统
   - `data_entities` - 数据实体
   - `technology_components` - 技术组件
   - `architecture_relationships` - 架构关系

### 迁移方法

#### 方法1: 使用导入脚本（推荐）

在应用服务器上执行：

```bash
ssh ubuntu@43.143.139.197
cd /opt/enterprise-ai-platform

# 安装依赖（如果未安装）
pip3 install neo4j asyncpg

# 设置环境变量
export NEO4J_URI=bolt://43.143.90.179:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=Neo4j@2024

# 运行导入脚本
python3 scripts/import_neo4j_data_simple.py
```

#### 方法2: 在Docker容器中运行

```bash
# 在metadata-service容器中运行
docker exec -it enterprise-ai-metadata-service bash
cd /opt/enterprise-ai-platform
python3 scripts/import_neo4j_data_simple.py
```

#### 方法3: 使用Cypher直接导入

如果数据量不大，可以在Neo4j Browser中直接执行Cypher语句导入。

---

## 验证步骤

### 1. 验证Neo4j服务

```bash
# 检查服务状态
ssh root@43.143.90.179 "docker ps | grep neo4j"

# 测试连接
ssh root@43.143.90.179 "docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p 'Neo4j@2024' 'RETURN 1 AS test'"
```

### 2. 验证应用配置

```bash
# 检查环境变量
ssh ubuntu@43.143.139.197 "cd /opt/enterprise-ai-platform && grep -i neo4j .env"

# 测试网络连接
ssh ubuntu@43.143.139.197 "timeout 5 bash -c 'cat < /dev/null > /dev/tcp/43.143.90.179/7687' && echo '连接成功' || echo '连接失败'"
```

### 3. 验证数据迁移

```bash
# 在Neo4j服务器上
ssh root@43.143.90.179
docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p 'Neo4j@2024' << 'EOF'
// 统计节点
MATCH (n) RETURN count(n) AS node_count;

// 统计关系
MATCH ()-[r]->() RETURN count(r) AS rel_count;

// 查看节点类型
CALL db.labels() YIELD label RETURN label;
EOF
```

---

## 页面功能

### Neo4j Web界面功能

访问 http://43.143.90.179:7474/browser/ 可以：

1. **执行Cypher查询**
   ```cypher
   MATCH (n) RETURN n LIMIT 25
   ```

2. **查看图数据**
   - 可视化节点和关系
   - 交互式探索

3. **数据管理**
   - 创建节点和关系
   - 更新和删除数据
   - 执行复杂查询

### 应用内页面功能

访问 http://43.143.139.197:3000/admin/database/neo4j 可以：

1. **嵌入Neo4j Browser**
   - 在应用内直接使用Neo4j界面
   - 无需单独打开新窗口

2. **快速访问**
   - 显示连接信息
   - 一键在新窗口打开

---

## 下一步操作

### 1. 数据迁移（重要）

需要将PostgreSQL中的数据迁移到Neo4j：

```bash
# 在应用服务器上执行
cd /opt/enterprise-ai-platform
python3 scripts/import_neo4j_data_simple.py
```

### 2. 验证迁移结果

迁移后验证数据是否正确导入。

### 3. 测试应用连接

确保应用可以正常连接和查询Neo4j数据。

---

## 总结

✅ **Neo4j服务器**: 已部署并运行正常  
✅ **应用服务器配置**: 已配置Neo4j连接  
✅ **前端页面**: 已创建并配置菜单  
⚠️ **数据迁移**: 待执行

**Neo4j Web界面**: http://43.143.90.179:7474/browser/  
**应用内页面**: http://43.143.139.197:3000/admin/database/neo4j

---

**报告生成时间**: 2025-12-09



