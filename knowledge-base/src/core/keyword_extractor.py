"""
关键词提取器
从文档中提取关键词和重要短语
"""
import logging
from typing import List, Dict, Any, Optional
import re
from collections import Counter

logger = logging.getLogger(__name__)

# 尝试导入NLP库
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
    # 尝试下载必需的NLTK数据
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except:
            pass
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except:
            pass
except ImportError:
    NLTK_AVAILABLE = False


class KeywordExtractor:
    """关键词提取器"""
    
    def __init__(self, language: str = "en", max_keywords: int = 10):
        """
        初始化关键词提取器
        
        Args:
            language: 语言代码（en, zh）
            max_keywords: 最大提取关键词数量
        """
        self.language = language
        self.max_keywords = max_keywords
        self._stopwords = self._load_stopwords()
    
    def _load_stopwords(self) -> set:
        """加载停用词"""
        stopwords_set = set()
        
        if self.language == "en" and NLTK_AVAILABLE:
            try:
                stopwords_set = set(stopwords.words('english'))
            except:
                pass
        
        # 添加常见停用词
        common_stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "this", "that", "these", "those", "it", "they", "we", "you", "he", "she"
        }
        stopwords_set.update(common_stopwords)
        
        return stopwords_set
    
    def extract(self, text: str, method: str = "tfidf") -> List[Dict[str, Any]]:
        """
        提取关键词
        
        Args:
            text: 文本内容
            method: 提取方法（tfidf, frequency, simple）
        
        Returns:
            关键词列表，每个关键词包含词、权重、位置等信息
        """
        if not text or len(text.strip()) < 10:
            return []
        
        text = text.strip()
        
        if method == "tfidf" and SKLEARN_AVAILABLE:
            return self._extract_tfidf(text)
        elif method == "frequency":
            return self._extract_frequency(text)
        else:
            return self._extract_simple(text)
    
    def _extract_tfidf(self, text: str) -> List[Dict[str, Any]]:
        """使用TF-IDF提取关键词"""
        try:
            # 分词
            words = self._tokenize(text)
            if len(words) < 3:
                return []
            
            # 使用TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=self.max_keywords * 2,
                stop_words=list(self._stopwords) if self._stopwords else None,
                ngram_range=(1, 2),  # 支持单字和双字短语
                min_df=1,
                max_df=0.8
            )
            
            # 将文本转换为TF-IDF向量
            tfidf_matrix = vectorizer.fit_transform([text])
            
            # 获取特征名称和权重
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # 创建关键词-权重对
            keywords = []
            for word, score in zip(feature_names, scores):
                if score > 0:
                    keywords.append({
                        "keyword": word,
                        "score": float(score),
                        "method": "tfidf"
                    })
            
            # 按权重排序并返回前N个
            keywords.sort(key=lambda x: x["score"], reverse=True)
            return keywords[:self.max_keywords]
            
        except Exception as e:
            logger.warning(f"TF-IDF extraction failed: {str(e)}, falling back to simple method")
            return self._extract_simple(text)
    
    def _extract_frequency(self, text: str) -> List[Dict[str, Any]]:
        """基于词频提取关键词"""
        words = self._tokenize(text)
        
        # 过滤停用词和短词
        filtered_words = [
            w.lower() for w in words
            if len(w) > 2 and w.lower() not in self._stopwords
        ]
        
        if not filtered_words:
            return []
        
        # 统计词频
        word_freq = Counter(filtered_words)
        
        # 计算总词数
        total_words = len(filtered_words)
        
        # 创建关键词列表
        keywords = []
        for word, count in word_freq.most_common(self.max_keywords):
            keywords.append({
                "keyword": word,
                "score": count / total_words,  # 归一化频率
                "frequency": count,
                "method": "frequency"
            })
        
        return keywords
    
    def _extract_simple(self, text: str) -> List[Dict[str, Any]]:
        """简单关键词提取（基于词频和长度）"""
        words = self._tokenize(text)
        
        # 过滤停用词和短词
        filtered_words = [
            w for w in words
            if len(w) > 3 and w.lower() not in self._stopwords
        ]
        
        if not filtered_words:
            return []
        
        # 统计词频
        word_freq = Counter(filtered_words)
        
        # 计算总词数
        total_words = len(filtered_words)
        
        # 创建关键词列表（按频率和长度加权）
        keywords = []
        for word, count in word_freq.most_common(self.max_keywords * 2):
            # 计算分数：频率 * 长度权重
            length_weight = min(len(word) / 10, 1.0)  # 长度权重，最长10个字符
            score = (count / total_words) * (1 + length_weight * 0.5)
            
            keywords.append({
                "keyword": word,
                "score": score,
                "frequency": count,
                "method": "simple"
            })
        
        # 按分数排序
        keywords.sort(key=lambda x: x["score"], reverse=True)
        return keywords[:self.max_keywords]
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        if self.language == "zh" and JIEBA_AVAILABLE:
            # 中文分词
            return list(jieba.cut(text))
        elif NLTK_AVAILABLE:
            # 英文分词
            try:
                return word_tokenize(text)
            except:
                pass
        
        # 简单分词（按空格和标点）
        words = re.findall(r'\b\w+\b', text)
        return words
    
    def extract_phrases(self, text: str, min_length: int = 2, max_length: int = 4) -> List[str]:
        """
        提取短语（n-gram）
        
        Args:
            text: 文本内容
            min_length: 最小短语长度
            max_length: 最大短语长度
        
        Returns:
            短语列表
        """
        words = self._tokenize(text)
        
        if len(words) < min_length:
            return []
        
        phrases = []
        for n in range(min_length, max_length + 1):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                # 过滤包含停用词的短语
                if not any(word.lower() in self._stopwords for word in words[i:i+n]):
                    phrases.append(phrase)
        
        # 统计短语频率
        phrase_freq = Counter(phrases)
        
        # 返回最常见的短语
        return [phrase for phrase, _ in phrase_freq.most_common(self.max_keywords)]


def get_keyword_extractor(language: str = "en", max_keywords: int = 10) -> KeywordExtractor:
    """获取关键词提取器实例"""
    return KeywordExtractor(language=language, max_keywords=max_keywords)









