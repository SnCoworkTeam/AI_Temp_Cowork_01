"""
文档质量评估器
评估文档的质量和完整性
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class QualityAssessor:
    """文档质量评估器"""
    
    def __init__(self):
        """初始化质量评估器"""
        self.min_content_length = 100  # 最小内容长度
        self.min_word_count = 50  # 最小词数
        self.max_content_length = 10 * 1024 * 1024  # 最大内容长度（10MB）
    
    def assess(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunks: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        评估文档质量
        
        Args:
            content: 文档内容
            metadata: 文档元数据
            chunks: 文档块列表（可选）
        
        Returns:
            质量评估结果，包含总分、各维度分数、建议等
        """
        if not content:
            return {
                "overall_score": 0.0,
                "dimensions": {},
                "issues": ["文档内容为空"],
                "recommendations": ["请提供文档内容"],
                "grade": "F"
            }
        
        # 各维度评估
        dimensions = {
            "content_length": self._assess_content_length(content),
            "readability": self._assess_readability(content),
            "structure": self._assess_structure(content, chunks),
            "metadata_completeness": self._assess_metadata(metadata),
            "language_quality": self._assess_language_quality(content),
        }
        
        # 计算总分（加权平均）
        weights = {
            "content_length": 0.15,
            "readability": 0.25,
            "structure": 0.20,
            "metadata_completeness": 0.15,
            "language_quality": 0.25,
        }
        
        overall_score = sum(
            dimensions[dim] * weights[dim]
            for dim in dimensions
        )
        
        # 识别问题
        issues = self._identify_issues(content, metadata, dimensions)
        
        # 生成建议
        recommendations = self._generate_recommendations(dimensions, issues)
        
        # 评级
        grade = self._get_grade(overall_score)
        
        return {
            "overall_score": round(overall_score, 2),
            "dimensions": {k: round(v, 2) for k, v in dimensions.items()},
            "issues": issues,
            "recommendations": recommendations,
            "grade": grade,
            "assessed_at": datetime.now().isoformat()
        }
    
    def _assess_content_length(self, content: str) -> float:
        """评估内容长度"""
        length = len(content)
        
        if length < self.min_content_length:
            return 0.2  # 太短
        elif length < self.min_content_length * 2:
            return 0.5  # 较短
        elif length < 5000:
            return 1.0  # 理想长度
        elif length < 50000:
            return 0.9  # 较长但可接受
        elif length < self.max_content_length:
            return 0.7  # 很长
        else:
            return 0.3  # 过长
    
    def _assess_readability(self, content: str) -> float:
        """评估可读性"""
        # 计算句子数量
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        if sentence_count == 0:
            return 0.0
        
        # 计算平均句子长度
        words = content.split()
        word_count = len(words)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # 计算平均词长度
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        score = 1.0
        
        # 句子长度检查（理想：15-25词）
        if avg_sentence_length < 10:
            score -= 0.2  # 句子太短
        elif avg_sentence_length > 40:
            score -= 0.3  # 句子太长
        
        # 词长度检查（理想：4-6字符）
        if avg_word_length > 8:
            score -= 0.2  # 词太长（可能包含很多技术术语）
        
        # 段落检查
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) == 0:
            score -= 0.3  # 没有段落结构
        
        return max(0.0, min(1.0, score))
    
    def _assess_structure(self, content: str, chunks: Optional[List[Any]] = None) -> float:
        """评估文档结构"""
        score = 0.5  # 基础分
        
        # 检查标题
        has_title = bool(re.search(r'^#+\s+', content, re.MULTILINE))
        if has_title:
            score += 0.2
        
        # 检查列表
        has_list = bool(re.search(r'^\s*[-*+]\s+', content, re.MULTILINE))
        if has_list:
            score += 0.1
        
        # 检查段落
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 0.1
        
        # 检查分块
        if chunks and len(chunks) > 0:
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_metadata(self, metadata: Optional[Dict[str, Any]]) -> float:
        """评估元数据完整性"""
        if not metadata:
            return 0.0
        
        score = 0.0
        required_fields = ["title", "author", "creation_date"]
        optional_fields = ["modification_date", "language", "page_count", "word_count"]
        
        # 必需字段
        for field in required_fields:
            if metadata.get(field):
                score += 0.2
        
        # 可选字段
        for field in optional_fields:
            if metadata.get(field):
                score += 0.1
        
        return min(1.0, score)
    
    def _assess_language_quality(self, content: str) -> float:
        """评估语言质量"""
        score = 1.0
        
        # 检查拼写错误（简单检查：重复字符）
        repeated_chars = re.findall(r'(.)\1{3,}', content)
        if repeated_chars:
            score -= 0.1
        
        # 检查特殊字符比例
        special_chars = len(re.findall(r'[^\w\s]', content))
        total_chars = len(content)
        if total_chars > 0:
            special_char_ratio = special_chars / total_chars
            if special_char_ratio > 0.3:
                score -= 0.2  # 特殊字符过多
        
        # 检查空白字符比例
        whitespace_ratio = content.count(' ') / total_chars if total_chars > 0 else 0
        if whitespace_ratio < 0.1:
            score -= 0.2  # 空白字符太少（可能格式有问题）
        
        return max(0.0, min(1.0, score))
    
    def _identify_issues(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]],
        dimensions: Dict[str, float]
    ) -> List[str]:
        """识别问题"""
        issues = []
        
        # 内容长度问题
        if dimensions["content_length"] < 0.5:
            issues.append("文档内容过短")
        
        # 可读性问题
        if dimensions["readability"] < 0.6:
            issues.append("文档可读性较差")
        
        # 结构问题
        if dimensions["structure"] < 0.5:
            issues.append("文档结构不清晰")
        
        # 元数据问题
        if dimensions["metadata_completeness"] < 0.5:
            issues.append("文档元数据不完整")
        
        # 语言质量问题
        if dimensions["language_quality"] < 0.7:
            issues.append("文档语言质量需要改进")
        
        # 内容检查
        if len(content) < self.min_content_length:
            issues.append(f"内容长度不足（建议至少{self.min_content_length}字符）")
        
        if not metadata or not metadata.get("title"):
            issues.append("缺少文档标题")
        
        return issues
    
    def _generate_recommendations(
        self,
        dimensions: Dict[str, float],
        issues: List[str]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if dimensions["content_length"] < 0.7:
            recommendations.append("增加文档内容，提供更详细的信息")
        
        if dimensions["readability"] < 0.7:
            recommendations.append("改进文档可读性：使用更短的句子和段落")
        
        if dimensions["structure"] < 0.7:
            recommendations.append("改进文档结构：添加标题、列表和段落分隔")
        
        if dimensions["metadata_completeness"] < 0.7:
            recommendations.append("完善文档元数据：添加标题、作者、创建日期等信息")
        
        if dimensions["language_quality"] < 0.7:
            recommendations.append("改进语言质量：检查拼写和语法错误")
        
        if not recommendations:
            recommendations.append("文档质量良好，继续保持")
        
        return recommendations
    
    def _get_grade(self, score: float) -> str:
        """获取评级"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"


def get_quality_assessor() -> QualityAssessor:
    """获取质量评估器实例"""
    return QualityAssessor()









