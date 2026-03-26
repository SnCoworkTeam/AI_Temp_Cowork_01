#!/usr/bin/env python3
"""
SAP MM实体批量导入脚本
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8005/api/metadata/business-entities"

def load_entities(file_path):
    """加载实体定义"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('entities', [])
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        sys.exit(1)

def create_entity(entity):
    """创建单个实体"""
    try:
        response = requests.post(BASE_URL, json=entity, timeout=10)
        if response.status_code in [200, 201]:
            result = response.json()
            entity_id = result.get('id', 'N/A')
            print(f"✅ Created: {entity['display_name']} (ID: {entity_id})")
            return result
        elif response.status_code == 409:
            # 实体已存在
            print(f"⚠️  Already exists: {entity['display_name']}")
            return None
        else:
            print(f"❌ Failed: {entity['display_name']} - HTTP {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务，请确保metadata-service正在运行")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating {entity['display_name']}: {e}")
        return None

def main():
    """主函数"""
    print("=" * 50)
    print("SAP MM实体批量导入")
    print("=" * 50)
    print()
    
    # 加载实体定义
    entities = load_entities('sap_mm_entities.json')
    print(f"📋 加载了 {len(entities)} 个实体定义\n")
    
    # 批量创建
    created = 0
    failed = 0
    skipped = 0
    
    for i, entity in enumerate(entities, 1):
        print(f"[{i}/{len(entities)}] 处理: {entity['display_name']}...")
        result = create_entity(entity)
        if result:
            created += 1
        elif result is None and "Already exists" in str(result):
            skipped += 1
        else:
            failed += 1
        time.sleep(0.3)  # 避免请求过快
        print()
    
    print("=" * 50)
    print("导入完成")
    print("=" * 50)
    print(f"✅ 成功: {created}")
    print(f"⚠️  跳过: {skipped}")
    print(f"❌ 失败: {failed}")
    print()
    
    if created > 0:
        print(f"🎉 成功创建了 {created} 个SAP MM实体！")
        print()
        print("下一步:")
        print("1. 执行本体构建: POST /api/ontology/sap/build")
        print("2. 验证知识图谱: GET /api/knowledge-graph/stats")

if __name__ == "__main__":
    main()





