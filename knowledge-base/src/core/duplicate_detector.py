"""
重复文档检测器
检测知识库中的重复或相似文档
"""
import logging
from typing import List, Dict, Any, Optional
from .embedding_manager import get_embedding_manager

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """重复文档检测器"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        初始化重复文档检测器
        
        Args:
            similarity_threshold: 相似度阈值（0-1），超过此值视为重复
        """
        self.similarity_threshold = similarity_threshold
        self.embedding_manager = None
    
    def _get_embedding_manager(self):
        """延迟加载嵌入管理器"""
        if self.embedding_manager is None:
            try:
                self.embedding_manager = get_embedding_manager()
            except Exception as e:
                logger.warning(f"Failed to load embedding manager: {str(e)}")
        return self.embedding_manager
    
    def detect_duplicates(
        self,
        documents: List[Dict[str, Any]],
        method: str = "embedding"
    ) -> List[Dict[str, Any]]:
        """
        检测重复文档
        
        Args:
            documents: 文档列表，每个文档包含id、content等字段
            method: 检测方法（embedding, hash, content）
        
        Returns:
            重复文档组列表，每个组包含相似文档的信息
        """
        if len(documents) < 2:
            return []
        
        if method == "embedding":
            return self._detect_by_embedding(documents)
        elif method == "hash":
            return self._detect_by_hash(documents)
        else:
            return self._detect_by_content(documents)
    
    def _detect_by_embedding(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于嵌入向量的重复检测"""
        embedding_manager = self._get_embedding_manager()
        
        if embedding_manager is None:
            logger.warning("Embedding manager not available, falling back to content-based detection")
            return self._detect_by_content(documents)
        
        try:
            # 生成所有文档的嵌入向量
            embeddings = {}
            for doc in documents:
                content = doc.get("content", "")
                if content:
                    # 限制内容长度以提高性能
                    content_sample = content[:5000] if len(content) > 5000 else content
                    embedding = embedding_manager.embed_text(content_sample)
                    embeddings[doc["id"]] = embedding
            
            # 计算相似度矩阵
            duplicate_groups = []
            processed = set()
            
            doc_ids = list(embeddings.keys())
            for i, doc_id1 in enumerate(doc_ids):
                if doc_id1 in processed:
                    continue
                
                group = [doc_id1]
                doc1_embedding = embeddings[doc_id1]
                
                for doc_id2 in doc_ids[i+1:]:
                    if doc_id2 in processed:
                        continue
                    
                    doc2_embedding = embeddings[doc_id2]
                    similarity = self._cosine_similarity(doc1_embedding, doc2_embedding)
                    
                    if similarity >= self.similarity_threshold:
                        group.append(doc_id2)
                        processed.add(doc_id2)
                
                if len(group) > 1:
                    duplicate_groups.append({
                        "documents": group,
                        "similarity": similarity,
                        "method": "embedding"
                    })
                    processed.add(doc_id1)
            
            return duplicate_groups
        
        except Exception as e:
            logger.error(f"Embedding-based duplicate detection failed: {str(e)}")
            return self._detect_by_content(documents)
    
    def _detect_by_hash(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于内容哈希的重复检测"""
        import hashlib
        
        # 计算每个文档的哈希值
        doc_hashes = {}
        for doc in documents:
            content = doc.get("content", "")
            if content:
                # 标准化内容（去除空白）
                normalized = " ".join(content.split())
                content_hash = hashlib.md5(normalized.encode()).hexdigest()
                
                if content_hash not in doc_hashes:
                    doc_hashes[content_hash] = []
                doc_hashes[content_hash].append(doc["id"])
        
        # 找出重复的哈希值
        duplicate_groups = []
        for content_hash, doc_ids in doc_hashes.items():
            if len(doc_ids) > 1:
                duplicate_groups.append({
                    "documents": doc_ids,
                    "similarity": 1.0,  # 完全相同的哈希意味着完全相同的内容
                    "method": "hash"
                })
        
        return duplicate_groups
    
    def _detect_by_content(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于内容相似度的重复检测"""
        duplicate_groups = []
        processed = set()
        
        for i, doc1 in enumerate(documents):
            if doc1["id"] in processed:
                continue
            
            content1 = doc1.get("content", "")
            if not content1:
                continue
            
            group = [doc1["id"]]
            
            for doc2 in documents[i+1:]:
                if doc2["id"] in processed:
                    continue
                
                content2 = doc2.get("content", "")
                if not content2:
                    continue
                
                similarity = self._content_similarity(content1, content2)
                
                if similarity >= self.similarity_threshold:
                    group.append(doc2["id"])
                    processed.add(doc2["id"])
            
            if len(group) > 1:
                duplicate_groups.append({
                    "documents": group,
                    "similarity": similarity,
                    "method": "content"
                })
                processed.add(doc1["id"])
        
        return duplicate_groups
    
    def _content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度（基于Jaccard相似度）"""
        # 转换为词集合
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if len(words1) == 0 or len(words2) == 0:
            return 0.0
        
        # Jaccard相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
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
    
    def find_similar(
        self,
        target_document: Dict[str, Any],
        candidate_documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找与目标文档相似的文档
        
        Args:
            target_document: 目标文档
            candidate_documents: 候选文档列表
            top_k: 返回前k个相似文档
        
        Returns:
            相似文档列表，按相似度排序
        """
        if not candidate_documents:
            return []
        
        similarity_scores = []
        
        target_content = target_document.get("content", "")
        if not target_content:
            return []
        
        embedding_manager = self._get_embedding_manager()
        
        if embedding_manager:
            # 使用嵌入向量
            try:
                target_embedding = embedding_manager.embed_text(target_content[:5000])
                
                for candidate in candidate_documents:
                    candidate_content = candidate.get("content", "")
                    if candidate_content:
                        candidate_embedding = embedding_manager.embed_text(candidate_content[:5000])
                        similarity = self._cosine_similarity(target_embedding, candidate_embedding)
                        
                        similarity_scores.append({
                            "document_id": candidate["id"],
                            "similarity": similarity,
                            "method": "embedding"
                        })
            except Exception as e:
                logger.warning(f"Embedding-based similarity failed: {str(e)}")
                # 降级到内容相似度
                embedding_manager = None
        
        if not embedding_manager:
            # 使用内容相似度
            for candidate in candidate_documents:
                candidate_content = candidate.get("content", "")
                if candidate_content:
                    similarity = self._content_similarity(target_content, candidate_content)
                    
                    similarity_scores.append({
                        "document_id": candidate["id"],
                        "similarity": similarity,
                        "method": "content"
                    })
        
        # 按相似度排序并返回top-k
        similarity_scores.sort(key=lambda x: x["similarity"], reverse=True)
        return similarity_scores[:top_k]


def get_duplicate_detector(similarity_threshold: float = 0.95) -> DuplicateDetector:
    """获取重复文档检测器实例"""
    return DuplicateDetector(similarity_threshold=similarity_threshold)

