"""
多模态向量融合服务
实现不同的向量融合策略
"""
import logging
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


class VectorFusionService:
    """向量融合服务"""
    
    def __init__(self, strategy: str = "weighted_average", default_weights: Optional[Dict[str, float]] = None):
        """
        初始化向量融合服务
        
        Args:
            strategy: 融合策略（weighted_average, attention, concatenate）
            default_weights: 默认权重（用于weighted_average）
        """
        self.strategy = strategy
        self.default_weights = default_weights or {
            "metadata": 0.4,
            "knowledge": 0.4,
            "permission": 0.2
        }
    
    def fuse(
        self,
        vectors: Dict[str, List[float]],
        weights: Optional[Dict[str, float]] = None
    ) -> List[float]:
        """
        融合多个模态的向量
        
        Args:
            vectors: 向量字典，key为模态名称，value为向量
            weights: 权重字典（可选，如果不提供则使用默认权重）
        
        Returns:
            融合后的向量
        """
        if not vectors:
            raise ValueError("vectors cannot be empty")
        
        if self.strategy == "weighted_average":
            return self._weighted_average(vectors, weights)
        elif self.strategy == "concatenate":
            return self._concatenate(vectors)
        elif self.strategy == "attention":
            return self._attention_fusion(vectors, weights)
        else:
            raise ValueError(f"Unknown fusion strategy: {self.strategy}")
    
    def _weighted_average(
        self,
        vectors: Dict[str, List[float]],
        weights: Optional[Dict[str, float]] = None
    ) -> List[float]:
        """
        加权平均融合
        
        这是最简单的融合策略，适用于所有向量维度相同的情况
        """
        if weights is None:
            weights = self.default_weights
        
        # 确保所有权重和为1
        total_weight = sum(weights.get(modality, 0.0) for modality in vectors.keys())
        if total_weight == 0:
            # 如果权重为0，使用均匀权重
            weight_per_modality = 1.0 / len(vectors)
            weights = {modality: weight_per_modality for modality in vectors.keys()}
        else:
            # 归一化权重
            weights = {k: v / total_weight for k, v in weights.items() if k in vectors}
        
        # 检查所有向量维度是否相同
        dimensions = [len(v) for v in vectors.values()]
        if len(set(dimensions)) > 1:
            raise ValueError(f"Vectors have different dimensions: {dimensions}")
        
        dimension = dimensions[0]
        
        # 加权平均
        fused_vector = np.zeros(dimension)
        for modality, vector in vectors.items():
            weight = weights.get(modality, 0.0)
            fused_vector += np.array(vector) * weight
        
        # 归一化
        norm = np.linalg.norm(fused_vector)
        if norm > 0:
            fused_vector = fused_vector / norm
        
        return fused_vector.tolist()
    
    def _concatenate(self, vectors: Dict[str, List[float]]) -> List[float]:
        """
        拼接融合
        
        将所有向量拼接在一起，适用于需要保留所有信息的场景
        """
        concatenated = []
        for modality in sorted(vectors.keys()):  # 确保顺序一致
            concatenated.extend(vectors[modality])
        
        # 归一化
        concatenated_array = np.array(concatenated)
        norm = np.linalg.norm(concatenated_array)
        if norm > 0:
            concatenated_array = concatenated_array / norm
        
        return concatenated_array.tolist()
    
    def _attention_fusion(
        self,
        vectors: Dict[str, List[float]],
        weights: Optional[Dict[str, float]] = None
    ) -> List[float]:
        """
        注意力机制融合（简化版）
        
        这是一个简化的注意力机制，实际可以使用更复杂的注意力模型
        """
        # 简化版：使用权重作为注意力权重
        # 实际应用中可以使用学习到的注意力权重
        return self._weighted_average(vectors, weights)
    
    def get_fusion_info(self) -> dict:
        """获取融合策略信息"""
        return {
            "strategy": self.strategy,
            "default_weights": self.default_weights,
            "supported_strategies": ["weighted_average", "concatenate", "attention"]
        }







