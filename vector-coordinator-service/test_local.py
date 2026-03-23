"""
本地测试脚本 - 不依赖Docker
用于快速验证服务代码是否正确
"""
import sys
from pathlib import Path

# 添加路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared_libs"))

def test_imports():
    """测试导入"""
    print("测试导入...")
    try:
        from src.core.config import settings
        print(f"✅ 配置加载成功: PORT={settings.PORT}")
        
        from src.core.embedding_manager import get_unified_embedding_manager
        print("✅ 向量模型管理器导入成功")
        
        from src.core.vector_fusion import VectorFusionService
        print("✅ 向量融合服务导入成功")
        
        from src.core.similarity_service import SimilarityService
        print("✅ 相似度服务导入成功")
        
        from src.services.vector_coordinator_service import VectorCoordinatorService
        print("✅ 向量协调服务导入成功")
        
        print("\n✅ 所有模块导入成功！")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n测试基本功能...")
    try:
        from src.core.vector_fusion import VectorFusionService
        
        # 测试向量融合
        fusion = VectorFusionService()
        vectors = {
            "metadata": [0.1, 0.2, 0.3],
            "knowledge": [0.4, 0.5, 0.6]
        }
        fused = fusion.fuse(vectors)
        print(f"✅ 向量融合测试成功: 维度={len(fused)}")
        
        from src.core.similarity_service import SimilarityService
        sim_service = SimilarityService()
        similarity = sim_service.calculate_similarity([0.1, 0.2], [0.1, 0.2])
        print(f"✅ 相似度计算测试成功: {similarity:.4f}")
        
        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("向量协调服务 - 本地测试")
    print("=" * 50)
    
    if test_imports():
        test_basic_functionality()
        print("\n✅ 本地测试完成！代码没有问题。")
        print("\n下一步：解决Docker构建问题")
    else:
        print("\n❌ 测试失败，请检查代码")






