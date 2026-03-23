"""
采购场景图谱构建脚本
将采购场景的业务活动、实体和映射关系构建为知识图谱并导入数据库
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入数据库相关模块
from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from database.src.models import (
    BusinessActivity,
    CapabilityUnit,
    ActivityCapabilityMapping
)

DATA_DIR = PROJECT_ROOT / "data" / "procurement"
VECTORS_DIR = DATA_DIR / "vectors"


def load_json_data(filename: str) -> List[Dict[str, Any]]:
    """加载JSON数据文件"""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"数据文件不存在: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def load_vectorized_activities() -> Dict[str, List[float]]:
    """加载向量化数据"""
    vectorized_file = VECTORS_DIR / "vectorized_activities.json"
    if not vectorized_file.exists():
        print("[WARN] 向量化数据文件不存在，将使用空向量")
        return {}
    
    with open(vectorized_file, 'r', encoding='utf-8') as f:
        vectorized_data = json.load(f)
    
    # 构建activity_id -> vector的映射
    vectors = {}
    for item in vectorized_data:
        activity_id = item.get("activity_id")
        vector = item.get("vector")
        if activity_id and vector:
            vectors[activity_id] = vector
    
    return vectors


def create_capability_units(mappings: List[Dict[str, Any]]) -> Dict[str, CapabilityUnit]:
    """创建能力单元"""
    capability_units = {}
    capability_ids = set()
    
    # 收集所有能力ID
    for mapping in mappings:
        capability_id = mapping.get("capability_id")
        if capability_id:
            capability_ids.add(capability_id)
    
    # 为每个能力创建能力单元
    for capability_id in capability_ids:
        # 解析能力类型和名称
        parts = capability_id.split(":")
        if len(parts) >= 3:
            capability_type = parts[1].capitalize()  # sap -> Sap, workflow -> Workflow
            capability_name = parts[2].replace("_", " ").title()
        else:
            capability_type = "Component"
            capability_name = capability_id
        
        capability_unit = CapabilityUnit(
            id=capability_id,
            name=capability_name,
            description=f"{capability_type}组件: {capability_name}",
            capability_type=capability_type,
            endpoint=f"http://api.internal/components/{parts[1]}/{parts[2]}" if len(parts) >= 3 else f"http://api.internal/components/{capability_id}",
            reliability_score=0.85,  # 默认可靠性分数
            usage_count=0
        )
        capability_units[capability_id] = capability_unit
    
    return capability_units


def import_business_activities(db, activities: List[Dict[str, Any]], vectors: Dict[str, List[float]]):
    """导入业务活动到数据库"""
    print(f"[INFO] 导入 {len(activities)} 个业务活动...")
    
    imported_count = 0
    updated_count = 0
    
    for activity in activities:
        activity_id = activity.get("id")
        if not activity_id:
            continue
        
        # 检查是否已存在
        existing = db.query(BusinessActivity).filter_by(id=activity_id).first()
        
        # 准备数据
        activity_data = {
            "id": activity_id,
            "name": activity.get("name", ""),
            "description": activity.get("description"),
            "activity_type": activity.get("activity_type", "action"),
            "business_domain": activity.get("business_domain", "procurement"),
            "success_criteria": activity.get("success_criteria"),
            "prerequisites": activity.get("prerequisites", []),
            "estimated_time": activity.get("estimated_time"),
            "risk_level": activity.get("risk_level"),
            "owner_dept": activity.get("owner_dept"),
            "source_type": activity.get("source_type"),
            "source_id": activity.get("source_id"),
            "vector_entity_uri": activity.get("vector_entity_uri", f"activity://procurement/{activity_id}"),
            "embedding_version": activity.get("embedding_version", "1.0"),
            "last_vectorized_at": datetime.now() if activity_id in vectors else None
        }
        
        if existing:
            # 更新现有记录
            for key, value in activity_data.items():
                if key != "id":
                    setattr(existing, key, value)
            updated_count += 1
        else:
            # 创建新记录
            new_activity = BusinessActivity(**activity_data)
            db.add(new_activity)
            imported_count += 1
    
    db.commit()
    print(f"  [OK] 导入: {imported_count} 个")
    print(f"  [OK] 更新: {updated_count} 个")
    print()


def import_capability_units(db, capability_units: Dict[str, CapabilityUnit]):
    """导入能力单元到数据库"""
    print(f"[INFO] 导入 {len(capability_units)} 个能力单元...")
    
    imported_count = 0
    updated_count = 0
    
    for capability_id, capability_unit in capability_units.items():
        # 检查是否已存在
        existing = db.query(CapabilityUnit).filter_by(id=capability_id).first()
        
        if existing:
            # 更新现有记录
            for key, value in capability_unit.__dict__.items():
                if not key.startswith("_") and key != "id":
                    setattr(existing, key, value)
            updated_count += 1
        else:
            # 创建新记录
            db.add(capability_unit)
            imported_count += 1
    
    db.commit()
    print(f"  [OK] 导入: {imported_count} 个")
    print(f"  [OK] 更新: {updated_count} 个")
    print()


def import_mappings(db, mappings: List[Dict[str, Any]]):
    """导入活动-能力映射到数据库"""
    print(f"[INFO] 导入 {len(mappings)} 个映射关系...")
    
    imported_count = 0
    updated_count = 0
    
    for mapping in mappings:
        mapping_id = mapping.get("id")
        activity_id = mapping.get("activity_id")
        capability_id = mapping.get("capability_id")
        
        if not mapping_id or not activity_id or not capability_id:
            continue
        
        # 检查活动是否存在
        activity = db.query(BusinessActivity).filter_by(id=activity_id).first()
        if not activity:
            print(f"  [WARN] 活动不存在: {activity_id}，跳过映射")
            continue
        
        # 检查能力是否存在
        capability = db.query(CapabilityUnit).filter_by(id=capability_id).first()
        if not capability:
            print(f"  [WARN] 能力不存在: {capability_id}，跳过映射")
            continue
        
        # 检查是否已存在
        existing = db.query(ActivityCapabilityMapping).filter_by(id=mapping_id).first()
        
        # 准备extra_metadata
        extra_metadata = {}
        if mapping.get("description"):
            extra_metadata["description"] = mapping.get("description")
        
        mapping_data = {
            "id": mapping_id,
            "activity_id": activity_id,
            "capability_id": capability_id,
            "mapping_type": mapping.get("mapping_type", "primary"),
            "confidence": mapping.get("confidence", 0.8),
            "success_rate": mapping.get("confidence", 0.8),  # 使用confidence作为初始success_rate
            "extra_metadata": extra_metadata if extra_metadata else {}
        }
        
        if existing:
            # 更新现有记录
            for key, value in mapping_data.items():
                if key != "id":
                    setattr(existing, key, value)
            updated_count += 1
        else:
            # 创建新记录
            new_mapping = ActivityCapabilityMapping(**mapping_data)
            db.add(new_mapping)
            imported_count += 1
    
    db.commit()
    print(f"  [OK] 导入: {imported_count} 个")
    print(f"  [OK] 更新: {updated_count} 个")
    print()
    
    
def main():
    """主函数"""
    print("=" * 60)
    print("采购场景图谱构建")
    print("=" * 60)
    print()
    
    # 初始化数据库连接
    try:
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            print("❌ 数据库连接失败")
            return 1
        
        init_session_factory()
        print("[OK] 数据库连接成功")
        print()
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return 1
    
    # 加载数据
    try:
        print("[INFO] 加载数据文件...")
        activities = load_json_data("activities.json")
        mappings = load_json_data("mappings.json")
        vectors = load_vectorized_activities()
        print(f"  [OK] 加载了 {len(activities)} 个业务活动")
        print(f"  [OK] 加载了 {len(mappings)} 个映射关系")
        print(f"  [OK] 加载了 {len(vectors)} 个向量")
        print()
    except Exception as e:
        print(f"[ERROR] 加载数据失败: {e}")
        return 1
    
    # 创建能力单元
    try:
        capability_units = create_capability_units(mappings)
        print(f"[OK] 创建了 {len(capability_units)} 个能力单元")
        print()
    except Exception as e:
        print(f"[ERROR] 创建能力单元失败: {e}")
        return 1
    
    # 导入数据到数据库
    db = next(get_db())
    try:
        # 导入业务活动
        import_business_activities(db, activities, vectors)
        
        # 导入能力单元
        import_capability_units(db, capability_units)
        
        # 导入映射关系
        import_mappings(db, mappings)
        
        print("=" * 60)
        print("[OK] 图谱构建完成！")
        print("=" * 60)
        print()
        print(f"[SUMMARY] 统计信息:")
        print(f"   - 业务活动: {len(activities)} 个")
        print(f"   - 能力单元: {len(capability_units)} 个")
        print(f"   - 映射关系: {len(mappings)} 个")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 导入数据失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit(main())

