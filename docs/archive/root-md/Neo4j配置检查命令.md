# Neo4j配置检查命令

## 应用服务器: 43.143.139.197
## 用户名: ubuntu
## 密码: Liu@bner1983

---

## 快速检查命令

### 方法1: 直接SSH连接执行

```bash
# 连接到服务器
ssh ubuntu@43.143.139.197
# 输入密码: Liu@bner1983

# 执行检查命令
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || cd ~/enterprise-ai-platform 2>/dev/null

# 检查1: 查看Neo4j环境变量配置
echo "=== 检查.env文件中的Neo4j配置 ==="
grep -i neo4j .env 2>/dev/null || echo "未找到Neo4j配置"

# 检查2: 测试网络连接
echo ""
echo "=== 测试到Neo4j服务器的网络连接 ==="
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/43.143.90.179/7687' 2>&1 && echo "✅ 网络连接成功" || echo "❌ 网络连接失败"

# 检查3: 检查Docker Compose配置
echo ""
echo "=== 检查Docker Compose配置 ==="
docker-compose config 2>/dev/null | grep -i NEO4J | head -10 || echo "未找到Neo4j配置"
```

### 方法2: 一键执行脚本

在服务器上创建并执行：

```bash
ssh ubuntu@43.143.139.197
# 输入密码后执行:

cat > /tmp/check-neo4j.sh << 'EOF'
#!/bin/bash
echo "=========================================="
echo "Neo4j配置检查"
echo "=========================================="

cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || cd ~/enterprise-ai-platform 2>/dev/null || { echo "项目目录未找到"; exit 1; }

echo ""
echo "[1] 检查.env文件中的Neo4j配置"
if [ -f .env ]; then
    if grep -q "NEO4J_URI" .env; then
        echo "✅ 已配置NEO4J_URI:"
        grep "NEO4J_URI" .env
    else
        echo "❌ 未配置NEO4J_URI"
    fi
    
    if grep -q "NEO4J_USER" .env; then
        echo "✅ 已配置NEO4J_USER:"
        grep "NEO4J_USER" .env
    else
        echo "❌ 未配置NEO4J_USER"
    fi
    
    if grep -q "NEO4J_PASSWORD" .env; then
        echo "✅ 已配置NEO4J_PASSWORD:"
        grep "NEO4J_PASSWORD" .env | sed 's/PASSWORD=.*/PASSWORD=***/'
    else
        echo "❌ 未配置NEO4J_PASSWORD"
    fi
else
    echo "❌ .env文件不存在"
fi

echo ""
echo "[2] 测试到Neo4j服务器的网络连接"
if timeout 5 bash -c 'cat < /dev/null > /dev/tcp/43.143.90.179/7687' 2>/dev/null; then
    echo "✅ 网络连接成功: 43.143.90.179:7687"
else
    echo "❌ 网络连接失败: 43.143.90.179:7687"
fi

echo ""
echo "[3] 检查Docker Compose配置"
if [ -f docker-compose.yml ]; then
    docker-compose config 2>/dev/null | grep -i NEO4J | head -10 || echo "未找到Neo4j配置"
fi

echo ""
echo "[4] 检查运行中容器的环境变量"
for container in $(docker ps --format "{{.Names}}" 2>/dev/null); do
    if docker exec $container env 2>/dev/null | grep -q NEO4J; then
        echo "容器 $container 包含Neo4j配置:"
        docker exec $container env | grep NEO4J
    fi
done

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
EOF

chmod +x /tmp/check-neo4j.sh
bash /tmp/check-neo4j.sh
```

---

## 如果未配置，添加配置

```bash
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || cd ~/enterprise-ai-platform 2>/dev/null

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

---

## 测试Neo4j连接

```bash
# 如果安装了Python和neo4j库
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
except ImportError:
    print("⚠️  neo4j库未安装，请安装: pip install neo4j")
except Exception as e:
    print(f"❌ Neo4j连接失败: {e}")
EOF
```

---

## 更新配置后重启服务

```bash
# 如果使用Docker Compose
docker-compose restart

# 或者重启特定服务
docker-compose restart knowledge-base
docker-compose restart metadata-service
```

---

## 总结

**需要检查的配置项**:
- ✅ NEO4J_URI=bolt://43.143.90.179:7687
- ✅ NEO4J_USER=neo4j
- ✅ NEO4J_PASSWORD=Neo4j@2024
- ✅ NEO4J_DATABASE=neo4j

**Neo4j服务器信息**:
- 地址: 43.143.90.179
- 端口: 7687 (Bolt), 7474 (HTTP)
- 用户名: neo4j
- 密码: Neo4j@2024



