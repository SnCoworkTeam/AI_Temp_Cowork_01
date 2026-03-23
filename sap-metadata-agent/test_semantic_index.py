"""
测试语义索引构建
"""
import requests
import json

API_URL = "http://localhost:8015/api/sap-metadata/discover"

# 测试1: 检查是否能从元数据服务加载数据
print("测试1: 检查元数据服务中的数据...")
response = requests.get("http://localhost:8005/api/data-assets?limit=5&source_system=SAP")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, list):
        print(f"✓ 找到 {len(data)} 个SAP数据资产")
        if len(data) > 0:
            print(f"  示例: {data[0].get('name', 'N/A')}")
    else:
        print(f"✓ API返回: {type(data)}")
        print(f"  内容: {json.dumps(data, indent=2)[:200]}")
else:
    print(f"✗ 元数据服务响应: {response.status_code}")

# 测试2: 调用语义索引API
print("\n测试2: 调用语义索引构建API...")
body = {
    "include_database": False,
    "include_odata": False,
    "include_bapi": False,
    "build_semantic_index": True,
    "sync_to_metadata_service": False
}

try:
    response = requests.post(API_URL, json=body, timeout=60)
    response.raise_for_status()
    result = response.json()
    
    print(f"✓ API调用成功")
    print(f"  响应键: {list(result.keys())}")
    
    # 检查元数据
    metadata = result.get('metadata', {})
    print(f"  元数据键: {list(metadata.keys())}")
    
    # 检查语义索引结果
    semantic_index = metadata.get('semantic_index', {})
    print(f"  语义索引: {semantic_index}")
    
    # 检查数据资产
    data_assets = result.get('data_assets', [])
    print(f"  数据资产数量: {len(data_assets)}")
    
    if len(data_assets) > 0:
        print(f"  第一个资产: {data_assets[0].get('name', 'N/A')}")
    
except Exception as e:
    print(f"✗ API调用失败: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"  响应: {e.response.text[:500]}")

