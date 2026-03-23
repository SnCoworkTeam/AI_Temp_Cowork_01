"""
创建企业架构元数据分类
根据企业架构功能实施指南创建分类
"""
import requests
import json
import sys
from typing import Dict, Any, Optional

# 配置
BASE_URL = "http://localhost:8005/api/metadata"  # 元数据服务地址
# 如果通过API Gateway，使用: "http://localhost:8080/api/metadata"

classifications = [
    {
        "name": "enterprise_architecture",
        "display_name": "企业架构",
        "description": "企业架构相关元数据",
        "parent": None
    },
    {
        "name": "business_architecture",
        "display_name": "业务架构",
        "description": "业务架构相关元数据",
        "parent": "enterprise_architecture"
    },
    {
        "name": "application_architecture",
        "display_name": "应用架构",
        "description": "应用架构相关元数据",
        "parent": "enterprise_architecture"
    },
    {
        "name": "data_architecture",
        "display_name": "数据架构",
        "description": "数据架构相关元数据",
        "parent": "enterprise_architecture"
    },
    {
        "name": "technology_architecture",
        "display_name": "技术架构",
        "description": "技术架构相关元数据",
        "parent": "enterprise_architecture"
    }
]


def create_classifications(base_url: str = BASE_URL) -> Dict[str, bool]:
    """
    创建企业架构元数据分类
    
    Args:
        base_url: 元数据服务的基础URL
        
    Returns:
        创建结果字典 {name: success}
    """
    results = {}
    
    print("=" * 50)
    print("创建企业架构元数据分类")
    print("=" * 50)
    print(f"目标服务: {base_url}")
    print()
    
    # 先创建父分类
    parent_classifications = [c for c in classifications if c["parent"] is None]
    child_classifications = [c for c in classifications if c["parent"] is not None]
    
    # 创建父分类
    for classification in parent_classifications:
        try:
            print(f"创建分类: {classification['display_name']}...")
            
            request_data = {
                "name": classification["name"],
                "display_name": classification["display_name"],
                "description": classification["description"],
                "parent": classification["parent"]
            }
            
            response = requests.post(
                f"{base_url}/classifications",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                results[classification["name"]] = True
                print(f"  ✅ 创建成功: {classification['display_name']}")
            else:
                error_msg = response.text
                if "already exists" in error_msg.lower() or response.status_code == 409:
                    results[classification["name"]] = True
                    print(f"  ⚠️  分类已存在: {classification['display_name']}")
                else:
                    results[classification["name"]] = False
                    print(f"  ❌ 创建失败: {classification['display_name']} - {error_msg}")
                    
        except requests.exceptions.RequestException as e:
            results[classification["name"]] = False
            print(f"  ❌ 网络错误: {classification['display_name']} - {str(e)}")
        except Exception as e:
            results[classification["name"]] = False
            print(f"  ❌ 错误: {classification['display_name']} - {str(e)}")
    
    # 创建子分类
    for classification in child_classifications:
        try:
            print(f"创建分类: {classification['display_name']} (父: {classification['parent']})...")
            
            request_data = {
                "name": classification["name"],
                "display_name": classification["display_name"],
                "description": classification["description"],
                "parent": classification["parent"]
            }
            
            response = requests.post(
                f"{base_url}/classifications",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                results[classification["name"]] = True
                print(f"  ✅ 创建成功: {classification['display_name']}")
            else:
                error_msg = response.text
                if "already exists" in error_msg.lower() or response.status_code == 409:
                    results[classification["name"]] = True
                    print(f"  ⚠️  分类已存在: {classification['display_name']}")
                else:
                    results[classification["name"]] = False
                    print(f"  ❌ 创建失败: {classification['display_name']} - {error_msg}")
                    
        except requests.exceptions.RequestException as e:
            results[classification["name"]] = False
            print(f"  ❌ 网络错误: {classification['display_name']} - {str(e)}")
        except Exception as e:
            results[classification["name"]] = False
            print(f"  ❌ 错误: {classification['display_name']} - {str(e)}")
    
    print()
    print("=" * 50)
    print("创建完成")
    print("=" * 50)
    print()
    
    success_count = sum(1 for v in results.values() if v)
    print(f"成功: {success_count}/{len(classifications)}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="创建企业架构元数据分类")
    parser.add_argument(
        "--url",
        type=str,
        default=BASE_URL,
        help=f"元数据服务URL (默认: {BASE_URL})"
    )
    
    args = parser.parse_args()
    
    # 创建分类
    results = create_classifications(args.url)
    
    # 退出码
    success_count = sum(1 for v in results.values() if v)
    if success_count == len(classifications):
        print("✅ 所有分类创建成功")
        sys.exit(0)
    else:
        print(f"⚠️  部分分类创建失败 ({success_count}/{len(classifications)})")
        sys.exit(1)

