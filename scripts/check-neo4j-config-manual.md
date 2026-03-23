# Neo4j配置手动检查指南

## 应用服务器: 43.143.139.197

### 检查步骤

#### 1. 连接到应用服务器

```bash
ssh -i enterprise_ai_platform.pem root@43.143.139.197
# 或者如果密钥文件权限有问题，使用密码登录
ssh root@43.143.139.197
```

#### 2. 检查环境变量配置

```bash
cd /opt/enterprise-ai-platform
# 或者
cd /root/enterprise-ai-platform

# 检查.env文件中的Neo4j配置
grep -i neo4j .env
```

**期望结果**:
```env
NEO4J_URI=bolt://43.143.90.179:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Neo4j@2024
NEO4J_DATABASE=neo4j
```

**如果未找到配置**，需要添加：

```bash
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

#### 3. 检查Docker Compose配置

```bash
cd /opt/enterprise-ai-platform

# 检查docker-compose.yml中的Neo4j配置
docker-compose config | grep -i neo4j

# 或者查看服务环境变量
docker-compose config | grep -A 10 -B 5 NEO4J
```

**如果使用Docker Compose，确保服务环境变量包含**:
```yaml
environment:
  NEO4J_URI: bolt://43.143.90.179:7687
  NEO4J_USER: neo4j
  NEO4J_PASSWORD: Neo4j@2024
  NEO4J_DATABASE: neo4j
```

#### 4. 测试网络连接

```bash
# 测试到Neo4j服务器的网络连接
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/43.143.90.179/7687' && echo "✅ 网络连接成功" || echo "❌ 网络连接失败"

# 或者使用telnet
telnet 43.143.90.179 7687
# 如果连接成功，会看到连接信息，按Ctrl+]退出
```

#### 5. 测试Neo4j数据库连接

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
    print("⚠️  neo4j库未安装")
except Exception as e:
    print(f"❌ Neo4j连接失败: {e}")
EOF
```

#### 6. 检查运行中的容器环境变量

```bash
# 查看所有容器的环境变量
docker ps --format "table {{.Names}}\t{{.Image}}"

# 检查特定服务的环境变量（替换service_name为实际服务名）
docker exec <service_name> env | grep NEO4J

# 例如检查knowledge-base服务
docker exec enterprise-ai-knowledge-base env | grep NEO4J
```

---

## 一键检查脚本

在应用服务器上执行以下脚本：

```bash
#!/bin/bash
# Neo4j配置检查脚本

echo "=========================================="
echo "Neo4j配置检查"
echo "=========================================="

# 检查1: 环境变量
echo ""
echo "[1] 检查.env文件中的Neo4j配置"
cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || { echo "项目目录未找到"; exit 1; }

if [ -f .env ]; then
    echo "找到.env文件"
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

# 检查2: 网络连接
echo ""
echo "[2] 测试到Neo4j服务器的网络连接"
if timeout 5 bash -c 'cat < /dev/null > /dev/tcp/43.143.90.179/7687' 2>/dev/null; then
    echo "✅ 网络连接成功: 43.143.90.179:7687"
else
    echo "❌ 网络连接失败: 43.143.90.179:7687"
    echo "   请检查防火墙和安全组设置"
fi

# 检查3: Docker Compose配置
echo ""
echo "[3] 检查Docker Compose配置"
if [ -f docker-compose.yml ]; then
    echo "找到docker-compose.yml文件"
    docker-compose config 2>/dev/null | grep -i NEO4J || echo "未找到Neo4j配置"
else
    echo "docker-compose.yml文件不存在"
fi

# 检查4: 运行中的容器
echo ""
echo "[4] 检查运行中容器的环境变量"
for container in $(docker ps --format "{{.Names}}"); do
    if docker exec $container env 2>/dev/null | grep -q NEO4J; then
        echo "容器 $container 包含Neo4j配置:"
        docker exec $container env | grep NEO4J
    fi
done

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
```

---

## 配置更新脚本

如果需要更新配置，使用以下脚本：

```bash
#!/bin/bash
# 更新Neo4j配置

cd /opt/enterprise-ai-platform 2>/dev/null || cd /root/enterprise-ai-platform 2>/dev/null || { echo "项目目录未找到"; exit 1; }

# 备份
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份.env文件"
fi

# 移除旧配置
if [ -f .env ]; then
    sed -i '/^NEO4J_/d' .env
    echo "✅ 已移除旧Neo4j配置"
fi

# 添加新配置
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

echo "✅ 已添加Neo4j配置"
echo ""
echo "=== 更新后的配置 ==="
grep -i neo4j .env
```

---

## 验证配置

更新配置后，需要重启相关服务：

```bash
# 如果使用Docker Compose
docker-compose restart

# 或者重启特定服务
docker-compose restart knowledge-base
docker-compose restart metadata-service
```

然后验证配置是否生效：

```bash
# 检查服务日志
docker-compose logs knowledge-base | grep -i neo4j

# 或者检查容器环境变量
docker exec enterprise-ai-knowledge-base env | grep NEO4J
```



