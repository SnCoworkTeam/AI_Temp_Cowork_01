"""
相关性评估器
评估文档与查询的相关性
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from .keyword_extractor import KeywordExtractor
from .embedding_manager import get_embedding_manager

logger = logging.getLogger(__name__)


class RelevanceEvaluator:
    """相关性评估器"""
    
    def __init__(self):
        """初始化相关性评估器"""
        self.keyword_extractor = KeywordExtractor(max_keywords=20)
        self.embedding_manager = None
    
    def _get_embedding_manager(self):
        """延迟加载嵌入管理器"""
        if self.embedding_manager is None:
            try:
                self.embedding_manager = get_embedding_manager()
            except Exception as e:
                logger.warning(f"Failed to load embedding manager: {str(e)}")
        return self.embedding_manager
    
    def evaluate(
        self,
        query: str,
        document_content: str,
        document_keywords: Optional[List[str]] = None,
        use_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        评估文档与查询的相关性
        
        Args:
            query: 查询文本
            document_content: 文档内容
            document_keywords: 文档关键词（可选）
            use_embedding: 是否使用嵌入向量（默认True）
        
        Returns:
            相关性评估结果，包含相关性分数、匹配关键词、匹配类型等
        """
        if not query or not document_content:
            return {
                "relevance_score": 0.0,
                "method": "insufficient_input",
                "matched_keywords": [],
                "match_types": {}
            }
        
        query_lower = query.lower()
        doc_lower = document_content.lower()
        
        # 1. 关键词匹配
        keyword_score, matched_keywords = self._keyword_match(query_lower, doc_lower, document_keywords)
        
        # 2. 短语匹配
        phrase_score, matched_phrases = self._phrase_match(query_lower, doc_lower)
        
        # 3. 语义相似度（如果可用）
        semantic_score = 0.0
        if use_embedding:
            semantic_score = self._semantic_similarity(query, document_content)
        
        # 4. 综合分数（加权平均）
        weights = {
            "keyword": 0.3,
            "phrase": 0.2,
            "semantic": 0.5
        }
        
        # 如果语义相似度不可用，调整权重
        if semantic_score == 0.0:
            total_weight = weights["keyword"] + weights["phrase"]
            weights = {
                "keyword": weights["keyword"] / total_weight,
                "phrase": weights["phrase"] / total_weight,
                "semantic": 0.0
            }
        
        relevance_score = (
            keyword_score * weights["keyword"] +
            phrase_score * weights["phrase"] +
            semantic_score * weights["semantic"]
        )
        
        return {
            "relevance_score": round(relevance_score, 3),
            "keyword_score": round(keyword_score, 3),
            "phrase_score": round(phrase_score, 3),
            "semantic_score": round(semantic_score, 3),
            "matched_keywords": matched_keywords,
            "matched_phrases": matched_phrases,
            "method": "hybrid",
            "weights": weights
        }
    
    def _keyword_match(
        self,
        query: str,
        doc_content: str,
        document_keywords: Optional[List[str]] = None
    ) -> Tuple[float, List[str]]:
        """关键词匹配"""
        # 提取查询关键词
        query_keywords = self.keyword_extractor.extract(query, method="simple")
        query_keyword_list = [kw["keyword"].lower() for kw in query_keywords]
        
        # 如果没有提供文档关键词，从文档内容提取
        if document_keywords is None:
            doc_keywords = self.keyword_extractor.extract(doc_content, method="simple")
            doc_keyword_list = [kw["keyword"].lower() for kw in doc_keywords]
        else:
            doc_keyword_list = [kw.lower() for kw in document_keywords]
        
        # 计算匹配
        matched = []
        for qkw in query_keyword_list:
            if qkw in doc_keyword_list:
                matched.append(qkw)
            elif qkw in doc_content:
                matched.append(qkw)
        
        # 计算分数
        if len(query_keyword_list) == 0:
            return 0.0, []
        
        score = len(matched) / len(query_keyword_list)
        return min(score, 1.0), matched
    
    def _phrase_match(self, query: str, doc_content: str) -> Tuple[float, List[str]]:
        """短语匹配"""
        # 提取查询短语（2-3词）
        query_words = query.split()
        if len(query_words) < 2:
            return 0.0, []
        
        matched_phrases = []
        
        # 检查2-gram和3-gram
        for n in [2, 3]:
            if len(query_words) < n:
                continue
            
            for i in range(len(query_words) - n + 1):
                phrase = " ".join(query_words[i:i+n])
                if phrase in doc_content:
                    matched_phrases.append(phrase)
        
        # 计算分数
        if len(query_words) < 2:
            return 0.0, []
        
        max_phrases = len(query_words) - 1  # 可能的短语数
        score = len(set(matched_phrases)) / max_phrases if max_phrases > 0 else 0.0
        
        return min(score, 1.0), list(set(matched_phrases))
    
    def _semantic_similarity(self, query: str, document_content: str) -> float:
        """语义相似度（使用嵌入向量）"""
        embedding_manager = self._get_embedding_manager()
        
        if embedding_manager is None:
            return 0.0
        
        try:
            # 生成嵌入向量
            query_embedding = embedding_manager.embed_text(query)
            doc_embedding = embedding_manager.embed_text(document_content[:5000])  # 限制长度
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            return max(0.0, similarity)
        
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {str(e)}")
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


def get_relevance_evaluator() -> RelevanceEvaluator:
    """获取相关性评估器实例"""
    return RelevanceEvaluator()

