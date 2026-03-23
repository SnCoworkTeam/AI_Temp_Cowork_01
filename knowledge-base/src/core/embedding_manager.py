"""
嵌入模型管理
负责文本向量化
"""
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# 尝试导入sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning(f"sentence-transformers not available: {str(e)}, using mock embeddings")
    logger.warning("To fix: pip install sentence-transformers torch transformers")

# 尝试导入OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EmbeddingManager:
    """嵌入模型管理器"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        """
        初始化嵌入管理器
        
        Args:
            model_name: 模型名称
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
            if SENTENCE_TRANSFORMERS_AVAILABLE and "sentence-transformers" in self.model_name:
                logger.info(f"Loading embedding model: {self.model_name}")
                # 配置HuggingFace镜像源（如果可用）
                import os
                hf_endpoint = os.getenv("HF_ENDPOINT", os.getenv("HUGGINGFACE_HUB_CACHE"))
                if hf_endpoint:
                    os.environ["HF_ENDPOINT"] = hf_endpoint
                    logger.info(f"Using HuggingFace endpoint: {hf_endpoint}")
                
                # 尝试加载模型，如果网络失败则使用mock
                try:
                    # 指定缓存目录，优先使用本地缓存
                    import os
                    cache_folder = os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
                    logger.info(f"Loading model with cache folder: {cache_folder}")
                    self.model = SentenceTransformer(self.model_name, device=self.device, cache_folder=cache_folder)
                    # 获取模型维度
                    test_embedding = self.model.encode(["test"])
                    self.dimension = len(test_embedding[0])
                    logger.info(f"Embedding model loaded successfully, dimension: {self.dimension}")
                except Exception as load_error:
                    logger.warning(f"Failed to load model: {str(load_error)}")
                    logger.warning("Using mock embedding model (fallback)")
                    self.model = None
                    self.dimension = 384
            else:
                logger.warning("Using mock embedding model")
                # 使用默认维度
                self.dimension = 384
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            logger.warning("Using mock embedding model")
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
                # Mock embeddings for development
                return self._generate_mock_embeddings(texts)
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            return self._generate_mock_embeddings(texts)
    
    def encode_single(self, text: str) -> List[float]:
        """
        编码单个文本
        
        Args:
            text: 文本
        
        Returns:
            向量
        """
        return self.encode([text])[0]
    
    def _generate_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        生成模拟嵌入向量（用于开发环境）
        
        Args:
            texts: 文本列表
        
        Returns:
            模拟向量列表
        """
        # 使用简单的哈希函数生成伪随机向量
        import hashlib
        embeddings = []
        for text in texts:
            # 使用文本的哈希值作为种子
            hash_obj = hashlib.md5(text.encode())
            seed = int(hash_obj.hexdigest(), 16) % (2**32)
            np.random.seed(seed)
            # 生成归一化的随机向量
            vector = np.random.normal(0, 1, self.dimension).tolist()
            # 归一化
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


# 全局嵌入管理器实例
_embedding_manager: Optional[EmbeddingManager] = None


def get_embedding_manager(model_name: str = None, device: str = None) -> EmbeddingManager:
    """
    获取嵌入管理器单例
    
    Args:
        model_name: 模型名称（可选，用于重新初始化）
        device: 设备（可选，用于重新初始化）
    
    Returns:
        嵌入管理器实例
    """
    global _embedding_manager
    
    if _embedding_manager is None:
        from ..config import settings
        _embedding_manager = EmbeddingManager(
            model_name=model_name or settings.EMBEDDING_MODEL,
            device=device or settings.EMBEDDING_DEVICE
        )
    elif model_name or device:
        # 如果提供了新参数，重新初始化
        _embedding_manager = EmbeddingManager(
            model_name=model_name or _embedding_manager.model_name,
            device=device or _embedding_manager.device
        )
    
    return _embedding_manager







