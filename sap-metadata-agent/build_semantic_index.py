"""
构建语义索引脚本
"""
import requests
import json
import sys
from datetime import datetime

API_URL = "http://localhost:8015/api/sap-metadata/discover"

def build_semantic_index():
    """构建语义索引"""
    print("=" * 60)
    print("开始构建语义索引")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        body = {
            "include_database": False,
            "include_odata": False,
            "build_semantic_index": True,
            "sync_to_metadata_service": False
        }
        
        print("正在调用SAP元数据代理API...")
        response = requests.post(API_URL, json=body, timeout=1800)
        response.raise_for_status()
        
        result = response.json()
        index_result = result.get('metadata', {}).get('semantic_index', {})
        
        indexed = index_result.get('indexed', 0)
        failed = index_result.get('failed', 0)
        
        print(f"\n✓ 语义索引构建完成")
        print(f"   索引成功: {indexed}")
        print(f"   索引失败: {failed}")
        
        if indexed > 0:
            print(f"\n✅ 语义索引构建成功！")
            return True
        else:
            print(f"\n⚠️  没有文档被索引")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 构建失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   响应内容: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return False

if __name__ == "__main__":
    success = build_semantic_index()
    sys.exit(0 if success else 1)


