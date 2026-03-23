"""
创建企业架构知识库
根据企业架构功能实施指南创建5个知识库
"""
import requests
import json
import sys
from typing import Dict, Any, Optional

# 配置
BASE_URL = "http://localhost:8004/api"  # 知识库服务地址
# 如果通过API Gateway，使用: "http://localhost:8080/api"

knowledge_bases = [
    {
        "name": "企业架构知识库",
        "description": "企业架构总览和跨架构域文档",
        "status": "active",
        "embedding_model": "default",
        "chunk_strategy": "semantic",
        "chunk_size": 1000,
        "chunk_overlap": 200
    },
    {
        "name": "业务架构知识库",
        "description": "业务流程、业务能力、业务服务文档",
        "status": "active",
        "embedding_model": "default",
        "chunk_strategy": "semantic",
        "chunk_size": 1000,
        "chunk_overlap": 200
    },
    {
        "name": "应用架构知识库",
        "description": "应用系统、应用服务、API接口文档",
        "status": "active",
        "embedding_model": "default",
        "chunk_strategy": "semantic",
        "chunk_size": 1000,
        "chunk_overlap": 200
    },
    {
        "name": "数据架构知识库",
        "description": "数据模型、数据实体、数据流文档",
        "status": "active",
        "embedding_model": "default",
        "chunk_strategy": "semantic",
        "chunk_size": 1000,
        "chunk_overlap": 200
    },
    {
        "name": "技术架构知识库",
        "description": "技术栈、基础设施、网络架构文档",
        "status": "active",
        "embedding_model": "default",
        "chunk_strategy": "semantic",
        "chunk_size": 1000,
        "chunk_overlap": 200
    }
]


def create_knowledge_bases(base_url: str = BASE_URL) -> Dict[str, str]:
    """
    创建企业架构知识库
    
    Args:
        base_url: 知识库服务的基础URL
        
    Returns:
        创建的知识库ID映射字典 {name: id}
    """
    created_kbs = {}
    
    print("=" * 50)
    print("创建企业架构知识库")
    print("=" * 50)
    print(f"目标服务: {base_url}")
    print()
    
    for kb in knowledge_bases:
        try:
            print(f"创建知识库: {kb['name']}...")
            
            # 准备请求数据
            request_data = {
                "name": kb["name"],
                "description": kb["description"],
                "embedding_model": kb.get("embedding_model", "default"),
                "chunk_strategy": kb.get("chunk_strategy", "fixed"),
                "chunk_size": kb.get("chunk_size", 1000),
                "chunk_overlap": kb.get("chunk_overlap", 200),
                "settings": {}
            }
            
            # 发送创建请求
            response = requests.post(
                f"{base_url}/knowledge-bases",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                kb_id = result.get("id")
                created_kbs[kb["name"]] = kb_id
                print(f"  ✅ 创建成功: {kb['name']} (ID: {kb_id})")
            else:
                error_msg = response.text
                # 检查是否是因为已存在
                if "already exists" in error_msg.lower() or response.status_code == 409:
                    print(f"  ⚠️  知识库已存在: {kb['name']}")
                    # 尝试获取现有知识库
                    list_response = requests.get(
                        f"{base_url}/knowledge-bases?search={kb['name']}",
                        timeout=30
                    )
                    if list_response.status_code == 200:
                        kbs = list_response.json()
                        if isinstance(kbs, dict) and "knowledge_bases" in kbs:
                            kbs_list = kbs["knowledge_bases"]
                        elif isinstance(kbs, list):
                            kbs_list = kbs
                        else:
                            kbs_list = []
                        
                        for existing_kb in kbs_list:
                            if existing_kb.get("name") == kb["name"]:
                                created_kbs[kb["name"]] = existing_kb.get("id")
                                print(f"  ✅ 使用现有知识库: {kb['name']} (ID: {existing_kb.get('id')})")
                                break
                else:
                    print(f"  ❌ 创建失败: {kb['name']} - {error_msg}")
                    
        except requests.exceptions.RequestException as e:
            print(f"  ❌ 网络错误: {kb['name']} - {str(e)}")
        except Exception as e:
            print(f"  ❌ 错误: {kb['name']} - {str(e)}")
    
    print()
    print("=" * 50)
    print("创建完成")
    print("=" * 50)
    print()
    print("创建的知识库:")
    for name, kb_id in created_kbs.items():
        print(f"  - {name}: {kb_id}")
    print()
    
    return created_kbs


def save_kb_ids(kb_ids: Dict[str, str], filename: str = "ea_knowledge_base_ids.json"):
    """保存知识库ID到文件"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(kb_ids, f, indent=2, ensure_ascii=False)
        print(f"知识库ID已保存到: {filename}")
    except Exception as e:
        print(f"保存知识库ID失败: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="创建企业架构知识库")
    parser.add_argument(
        "--url",
        type=str,
        default=BASE_URL,
        help=f"知识库服务URL (默认: {BASE_URL})"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="保存知识库ID到文件"
    )
    
    args = parser.parse_args()
    
    # 创建知识库
    kb_ids = create_knowledge_bases(args.url)
    
    # 保存ID（如果指定）
    if args.save and kb_ids:
        save_kb_ids(kb_ids)
    
    # 退出码
    if len(kb_ids) == len(knowledge_bases):
        print("✅ 所有知识库创建成功")
        sys.exit(0)
    else:
        print(f"⚠️  部分知识库创建失败 ({len(kb_ids)}/{len(knowledge_bases)})")
        sys.exit(1)

