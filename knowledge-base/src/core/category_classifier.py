"""
文档分类器
自动对文档进行分类
"""
import logging
from typing import List, Dict, Any, Optional
from .keyword_extractor import KeywordExtractor

logger = logging.getLogger(__name__)


class CategoryClassifier:
    """文档分类器"""
    
    def __init__(self):
        """初始化文档分类器"""
        self.keyword_extractor = KeywordExtractor(max_keywords=20)
        
        # 预定义文档类别及其特征关键词
        self.categories = {
            "技术文档": {
                "keywords": ["api", "代码", "编程", "开发", "技术", "架构", "系统", "算法", "框架", "库"],
                "weight": 1.0
            },
            "产品文档": {
                "keywords": ["产品", "功能", "特性", "需求", "规格", "设计", "用户", "界面", "体验"],
                "weight": 1.0
            },
            "用户手册": {
                "keywords": ["使用", "操作", "指南", "教程", "步骤", "说明", "帮助", "如何", "方法"],
                "weight": 1.0
            },
            "API文档": {
                "keywords": ["api", "接口", "endpoint", "请求", "响应", "参数", "方法", "rest", "http"],
                "weight": 1.2  # 更高的权重
            },
            "常见问题": {
                "keywords": ["问题", "faq", "解答", "故障", "错误", "解决", "修复", "常见"],
                "weight": 1.0
            },
            "培训材料": {
                "keywords": ["培训", "学习", "课程", "教学", "教育", "培训", "练习", "示例"],
                "weight": 1.0
            },
            "政策文档": {
                "keywords": ["政策", "规定", "制度", "规则", "流程", "标准", "规范", "合规"],
                "weight": 1.0
            },
            "财务报告": {
                "keywords": ["财务", "预算", "成本", "收入", "报表", "会计", "利润", "支出"],
                "weight": 1.0
            },
            "市场分析": {
                "keywords": ["市场", "分析", "调研", "竞争", "趋势", "策略", "客户", "销售"],
                "weight": 1.0
            },
            "项目管理": {
                "keywords": ["项目", "计划", "进度", "任务", "里程碑", "交付", "资源", "风险"],
                "weight": 1.0
            },
            "会议记录": {
                "keywords": ["会议", "讨论", "决议", "议题", "参会", "记录", "纪要"],
                "weight": 1.0
            },
            "研究报告": {
                "keywords": ["研究", "分析", "数据", "结论", "建议", "调查", "统计"],
                "weight": 1.0
            },
        }
    
    def classify(
        self,
        text: str,
        document_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        对文档进行分类
        
        Args:
            text: 文档内容
            document_type: 文档类型（可选）
            metadata: 文档元数据（可选）
        
        Returns:
            分类结果，包含主要类别、置信度、所有类别分数等
        """
        if not text or len(text.strip()) < 10:
            return {
                "category": "未分类",
                "confidence": 0.0,
                "scores": {},
                "method": "insufficient_content"
            }
        
        text_lower = text.lower()
        
        # 计算每个类别的匹配分数
        category_scores = {}
        
        for category, config in self.categories.items():
            keywords = config["keywords"]
            weight = config["weight"]
            
            # 计算关键词匹配数
            matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            
            if matches > 0:
                # 计算分数：匹配比例 * 权重
                score = (matches / len(keywords)) * weight
                category_scores[category] = score
        
        # 如果没有匹配，尝试从文档类型推断
        if not category_scores and document_type:
            inferred = self._infer_from_type(document_type)
            if inferred:
                category_scores[inferred] = 0.3
        
        # 如果没有匹配，尝试从元数据推断
        if not category_scores and metadata:
            inferred = self._infer_from_metadata(metadata)
            if inferred:
                category_scores[inferred] = 0.2
        
        if not category_scores:
            return {
                "category": "未分类",
                "confidence": 0.0,
                "scores": {},
                "method": "no_match"
            }
        
        # 找到最高分的类别
        max_score = max(category_scores.values())
        primary_category = max(category_scores.items(), key=lambda x: x[1])[0]
        
        # 归一化分数
        total_score = sum(category_scores.values())
        normalized_scores = {
            cat: score / total_score if total_score > 0 else 0
            for cat, score in category_scores.items()
        }
        
        # 计算置信度（最高分 / 总分）
        confidence = max_score / total_score if total_score > 0 else 0
        
        return {
            "category": primary_category,
            "confidence": min(confidence, 1.0),
            "scores": normalized_scores,
            "raw_scores": category_scores,
            "method": "keyword_matching"
        }
    
    def _infer_from_type(self, document_type: str) -> Optional[str]:
        """从文档类型推断类别"""
        type_mapping = {
            "excel": "财务报告",
            "pdf": "文档",
            "word": "文档",
        }
        
        doc_type_lower = document_type.lower()
        return type_mapping.get(doc_type_lower)
    
    def _infer_from_metadata(self, metadata: Dict[str, Any]) -> Optional[str]:
        """从元数据推断类别"""
        # 检查标题中的关键词
        title = metadata.get("title", "").lower()
        if title:
            for category, config in self.categories.items():
                for kw in config["keywords"]:
                    if kw.lower() in title:
                        return category
        
        # 检查作者信息
        author = metadata.get("author", "").lower()
        if "技术" in author or "开发" in author:
            return "技术文档"
        
        return None
    
    def get_top_categories(
        self,
        text: str,
        top_k: int = 3,
        min_confidence: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        获取top-k类别
        
        Args:
            text: 文档内容
            top_k: 返回前k个类别
            min_confidence: 最小置信度阈值
        
        Returns:
            类别列表，按置信度排序
        """
        result = self.classify(text)
        
        if not result["scores"]:
            return []
        
        # 按分数排序
        sorted_categories = sorted(
            result["scores"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 过滤并返回top-k
        top_categories = []
        for category, score in sorted_categories[:top_k]:
            if score >= min_confidence:
                top_categories.append({
                    "category": category,
                    "confidence": score,
                    "raw_score": result["raw_scores"].get(category, 0)
                })
        
        return top_categories


def get_category_classifier() -> CategoryClassifier:
    """获取文档分类器实例"""
    return CategoryClassifier()









