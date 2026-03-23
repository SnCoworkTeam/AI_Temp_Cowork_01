"""
元数据增强
支持自动摘要、关键词提取、实体识别、情感分析
"""
import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import Counter

logger = logging.getLogger(__name__)

# 尝试导入NLP库
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    NLTK_AVAILABLE = True
    # 下载必要的NLTK数据
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available, some features disabled")


@dataclass
class EnhancedMetadata:
    """增强的元数据"""
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    sentiment: Optional[Dict[str, float]] = None
    topics: List[str] = field(default_factory=list)


class MetadataEnhancer:
    """元数据增强器"""
    
    def __init__(self):
        self.stop_words = set()
        if NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                pass
    
    def enhance(
        self,
        text: str,
        generate_summary: bool = True,
        extract_keywords: bool = True,
        identify_entities: bool = True,
        analyze_sentiment: bool = True
    ) -> EnhancedMetadata:
        """
        增强元数据
        
        Args:
            text: 文档文本
            generate_summary: 是否生成摘要
            extract_keywords: 是否提取关键词
            identify_entities: 是否识别实体
            analyze_sentiment: 是否分析情感
        
        Returns:
            增强的元数据
        """
        enhanced = EnhancedMetadata()
        
        if generate_summary:
            enhanced.summary = self._generate_summary(text)
        
        if extract_keywords:
            enhanced.keywords = self._extract_keywords(text)
        
        if identify_entities:
            enhanced.entities = self._identify_entities(text)
        
        if analyze_sentiment:
            enhanced.sentiment = self._analyze_sentiment(text)
        
        return enhanced
    
    def _generate_summary(self, text: str, max_sentences: int = 3) -> Optional[str]:
        """生成文档摘要（简化实现：提取前几句）"""
        if not text:
            return None
        
        # 简单的摘要：提取前几个句子
        if NLTK_AVAILABLE:
            try:
                sentences = sent_tokenize(text)
                summary_sentences = sentences[:max_sentences]
                return ' '.join(summary_sentences)
            except:
                pass
        
        # 回退方案：按句号分割
        sentences = re.split(r'[.!?]+', text)
        summary_sentences = [s.strip() for s in sentences[:max_sentences] if s.strip()]
        return '. '.join(summary_sentences) + '.' if summary_sentences else None
    
    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        if NLTK_AVAILABLE:
            try:
                # 分词
                words = word_tokenize(text.lower())
                # 过滤停用词和标点
                words = [w for w in words if w.isalnum() and w not in self.stop_words and len(w) > 2]
                # 计算词频
                word_freq = Counter(words)
                # 返回最常见的词
                return [word for word, _ in word_freq.most_common(top_k)]
            except Exception as e:
                logger.warning(f"Failed to extract keywords with NLTK: {str(e)}")
        
        # 回退方案：简单的词频统计
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(top_k)]
    
    def _identify_entities(self, text: str) -> List[Dict[str, Any]]:
        """识别实体（简化实现）"""
        entities = []
        
        # 识别邮箱
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({
                "type": "email",
                "value": email,
                "start": text.find(email),
                "end": text.find(email) + len(email)
            })
        
        # 识别URL
        urls = re.findall(r'https?://[^\s]+', text)
        for url in urls:
            entities.append({
                "type": "url",
                "value": url,
                "start": text.find(url),
                "end": text.find(url) + len(url)
            })
        
        # 识别大写单词（可能是专有名词）
        capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', text)
        for word in set(capitalized_words[:20]):  # 限制数量
            if word not in ['The', 'This', 'That', 'These', 'Those']:
                entities.append({
                    "type": "proper_noun",
                    "value": word,
                    "start": text.find(word),
                    "end": text.find(word) + len(word)
                })
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Optional[Dict[str, float]]:
        """分析情感（简化实现）"""
        if not text:
            return None
        
        # 简单的情感分析：基于正面和负面词汇
        positive_words = ['good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic', 'love', 'like']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'poor', 'worst']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return {"positive": 0.5, "negative": 0.5, "neutral": 1.0}
        
        positive_score = positive_count / total
        negative_score = negative_count / total
        neutral_score = 1.0 - abs(positive_score - negative_score)
        
        return {
            "positive": round(positive_score, 3),
            "negative": round(negative_score, 3),
            "neutral": round(neutral_score, 3)
        }


# 全局元数据增强器实例
_metadata_enhancer: Optional[MetadataEnhancer] = None


def get_metadata_enhancer() -> MetadataEnhancer:
    """获取元数据增强器单例"""
    global _metadata_enhancer
    if _metadata_enhancer is None:
        _metadata_enhancer = MetadataEnhancer()
    return _metadata_enhancer


