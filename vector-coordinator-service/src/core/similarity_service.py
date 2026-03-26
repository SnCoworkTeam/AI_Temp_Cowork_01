"""
向量相似度服务
提供向量相似度计算和搜索功能
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class SimilarityService:
    """向量相似度服务"""
    
    def __init__(self, metric: str = "cosine"):
        """
        初始化相似度服务
        
        Args:
            metric: 相似度度量（cosine, euclidean, dot）
        """
        self.metric = metric
    
    def calculate_similarity(
        self,
        vector1: List[float],
        vector2: List[float]
    ) -> float:
        """
        计算两个向量的相似度
        
        Args:
            vector1: 向量1
            vector2: 向量2
        
        Returns:
            相似度分数（0-1）
        """
        if len(vector1) != len(vector2):
            raise ValueError(f"Vectors have different dimensions: {len(vector1)} vs {len(vector2)}")
        
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        if self.metric == "cosine":
            # 余弦相似度
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            similarity = dot_product / (norm1 * norm2)
            # 归一化到0-1（余弦相似度范围是-1到1）
            return (similarity + 1) / 2
        
        elif self.metric == "euclidean":
            # 欧氏距离（转换为相似度）
            distance = np.linalg.norm(v1 - v2)
            # 使用指数函数转换为相似度（距离越小，相似度越高）
            similarity = np.exp(-distance)
            return float(similarity)
        
        elif self.metric == "dot":
            # 点积（需要归一化向量）
            v1_norm = v1 / np.linalg.norm(v1) if np.linalg.norm(v1) > 0 else v1
            v2_norm = v2 / np.linalg.norm(v2) if np.linalg.norm(v2) > 0 else v2
            dot_product = np.dot(v1_norm, v2_norm)
            # 归一化到0-1
            return (dot_product + 1) / 2
        
        else:
            raise ValueError(f"Unknown similarity metric: {self.metric}")
    
    def find_similar(
        self,
        query_vector: List[float],
        candidate_vectors: List[Dict[str, Any]],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        查找相似向量
        
        Args:
            query_vector: 查询向量
            candidate_vectors: 候选向量列表，每个元素包含vector和metadata
            limit: 返回数量限制
            threshold: 相似度阈值
        
        Returns:
            相似向量列表，按相似度排序
        """
        results = []
        
        for candidate in candidate_vectors:
            vector = candidate.get("vector")
            if not vector:
                continue
            
            similarity = self.calculate_similarity(query_vector, vector)
            
            if similarity >= threshold:
                result = {
                    "similarity": float(similarity),
                    "metadata": candidate.get("metadata", {}),
                    "entity_uri": candidate.get("entity_uri"),
                    "modality": candidate.get("modality")
                }
                results.append(result)
        
        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # 返回top-k
        return results[:limit]
    
    def get_metric_info(self) -> dict:
        """获取相似度度量信息"""
        return {
            "metric": self.metric,
            "supported_metrics": ["cosine", "euclidean", "dot"]
        }







