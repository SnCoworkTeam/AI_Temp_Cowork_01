"""
向量数据迁移脚本：从PostgreSQL ARRAY迁移到Qdrant
迁移内容：
1. 质量规则向量（quality_rule_vectors）
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.src.core.database import get_database_manager, init_session_factory
from database.src.core.session import get_db

# 尝试从metadata-service导入，如果失败则从database导入
try:
    from metadata_service.src.models.quality_vector import QualityRuleVector
except ImportError:
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "metadata-service" / "src"))
        from models.quality_vector import QualityRuleVector
    except ImportError:
        # 如果都失败，使用数据库模型
        from database.src.models.metadata_models import QualityRuleVector
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VectorMigrator:
    """向量数据迁移器"""
    
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        """
        初始化迁移器
        
        Args:
            qdrant_url: Qdrant服务地址
        """
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = "quality_rule_vectors"
        self.vector_dimension = 384  # Sentence Transformers默认维度
        self.db = None
        self.stats = {
            "vectors_migrated": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """初始化连接"""
        # 初始化PostgreSQL
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            raise RuntimeError("PostgreSQL连接失败")
        init_session_factory()
        self.db = next(get_db())
        
        # 确保Qdrant集合存在
        self._ensure_collection()
        
        logger.info("数据库连接初始化成功")
    
    def _ensure_collection(self):
        """确保Qdrant集合存在"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"创建Qdrant集合: {self.collection_name}")
            else:
                logger.info(f"Qdrant集合已存在: {self.collection_name}")
        except Exception as e:
            logger.error(f"创建Qdrant集合失败: {e}", exc_info=True)
            raise
    
    async def migrate_quality_vectors(self, batch_size: int = 100):
        """
        迁移质量规则向量
        
        Args:
            batch_size: 批处理大小
        """
        logger.info("开始迁移质量规则向量...")
        
        try:
            vectors = self.db.query(QualityRuleVector).all()
            logger.info(f"找到 {len(vectors)} 个质量规则向量")
            
            points = []
            
            for i, vector_record in enumerate(vectors, 1):
                try:
                    # 构建Qdrant点
                    point = PointStruct(
                        id=vector_record.id,
                        vector=vector_record.vector,  # 已经是List[float]
                        payload={
                            "asset_id": vector_record.asset_id,
                            "rule_id": vector_record.rule_id,
                            "vector_dimension": vector_record.vector_dimension,
                            "metrics": vector_record.metrics,
                            "metrics_text": vector_record.metrics_text,
                            "rule_result": vector_record.rule_result,
                            "executed_at": vector_record.executed_at.isoformat() if vector_record.executed_at else None,
                            "source": "postgresql",
                            "migrated_at": datetime.now().isoformat()
                        }
                    )
                    points.append(point)
                    
                    # 批量上传
                    if len(points) >= batch_size:
                        self.qdrant_client.upsert(
                            collection_name=self.collection_name,
                            points=points
                        )
                        self.stats["vectors_migrated"] += len(points)
                        logger.info(f"已迁移 {self.stats['vectors_migrated']}/{len(vectors)} 个向量")
                        points = []
                
                except Exception as e:
                    logger.error(f"迁移向量失败 {vector_record.id}: {e}")
                    self.stats["errors"] += 1
            
            # 上传剩余的向量
            if points:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                self.stats["vectors_migrated"] += len(points)
            
            logger.info(f"质量规则向量迁移完成: {self.stats['vectors_migrated']} 个")
        
        except Exception as e:
            logger.error(f"迁移质量规则向量失败: {e}", exc_info=True)
            raise
    
    async def cleanup(self):
        """清理资源"""
        if self.db:
            self.db.close()
        logger.info("资源清理完成")
    
    async def run_migration(self):
        """运行完整迁移"""
        logger.info("=" * 80)
        logger.info("开始向量数据迁移到Qdrant")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            await self.initialize()
            await self.migrate_quality_vectors()
            
            # 打印统计
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info("迁移完成")
            logger.info("=" * 80)
            logger.info(f"迁移统计:")
            logger.info(f"  向量数: {self.stats['vectors_migrated']}")
            logger.info(f"  错误数: {self.stats['errors']}")
            logger.info(f"  耗时: {duration:.2f} 秒")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"迁移失败: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="迁移向量数据到Qdrant")
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default="http://localhost:6333",
        help="Qdrant服务地址"
    )
    
    args = parser.parse_args()
    
    migrator = VectorMigrator(qdrant_url=args.qdrant_url)
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())

