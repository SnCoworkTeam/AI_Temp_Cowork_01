"""
全面检查所有页面的数据显示问题
"""
import requests
import json

API_BASE = "http://43.143.139.197:8080"

print("=" * 70)
print("全面检查页面数据显示问题")
print("=" * 70)

# 1. 知识库页面
print("\n📚 1. 知识库页面检查")
print("-" * 70)
try:
    # 获取知识库列表
    response = requests.get(f"{API_BASE}/api/knowledge/knowledge-bases", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            kb_count = len(data)
            print(f"  ✅ 知识库列表API正常: {kb_count} 个知识库")
            if kb_count > 0:
                print(f"     示例: {data[0].get('name', 'N/A')}")
        elif isinstance(data, dict):
            kb_list = data.get('knowledge_bases', data.get('data', []))
            kb_count = len(kb_list) if isinstance(kb_list, list) else 0
            print(f"  ✅ 知识库列表API正常: {kb_count} 个知识库")
        else:
            print(f"  ⚠️  知识库列表API返回格式异常: {type(data)}")
    else:
        print(f"  ❌ 知识库列表API错误: {response.status_code}")
except Exception as e:
    print(f"  ❌ 知识库列表API异常: {e}")

# 2. 智能体页面
print("\n🤖 2. 智能体页面检查")
print("-" * 70)
try:
    response = requests.get(f"{API_BASE}/api/v1/agents", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            agent_count = len(data)
            print(f"  ✅ 智能体列表API正常: {agent_count} 个智能体")
            if agent_count > 0:
                print(f"     示例: {data[0].get('name', 'N/A')}")
        elif isinstance(data, dict):
            agents = data.get('agents', data.get('data', []))
            agent_count = len(agents) if isinstance(agents, list) else 0
            print(f"  ✅ 智能体列表API正常: {agent_count} 个智能体")
        else:
            print(f"  ⚠️  智能体列表API返回格式异常: {type(data)}")
    else:
        print(f"  ❌ 智能体列表API错误: {response.status_code}")
except Exception as e:
    print(f"  ❌ 智能体列表API异常: {e}")

# 3. 工作流页面
print("\n🔄 3. 工作流页面检查")
print("-" * 70)
try:
    response = requests.get(f"{API_BASE}/api/workflows", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            workflow_count = len(data)
            print(f"  ✅ 工作流列表API正常: {workflow_count} 个工作流")
        elif isinstance(data, dict):
            workflows = data.get('workflows', data.get('data', []))
            workflow_count = len(workflows) if isinstance(workflows, list) else 0
            print(f"  ✅ 工作流列表API正常: {workflow_count} 个工作流")
        else:
            print(f"  ⚠️  工作流列表API返回格式异常: {type(data)}")
    else:
        print(f"  ❌ 工作流列表API错误: {response.status_code}")
except Exception as e:
    print(f"  ❌ 工作流列表API异常: {e}")

# 4. 元数据页面
print("\n📊 4. 元数据页面检查")
print("-" * 70)
try:
    # 数据资产
    response = requests.get(f"{API_BASE}/api/metadata/assets", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            asset_count = len(data)
            print(f"  ✅ 数据资产API正常: {asset_count} 个资产")
        elif isinstance(data, dict):
            assets = data.get('assets', data.get('data', []))
            asset_count = len(assets) if isinstance(assets, list) else 0
            print(f"  ✅ 数据资产API正常: {asset_count} 个资产")
        else:
            print(f"  ⚠️  数据资产API返回格式异常: {type(data)}")
    else:
        print(f"  ❌ 数据资产API错误: {response.status_code}")
except Exception as e:
    print(f"  ❌ 数据资产API异常: {e}")

# 5. 知识图谱页面（详细检查）
print("\n🕸️  5. 知识图谱页面检查")
print("-" * 70)
for limit in [100, 500, 715]:
    try:
        response = requests.get(f"{API_BASE}/api/knowledge-graph/graph?limit={limit}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get("nodes", [])
            links = data.get("links", [])
            print(f"  limit={limit}: 节点={len(nodes)}, 边={len(links)}")
            
            if limit == 715 and len(links) == 0:
                print(f"     ⚠️  问题：limit=715时边数为0，应该接近304")
        else:
            print(f"  ❌ limit={limit}时API错误: {response.status_code}")
    except Exception as e:
        print(f"  ❌ limit={limit}时API异常: {e}")

# 6. 文档页面
print("\n📄 6. 文档页面检查")
print("-" * 70)
try:
    response = requests.get(f"{API_BASE}/api/knowledge/documents?page=1&page_size=10", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict):
            docs = data.get('documents', data.get('data', []))
            total = data.get('total', len(docs) if isinstance(docs, list) else 0)
            doc_count = len(docs) if isinstance(docs, list) else 0
            print(f"  ✅ 文档列表API正常: {doc_count} 个文档（总数: {total}）")
        elif isinstance(data, list):
            print(f"  ✅ 文档列表API正常: {len(data)} 个文档")
        else:
            print(f"  ⚠️  文档列表API返回格式异常: {type(data)}")
    else:
        print(f"  ❌ 文档列表API错误: {response.status_code}")
except Exception as e:
    print(f"  ❌ 文档列表API异常: {e}")

# 7. 仪表板统计
print("\n📈 7. 仪表板统计检查")
print("-" * 70)
try:
    response = requests.get(f"{API_BASE}/api/analytics/stats", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ 统计API正常")
        print(f"     文档总数: {data.get('totalDocuments', 'N/A')}")
        print(f"     知识库数: {data.get('totalKnowledgeBases', 'N/A')}")
        print(f"     用户数: {data.get('totalUsers', 'N/A')}")
    else:
        print(f"  ❌ 统计API错误: {response.status_code}")
except Exception as e:
    print(f"  ❌ 统计API异常: {e}")

# 8. 企业架构
print("\n🏢 8. 企业架构页面检查")
print("-" * 70)
try:
    response = requests.get(f"{API_BASE}/api/enterprise-architecture/overview", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ 企业架构API正常")
        print(f"     业务架构: {data.get('business_architecture', {})}")
    else:
        print(f"  ❌ 企业架构API错误: {response.status_code}")
except Exception as e:
    print(f"  ❌ 企业架构API异常: {e}")

print("\n" + "=" * 70)
print("检查完成")
print("=" * 70)



