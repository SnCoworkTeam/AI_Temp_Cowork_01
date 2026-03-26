# Neo4j图数据库手动部署指南

由于SSH自动连接遇到权限问题，请按照以下步骤手动部署：

## 步骤1: 连接到Neo4j服务器

```bash
# 使用Neo4j.pem密钥文件连接
ssh -i Neo4j.pem ubuntu@43.143.90.179
```

如果连接失败，请检查：
- 密钥文件是否正确
- 服务器上的公钥是否已配置
- 防火墙是否允许SSH连接

## 步骤2: 在服务器上创建项目目录

```bash
sudo mkdir -p /opt/neo4j-enterprise-ai
sudo chown $USER:$USER /opt/neo4j-enterprise-ai
cd /opt/neo4j-enterprise-ai
```

## 步骤3: 上传docker-compose文件

在本地执行（Windows PowerShell）：
```powershell
$keyPath = Resolve-Path .\Neo4j.pem
scp -i $keyPath docker-compose.neo4j-standalone.yml ubuntu@43.143.90.179:/opt/neo4j-enterprise-ai/
```

或者使用WinSCP、FileZilla等工具上传文件。

## 步骤4: 在服务器上创建.env文件

```bash
cd /opt/neo4j-enterprise-ai
cat > .env << 'EOF'
NEO4J_PASSWORD=neo4j_password
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
NEO4J_HTTPS_PORT=7473
EOF
```

## 步骤5: 停止现有Neo4j服务（如果有）

```bash
cd /opt/neo4j-enterprise-ai
docker-compose -f docker-compose.neo4j-standalone.yml down 2>/dev/null
docker stop enterprise-ai-neo4j-standalone 2>/dev/null
```

## 步骤6: 启动Neo4j服务

```bash
cd /opt/neo4j-enterprise-ai
docker-compose -f docker-compose.neo4j-standalone.yml up -d
```

## 步骤7: 检查服务状态

```bash
# 查看容器状态
docker ps | grep neo4j

# 查看端口监听
netstat -tlnp | grep -E '7474|7687'
# 或
ss -tlnp | grep -E '7474|7687'

# 查看日志
docker logs enterprise-ai-neo4j-standalone
```

## 步骤8: 测试连接

```bash
# 测试Cypher连接
docker exec enterprise-ai-neo4j-standalone cypher-shell -u neo4j -p neo4j_password "RETURN 1"
```

## 验证

1. **Web界面**: 访问 http://43.143.90.179:7474
2. **Bolt连接**: bolt://43.143.90.179:7687
3. **用户名**: neo4j
4. **密码**: neo4j_password

## 故障排除

### 如果Docker未安装
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 如果端口被占用
```bash
# 检查端口占用
sudo lsof -i :7474
sudo lsof -i :7687

# 修改.env文件中的端口号
```

### 如果容器启动失败
```bash
# 查看详细日志
docker logs enterprise-ai-neo4j-standalone

# 检查配置文件
cat docker-compose.neo4j-standalone.yml
cat .env
```

---

**完成部署后，请更新应用服务器的Neo4j连接配置！**

