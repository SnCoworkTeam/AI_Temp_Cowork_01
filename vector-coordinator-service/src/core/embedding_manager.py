"""
统一向量模型管理器
确保所有服务使用相同的模型和版本
"""
import logging
from typing import List, Optional
import numpy as np
import os

# 在导入前设置 Hugging Face 镜像源
if not os.environ.get("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

logger = logging.getLogger(__name__)

# 尝试导入sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning(f"sentence-transformers not available: {str(e)}")
    logger.warning("To fix: pip install sentence-transformers torch transformers")


class UnifiedEmbeddingManager:
    """统一向量模型管理器"""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        """
        初始化统一向量模型管理器
        
        Args:
            model_name: 模型名称（默认：all-MiniLM-L6-v2，384维）
            device: 设备（cpu/cuda）
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.dimension = None
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化模型"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # 确保使用国内镜像源
                if os.environ.get("HF_ENDPOINT"):
                    logger.info(f"Using HuggingFace endpoint: {os.environ.get('HF_ENDPOINT')}")
                else:
                    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                    logger.info("Using HuggingFace mirror: https://hf-mirror.com")
                
                logger.info(f"Loading unified embedding model: {self.model_name}")
                # 尝试加载模型
                self.model = SentenceTransformer(
                    self.model_name, 
                    device=self.device
                )
                # 获取模型维度
                test_embedding = self.model.encode(["test"])
                self.dimension = len(test_embedding[0])
                logger.info(f"Unified embedding model loaded, dimension: {self.dimension}")
            else:
                logger.warning("sentence-transformers not available, using mock embeddings")
                self.dimension = 384
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)[:200]}")
            logger.warning("Using mock embedding model (service will still work)")
            self.model = None
            self.dimension = 384
    
    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        编码文本为向量
        
        Args:
            texts: 文本列表
            batch_size: 批次大小
        
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        try:
            if self.model:
                embeddings = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
                return embeddings.tolist()
            else:
                return self._generate_mock_embeddings(texts)
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            return self._generate_mock_embeddings(texts)
    
    def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        return self.encode([text])[0]
    
    def _generate_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成模拟嵌入向量（用于开发环境）"""
        import hashlib
        embeddings = []
        for text in texts:
            hash_obj = hashlib.md5(text.encode())
            seed = int(hash_obj.hexdigest(), 16) % (2**32)
            np.random.seed(seed)
            vector = np.random.normal(0, 1, self.dimension).tolist()
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = (np.array(vector) / norm).tolist()
            embeddings.append(vector)
        return embeddings
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension or 384
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self.model is not None
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "device": self.device,
            "available": self.is_available()
        }


# 全局统一向量模型管理器实例
_unified_embedding_manager: Optional[UnifiedEmbeddingManager] = None


def get_unified_embedding_manager(
    model_name: str = None,
    device: str = None
) -> UnifiedEmbeddingManager:
    """
    获取统一向量模型管理器单例
    
    Args:
        model_name: 模型名称（可选）
        device: 设备（可选）
    
    Returns:
        统一向量模型管理器实例
    """
    global _unified_embedding_manager
    
    if _unified_embedding_manager is None:
        from ..core.config import settings
        _unified_embedding_manager = UnifiedEmbeddingManager(
            model_name=model_name or settings.EMBEDDING_MODEL,
            device=device or settings.EMBEDDING_DEVICE
        )
    elif model_name or device:
        _unified_embedding_manager = UnifiedEmbeddingManager(
            model_name=model_name or _unified_embedding_manager.model_name,
            device=device or _unified_embedding_manager.device
        )
    
    return _unified_embedding_manager

