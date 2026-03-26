# Neo4j本地到远程数据迁移报告

**迁移时间**: 2025-12-09  
**状态**: 🔄 迁移进行中

---

## 迁移概览

### 数据源

- **本地Neo4j**: `bolt://localhost:7687`
- **容器名**: `enterprise-ai-neo4j`
- **数据量**: 
  - 节点: **3,651** 个
  - 关系: **1,224** 个

### 目标服务器

- **远程Neo4j**: `bolt://43.143.90.179:7687`
- **Web界面**: http://43.143.90.179:7474/browser/
- **用户名**: `neo4j`
- **密码**: `Neo4j@2024`

---

## 迁移方法

### 使用Python脚本直接迁移

**脚本**: `scripts/migrate_neo4j_local_to_remote.py`

**工作原理**:
1. 同时连接本地和远程Neo4j
2. 从本地批量读取节点和关系
3. 通过UUID建立ID映射
4. 批量写入远程Neo4j
5. 验证迁移结果

**优点**:
- 不需要停止数据库
- 可以实时监控进度
- 支持增量迁移

---

## 迁移步骤

### 1. 连接检查

- ✅ 连接本地Neo4j
- ✅ 连接远程Neo4j

### 2. 数据检查

- ✅ 统计本地数据量
- ✅ 清空远程数据库（可选）

### 3. 节点迁移

- 🔄 批量迁移节点（每批100个）
- 通过UUID建立ID映射

### 4. 关系迁移

- 🔄 使用ID映射迁移关系
- 保持关系类型和属性

### 5. 验证

- 对比节点和关系数量
- 检查数据完整性

---

## 执行命令

```powershell
# 设置环境变量（可选）
$env:LOCAL_NEO4J_URI = "bolt://localhost:7687"
$env:LOCAL_NEO4J_USER = "neo4j"
$env:LOCAL_NEO4J_PASSWORD = "neo4j_password"

$env:REMOTE_NEO4J_URI = "bolt://43.143.90.179:7687"
$env:REMOTE_NEO4J_USER = "neo4j"
$env:REMOTE_NEO4J_PASSWORD = "Neo4j@2024"

# 执行迁移
python scripts/migrate_neo4j_local_to_remote.py
```

---

## 验证迁移结果

### 检查远程数据

```bash
# SSH到远程服务器
ssh -i Neo4j.pem root@43.143.90.179

# 检查节点数量
docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p 'Neo4j@2024' \
  "MATCH (n) RETURN count(n) AS node_count;"

# 检查关系数量
docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p 'Neo4j@2024' \
  "MATCH ()-[r]->() RETURN count(r) AS rel_count;"

# 查看节点类型
docker exec enterprise-ai-neo4j cypher-shell -u neo4j -p 'Neo4j@2024' \
  "CALL db.labels() YIELD label RETURN label ORDER BY label;"
```

### 在Neo4j Browser中查看

访问: http://43.143.90.179:7474/browser/

执行查询:
```cypher
// 查看所有节点
MATCH (n) RETURN n LIMIT 25

// 查看节点统计
MATCH (n) 
RETURN labels(n) AS label, count(n) AS count 
ORDER BY count DESC

// 查看关系统计
MATCH ()-[r]->() 
RETURN type(r) AS type, count(r) AS count 
ORDER BY count DESC
```

---

## 预计时间

- **节点迁移**: 约 5-10 分钟（3,651个节点）
- **关系迁移**: 约 2-5 分钟（1,224个关系）
- **总计**: 约 10-15 分钟

---

## 注意事项

1. **网络连接**: 确保本地可以访问远程Neo4j服务器
2. **数据一致性**: 迁移过程中本地数据不应修改
3. **性能影响**: 迁移过程会占用网络和数据库资源
4. **备份**: 建议迁移前备份远程数据库

---

## 故障处理

### 如果迁移中断

1. 检查网络连接
2. 检查远程Neo4j服务状态
3. 重新运行脚本（会清空远程数据库）

### 如果数据不匹配

1. 检查UUID字段是否存在
2. 检查节点属性是否完整
3. 手动验证部分数据

---

## 替代方案

如果Python脚本迁移失败，可以使用：

1. **neo4j-admin dump/load**（需要停止数据库）
2. **APOC导出/导入**（需要APOC插件）
3. **手动Cypher导出**（适合小数据量）

---

**报告生成时间**: 2025-12-09



