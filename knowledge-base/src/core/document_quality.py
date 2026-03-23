"""
文档质量评估
支持质量评分、完整性检查、重复内容检测、相关性评分
"""
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """质量评分"""
    overall_score: float  # 0-100
    completeness_score: float  # 完整性评分
    readability_score: float  # 可读性评分
    relevance_score: float  # 相关性评分
    uniqueness_score: float  # 唯一性评分
    details: Dict[str, Any] = field(default_factory=dict)


class DocumentQualityAssessor:
    """文档质量评估器"""
    
    def __init__(self):
        self.content_hashes: Dict[str, str] = {}  # 存储内容哈希用于重复检测
    
    def assess_quality(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        knowledge_base_id: Optional[str] = None
    ) -> QualityScore:
        """
        评估文档质量
        
        Args:
            text: 文档文本
            metadata: 文档元数据
            knowledge_base_id: 知识库ID（用于相关性评估）
        
        Returns:
            质量评分
        """
        completeness = self._assess_completeness(text, metadata)
        readability = self._assess_readability(text)
        relevance = self._assess_relevance(text, knowledge_base_id) if knowledge_base_id else 0.5
        uniqueness = self._assess_uniqueness(text)
        
        # 加权平均
        overall = (
            completeness * 0.3 +
            readability * 0.3 +
            relevance * 0.2 +
            uniqueness * 0.2
        )
        
        return QualityScore(
            overall_score=round(overall * 100, 2),
            completeness_score=round(completeness * 100, 2),
            readability_score=round(readability * 100, 2),
            relevance_score=round(relevance * 100, 2),
            uniqueness_score=round(uniqueness * 100, 2),
            details={
                "text_length": len(text),
                "word_count": len(text.split()),
                "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
                "has_metadata": metadata is not None and len(metadata) > 0
            }
        )
    
    def _assess_completeness(self, text: str, metadata: Optional[Dict[str, Any]]) -> float:
        """评估完整性"""
        score = 0.0
        
        # 文本长度检查
        if len(text) > 100:
            score += 0.3
        elif len(text) > 50:
            score += 0.2
        else:
            score += 0.1
        
        # 段落检查
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 0.3
        elif len(paragraphs) >= 1:
            score += 0.2
        
        # 元数据检查
        if metadata:
            if metadata.get('title'):
                score += 0.2
            if metadata.get('author'):
                score += 0.1
            page_count = metadata.get('page_count')
            if page_count is not None and isinstance(page_count, (int, float)) and page_count > 0:
                score += 0.1
        
        return min(1.0, score)
    
    def _assess_readability(self, text: str) -> float:
        """评估可读性"""
        if not text:
            return 0.0
        
        score = 0.0
        
        # 句子数量
        sentences = [s for s in text.split('.') if s.strip()]
        if len(sentences) >= 5:
            score += 0.3
        elif len(sentences) >= 2:
            score += 0.2
        
        # 平均句子长度（适中的长度更好）
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 10 <= avg_sentence_length <= 25:
                score += 0.4
            elif 5 <= avg_sentence_length <= 35:
                score += 0.3
            else:
                score += 0.1
        
        # 特殊字符比例（过多特殊字符降低可读性）
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(text) if text else 0
        if special_ratio < 0.1:
            score += 0.3
        elif special_ratio < 0.2:
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_relevance(self, text: str, knowledge_base_id: str) -> float:
        """评估相关性（简化实现，实际应该使用向量相似度）"""
        # TODO: 实现基于向量相似度的相关性评估
        # 这里返回默认值
        return 0.5
    
    def _assess_uniqueness(self, text: str) -> float:
        """评估唯一性（检测重复内容）"""
        # 计算内容哈希
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # 检查是否重复
        if content_hash in self.content_hashes.values():
            return 0.0  # 完全重复
        
        # 检查相似度（简化实现）
        similarity = self._calculate_similarity(text)
        uniqueness = 1.0 - similarity
        
        return max(0.0, uniqueness)
    
    def _calculate_similarity(self, text: str) -> float:
        """计算与已有内容的相似度（简化实现）"""
        # TODO: 实现更精确的相似度计算（如使用TF-IDF或向量相似度）
        # 这里返回默认值
        return 0.0
    
    def check_completeness(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """检查文档完整性"""
        issues = []
        warnings = []
        
        # 检查文本长度
        if len(text) < 50:
            issues.append("文档内容过短（少于50字符）")
        elif len(text) < 100:
            warnings.append("文档内容较短（少于100字符）")
        
        # 检查段落
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        if len(paragraphs) == 0:
            issues.append("文档没有段落结构")
        elif len(paragraphs) < 2:
            warnings.append("文档段落较少")
        
        # 检查元数据
        if not metadata:
            warnings.append("缺少文档元数据")
        else:
            if not metadata.get('title'):
                warnings.append("缺少文档标题")
            if not metadata.get('author'):
                warnings.append("缺少作者信息")
        
        return {
            "is_complete": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": 1.0 - (len(issues) * 0.3 + len(warnings) * 0.1)
        }
    
    def detect_duplicates(
        self,
        text: str,
        threshold: float = 0.9
    ) -> List[Tuple[str, float]]:
        """
        检测重复内容
        
        Args:
            text: 文档文本
            threshold: 相似度阈值
        
        Returns:
            重复文档ID和相似度列表
        """
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        duplicates = []
        
        # 检查完全重复
        for doc_id, hash_value in self.content_hashes.items():
            if hash_value == content_hash:
                duplicates.append((doc_id, 1.0))
        
        # TODO: 实现基于相似度的重复检测
        # 可以使用TF-IDF或向量相似度
        
        return duplicates
    
    def register_document(self, document_id: str, text: str):
        """注册文档（用于重复检测）"""
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        self.content_hashes[document_id] = content_hash


# 全局质量评估器实例
_quality_assessor: Optional[DocumentQualityAssessor] = None


def get_quality_assessor() -> DocumentQualityAssessor:
    """获取质量评估器单例"""
    global _quality_assessor
    if _quality_assessor is None:
        _quality_assessor = DocumentQualityAssessor()
    return _quality_assessor


