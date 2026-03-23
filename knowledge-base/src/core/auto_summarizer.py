"""
自动摘要生成器
为文档生成摘要
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class AutoSummarizer:
    """自动摘要生成器"""
    
    def __init__(self, max_summary_length: int = 200):
        """
        初始化自动摘要生成器
        
        Args:
            max_summary_length: 最大摘要长度（字符数）
        """
        self.max_summary_length = max_summary_length
    
    def summarize(
        self,
        content: str,
        method: str = "extractive",
        summary_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成文档摘要
        
        Args:
            content: 文档内容
            method: 摘要方法（extractive, abstractive, first_sentences）
            summary_length: 摘要长度（字符数），如果为None则使用默认值
        
        Returns:
            摘要结果，包含摘要文本、长度、方法等信息
        """
        if not content or len(content.strip()) < 50:
            return {
                "summary": content[:self.max_summary_length] if content else "",
                "length": len(content) if content else 0,
                "method": "truncated",
                "original_length": len(content) if content else 0
            }
        
        if summary_length is None:
            summary_length = self.max_summary_length
        
        if method == "extractive":
            return self._extractive_summary(content, summary_length)
        elif method == "first_sentences":
            return self._first_sentences_summary(content, summary_length)
        else:
            return self._simple_summary(content, summary_length)
    
    def _extractive_summary(self, content: str, max_length: int) -> Dict[str, Any]:
        """抽取式摘要（基于句子重要性）"""
        import re
        
        # 分割句子
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return self._simple_summary(content, max_length)
        
        # 计算句子分数（基于位置、长度、关键词）
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            score = 0.0
            
            # 位置权重（开头和结尾的句子更重要）
            if i < len(sentences) * 0.1:  # 前10%
                score += 0.3
            elif i > len(sentences) * 0.9:  # 后10%
                score += 0.2
            
            # 长度权重（中等长度的句子更好）
            length = len(sentence)
            if 20 <= length <= 150:
                score += 0.2
            elif length > 150:
                score -= 0.1
            
            # 关键词权重（包含重要词的句子更重要）
            important_words = ["总结", "结论", "要点", "主要", "关键", "重要", 
                             "summary", "conclusion", "key", "important", "main"]
            for word in important_words:
                if word.lower() in sentence.lower():
                    score += 0.3
                    break
            
            sentence_scores.append((sentence, score, i))
        
        # 按分数排序
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 选择句子直到达到最大长度
        selected_sentences = []
        total_length = 0
        selected_indices = set()
        
        for sentence, score, original_index in sentence_scores:
            if total_length + len(sentence) <= max_length:
                selected_sentences.append((sentence, original_index))
                selected_indices.add(original_index)
                total_length += len(sentence) + 1  # +1 for space
            else:
                break
        
        # 按原始顺序排列
        selected_sentences.sort(key=lambda x: x[1])
        summary = " ".join(s[0] for s in selected_sentences)
        
        # 如果摘要太短，补充前几个句子
        if len(summary) < max_length * 0.5:
            remaining_length = max_length - len(summary)
            for i, sentence in enumerate(sentences):
                if i not in selected_indices and len(sentence) <= remaining_length:
                    summary = sentence + ". " + summary
                    remaining_length -= len(sentence)
                    if remaining_length <= 0:
                        break
        
        return {
            "summary": summary[:max_length],
            "length": len(summary),
            "method": "extractive",
            "original_length": len(content),
            "compression_ratio": len(summary) / len(content) if content else 0
        }
    
    def _first_sentences_summary(self, content: str, max_length: int) -> Dict[str, Any]:
        """基于前几个句子的摘要"""
        import re
        
        # 分割句子
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return self._simple_summary(content, max_length)
        
        # 选择前几个句子
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) <= max_length:
                summary += sentence + ". "
            else:
                break
        
        return {
            "summary": summary.strip()[:max_length],
            "length": len(summary),
            "method": "first_sentences",
            "original_length": len(content),
            "compression_ratio": len(summary) / len(content) if content else 0
        }
    
    def _simple_summary(self, content: str, max_length: int) -> Dict[str, Any]:
        """简单摘要（截取前N个字符）"""
        summary = content[:max_length]
        
        # 尝试在句子边界截断
        if len(content) > max_length:
            last_period = summary.rfind('.')
            last_exclamation = summary.rfind('!')
            last_question = summary.rfind('?')
            
            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > max_length * 0.7:  # 如果句子结束在合理位置
                summary = summary[:last_sentence_end + 1]
            else:
                summary = summary + "..."
        
        return {
            "summary": summary,
            "length": len(summary),
            "method": "simple",
            "original_length": len(content),
            "compression_ratio": len(summary) / len(content) if content else 0
        }
    
    def summarize_chunks(
        self,
        chunks: List[Dict[str, Any]],
        max_chunks: int = 3
    ) -> str:
        """
        为文档块生成摘要
        
        Args:
            chunks: 文档块列表
            max_chunks: 用于摘要的最大块数
        
        Returns:
            摘要文本
        """
        if not chunks:
            return ""
        
        # 选择前几个块
        selected_chunks = chunks[:max_chunks]
        
        # 提取每个块的内容
        chunk_contents = [chunk.get("content", "") for chunk in selected_chunks]
        
        # 合并并生成摘要
        combined_content = " ".join(chunk_contents)
        result = self.summarize(combined_content, method="extractive")
        
        return result["summary"]


def get_auto_summarizer(max_summary_length: int = 200) -> AutoSummarizer:
    """获取自动摘要生成器实例"""
    return AutoSummarizer(max_summary_length=max_summary_length)









