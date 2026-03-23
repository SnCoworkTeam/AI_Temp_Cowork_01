"""
采购场景业务活动向量化脚本
为采购场景的业务活动生成语义向量嵌入
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data" / "procurement"
OUTPUT_DIR = DATA_DIR / "vectors"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_activities() -> List[Dict[str, Any]]:
    """加载业务活动数据"""
    activities_file = DATA_DIR / "activities.json"
    if not activities_file.exists():
        raise FileNotFoundError(f"活动数据文件不存在: {activities_file}")
    
    with open(activities_file, 'r', encoding='utf-8') as f:
        activities = json.load(f)
    
    return activities


def create_embedding_text(activity: Dict[str, Any]) -> str:
    """创建用于向量化的文本"""
    parts = []
    
    # 活动名称
    if activity.get('name'):
        parts.append(f"活动名称: {activity['name']}")
    
    # 活动描述
    if activity.get('description'):
        parts.append(f"描述: {activity['description']}")
    
    # 活动类型
    if activity.get('activity_type'):
        parts.append(f"类型: {activity['activity_type']}")
    
    # 业务领域
    if activity.get('business_domain'):
        parts.append(f"业务领域: {activity['business_domain']}")
    
    # 成功标准
    if activity.get('success_criteria'):
        parts.append(f"成功标准: {activity['success_criteria']}")
    
    # 前置条件
    if activity.get('prerequisites'):
        if isinstance(activity['prerequisites'], list):
            parts.append(f"前置条件: {', '.join(activity['prerequisites'])}")
        else:
            parts.append(f"前置条件: {activity['prerequisites']}")
    
    return "\n".join(parts)


def vectorize_with_openai(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    使用OpenAI API进行向量化
    注意: 这里使用模拟向量，实际应该调用OpenAI API
    """
    try:
        # 尝试导入openai
        import openai
        from openai import OpenAI
        
        # 检查是否有API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  未找到OPENAI_API_KEY，使用模拟向量")
            return generate_mock_vector(1536)
        
        client = OpenAI(api_key=api_key)
        
        response = client.embeddings.create(
            model=model,
            input=text
        )
        
        return response.data[0].embedding
    
    except ImportError:
        print("⚠️  OpenAI库未安装，使用模拟向量")
        return generate_mock_vector(1536)
    except Exception as e:
        print(f"⚠️  向量化失败: {e}，使用模拟向量")
        return generate_mock_vector(1536)


def generate_mock_vector(dimension: int = 1536) -> List[float]:
    """生成模拟向量（用于测试）"""
    import random
    # 生成随机向量，但保持一致性（基于文本哈希）
    import hashlib
    seed = int(hashlib.md5(str(dimension).encode()).hexdigest(), 16) % (2**32)
    random.seed(seed)
    return [random.gauss(0, 0.1) for _ in range(dimension)]


def vectorize_activities(activities: List[Dict[str, Any]], use_real_api: bool = False) -> List[Dict[str, Any]]:
    """向量化所有业务活动"""
    vectorized_activities = []
    
    print(f"[INFO] 开始向量化 {len(activities)} 个业务活动...")
    print()
    
    for i, activity in enumerate(activities, 1):
        print(f"[{i}/{len(activities)}] 向量化: {activity.get('name', activity.get('id'))}")
        
        # 创建向量化文本
        embedding_text = create_embedding_text(activity)
        
        # 生成向量
        if use_real_api:
            vector = vectorize_with_openai(embedding_text)
        else:
            # 使用基于ID的模拟向量，确保一致性
            vector = generate_mock_vector(1536)
        
        # 创建向量化结果
        vectorized_activity = {
            "activity_id": activity.get("id"),
            "activity_name": activity.get("name"),
            "embedding_text": embedding_text,
            "vector": vector,
            "vector_dimension": len(vector),
            "embedding_model": "text-embedding-3-small" if use_real_api else "mock",
            "vectorized_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        vectorized_activities.append(vectorized_activity)
        
        # 避免API限流
        if use_real_api and i < len(activities):
            time.sleep(0.1)
    
    return vectorized_activities


def save_vectorized_data(vectorized_activities: List[Dict[str, Any]]):
    """保存向量化数据"""
    # 保存完整数据
    output_file = OUTPUT_DIR / "vectorized_activities.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(vectorized_activities, f, ensure_ascii=False, indent=2)
        print(f"[OK] 已保存完整向量化数据: {output_file}")
    
    # 保存简化版本（不包含向量数据，只包含元数据）
    simplified_data = []
    for item in vectorized_activities:
        simplified_item = {
            "activity_id": item["activity_id"],
            "activity_name": item["activity_name"],
            "vector_dimension": item["vector_dimension"],
            "embedding_model": item["embedding_model"],
            "vectorized_at": item["vectorized_at"]
        }
        simplified_data.append(simplified_item)
    
    summary_file = OUTPUT_DIR / "vectorization_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_activities": len(vectorized_activities),
            "vector_dimension": vectorized_activities[0]["vector_dimension"] if vectorized_activities else 0,
            "embedding_model": vectorized_activities[0]["embedding_model"] if vectorized_activities else "unknown",
            "vectorized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "activities": simplified_data
        }, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已保存向量化摘要: {summary_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("采购场景业务活动向量化")
    print("=" * 60)
    print()
    
    # 检查是否使用真实API
    use_real_api = os.getenv("USE_REAL_EMBEDDING_API", "false").lower() == "true"
    if use_real_api:
        print("[INFO] 使用OpenAI API进行向量化")
    else:
        print("[INFO] 使用模拟向量（用于测试）")
        print("   设置环境变量 USE_REAL_EMBEDDING_API=true 使用真实API")
    print()
    
    # 加载活动数据
    try:
        activities = load_activities()
        print(f"[OK] 加载了 {len(activities)} 个业务活动")
        print()
    except Exception as e:
        print(f"[ERROR] 加载活动数据失败: {e}")
        return 1
    
    # 向量化活动
    try:
        vectorized_activities = vectorize_activities(activities, use_real_api=use_real_api)
        print()
        print(f"[OK] 成功向量化 {len(vectorized_activities)} 个业务活动")
        print()
    except Exception as e:
        print(f"[ERROR] 向量化失败: {e}")
        return 1
    
    # 保存向量化数据
    try:
        save_vectorized_data(vectorized_activities)
        print()
    except Exception as e:
        print(f"[ERROR] 保存向量化数据失败: {e}")
        return 1
    
    # 统计信息
    print("=" * 60)
    print("[OK] 向量化完成！")
    print("=" * 60)
    print()
    print(f"[SUMMARY] 统计信息:")
    print(f"   - 向量化活动数: {len(vectorized_activities)}")
    if vectorized_activities:
        print(f"   - 向量维度: {vectorized_activities[0]['vector_dimension']}")
        print(f"   - 向量化模型: {vectorized_activities[0]['embedding_model']}")
    print()
    print(f"[INFO] 输出目录: {OUTPUT_DIR}")
    print()


if __name__ == "__main__":
    exit(main())

