import requests
import json

BASE_URL = "http://localhost:8004/api"

# 测试文档内容
test_content = """# 测试文档 - 知识库功能验证

这是一个用于测试知识库上传和处理功能的文档。

## 内容概述

本文档包含以下测试内容：
1. 采购订单管理流程
2. 供应商管理规范  
3. 物料主数据管理

## 采购订单管理

采购订单是企业采购管理的重要组成部分，包括：
- 订单创建
- 订单审批
- 订单执行
- 订单跟踪

## 供应商管理

供应商管理涉及供应商的全生命周期管理：
- 供应商注册
- 供应商评估
- 供应商合作
- 供应商绩效管理

## 物料主数据

物料主数据是企业管理的基础数据，包括：
- 物料编码
- 物料描述
- 物料分类
- 物料属性
"""

print("1. 测试文档上传...")
files = {
    'file': ('test_upload_doc.md', test_content.encode('utf-8'), 'text/markdown')
}
data = {
    'tags': 'test,上传测试',
    'category': '测试文档'
}

response = requests.post(
    f"{BASE_URL}/documents/upload",
    files=files,
    data=data,
    timeout=30
)

if response.status_code in [200, 201]:
    result = response.json()
    document_id = result.get("document_id") or result.get("id")
    filename = result.get("filename", "N/A")
    status = result.get("status", "N/A")
    
    print(f"✅ 文档上传成功!")
    print(f"   文档ID: {document_id}")
    print(f"   文件名: {filename}")
    print(f"   状态: {status}")
    
    # 等待处理
    import time
    print(f"\n2. 等待文档处理（10秒）...")
    time.sleep(10)
    
    # 检查处理进度
    print(f"\n3. 检查文档处理进度...")
    progress_response = requests.get(
        f"{BASE_URL}/documents/{document_id}/progress",
        timeout=30
    )
    
    if progress_response.status_code == 200:
        progress_data = progress_response.json()
        print(f"✅ 获取处理进度成功")
        print(f"   当前阶段: {progress_data.get('current_stage', 'N/A')}")
        print(f"   进度: {progress_data.get('progress', 0)}%")
        print(f"   状态: {progress_data.get('status', 'N/A')}")
        
        steps = progress_data.get('steps', [])
        if steps:
            print(f"\n   处理步骤:")
            for step in steps:
                step_name = step.get('name', 'N/A')
                completed = step.get('completed', 0)
                total = step.get('total', 0)
                step_status = step.get('status', 'N/A')
                print(f"   - {step_name}: {completed}/{total} ({step_status})")
    else:
        print(f"❌ 获取处理进度失败: {progress_response.status_code}")
    
    # 检查文档最终状态
    print(f"\n4. 检查文档最终状态...")
    detail_response = requests.get(
        f"{BASE_URL}/documents/{document_id}",
        timeout=30
    )
    
    if detail_response.status_code == 200:
        detail_data = detail_response.json()
        final_status = detail_data.get("status", "N/A")
        total_chunks = detail_data.get("total_chunks", 0)
        
        print(f"✅ 获取文档详情成功")
        print(f"   状态: {final_status}")
        print(f"   Chunks数量: {total_chunks}")
        
        if final_status == "processed" and total_chunks > 0:
            print(f"✅ 文档处理成功，chunks已生成!")
        elif final_status == "processing":
            print(f"⚠️ 文档仍在处理中，可能需要更多时间")
        elif final_status == "failed":
            print(f"❌ 文档处理失败")
    else:
        print(f"❌ 获取文档详情失败: {detail_response.status_code}")
        print(f"   响应: {detail_response.text}")
else:
    print(f"❌ 文档上传失败: {response.status_code}")
    print(f"   响应: {response.text}")
