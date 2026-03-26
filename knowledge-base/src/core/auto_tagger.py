"""
自动标签生成器
基于文档内容自动生成标签
"""
import logging
from typing import List, Dict, Any, Optional
from .keyword_extractor import KeywordExtractor

logger = logging.getLogger(__name__)


class AutoTagger:
    """自动标签生成器"""
    
    def __init__(self, max_tags: int = 10, min_score: float = 0.1):
        """
        初始化自动标签生成器
        
        Args:
            max_tags: 最大标签数量
            min_score: 最小标签分数阈值
        """
        self.max_tags = max_tags
        self.min_score = min_score
        self.keyword_extractor = KeywordExtractor(max_keywords=max_tags * 2)
        
        # 预定义标签类别
        self.category_keywords = {
            "技术文档": ["api", "代码", "编程", "开发", "技术", "架构", "系统", "算法"],
            "产品文档": ["产品", "功能", "特性", "需求", "规格", "设计", "用户"],
            "用户手册": ["使用", "操作", "指南", "教程", "步骤", "说明", "帮助"],
            "API文档": ["api", "接口", "endpoint", "请求", "响应", "参数", "方法"],
            "常见问题": ["问题", "faq", "解答", "故障", "错误", "解决"],
            "培训材料": ["培训", "学习", "课程", "教学", "教育"],
            "政策文档": ["政策", "规定", "制度", "规则", "流程", "标准"],
            "财务报告": ["财务", "预算", "成本", "收入", "报表", "会计"],
            "市场分析": ["市场", "分析", "调研", "竞争", "趋势", "策略"],
            "项目管理": ["项目", "计划", "进度", "任务", "里程碑", "交付"],
        }
    
    def generate_tags(
        self,
        text: str,
        document_type: Optional[str] = None,
        existing_tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成标签
        
        Args:
            text: 文档内容
            document_type: 文档类型（可选）
            existing_tags: 已有标签（可选）
        
        Returns:
            标签列表，每个标签包含名称、分数、来源等信息
        """
        if not text or len(text.strip()) < 10:
            return []
        
        text_lower = text.lower()
        
        # 1. 从关键词提取标签
        keywords = self.keyword_extractor.extract(text, method="tfidf")
        keyword_tags = [
            {
                "tag": kw["keyword"],
                "score": kw["score"],
                "source": "keyword_extraction",
                "confidence": min(kw["score"] * 2, 1.0)  # 归一化到0-1
            }
            for kw in keywords
            if kw["score"] >= self.min_score
        ]
        
        # 2. 从类别关键词匹配标签
        category_tags = self._match_categories(text_lower)
        
        # 3. 从文档类型推断标签
        type_tags = []
        if document_type:
            type_tags = self._infer_from_type(document_type)
        
        # 合并所有标签
        all_tags = keyword_tags + category_tags + type_tags
        
        # 去重并合并分数
        tag_dict = {}
        for tag_info in all_tags:
            tag_name = tag_info["tag"].lower()
            if tag_name in tag_dict:
                # 合并分数（取最大值并加权）
                tag_dict[tag_name]["score"] = max(
                    tag_dict[tag_name]["score"],
                    tag_info["score"]
                )
                tag_dict[tag_name]["confidence"] = max(
                    tag_dict[tag_name]["confidence"],
                    tag_info["confidence"]
                )
                # 合并来源
                if tag_info["source"] not in tag_dict[tag_name].get("sources", []):
                    tag_dict[tag_name].setdefault("sources", []).append(tag_info["source"])
            else:
                tag_dict[tag_name] = {
                    "tag": tag_info["tag"],
                    "score": tag_info["score"],
                    "confidence": tag_info["confidence"],
                    "source": tag_info["source"],
                    "sources": [tag_info["source"]]
                }
        
        # 过滤已有标签（如果提供）
        if existing_tags:
            existing_tags_lower = [t.lower() for t in existing_tags]
            tag_dict = {
                k: v for k, v in tag_dict.items()
                if k not in existing_tags_lower
            }
        
        # 转换为列表并按分数排序
        tags = list(tag_dict.values())
        tags.sort(key=lambda x: x["score"], reverse=True)
        
        # 返回前N个标签
        return tags[:self.max_tags]
    
    def _match_categories(self, text_lower: str) -> List[Dict[str, Any]]:
        """匹配预定义类别"""
        category_tags = []
        
        for category, keywords in self.category_keywords.items():
            # 计算匹配度
            matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            if matches > 0:
                score = matches / len(keywords)  # 匹配比例
                if score >= 0.2:  # 至少匹配20%的关键词
                    category_tags.append({
                        "tag": category,
                        "score": score,
                        "confidence": min(score * 1.5, 1.0),
                        "source": "category_matching"
                    })
        
        return category_tags
    
    def _infer_from_type(self, document_type: str) -> List[Dict[str, Any]]:
        """从文档类型推断标签"""
        type_mapping = {
            "pdf": ["文档", "PDF"],
            "word": ["文档", "Word"],
            "excel": ["数据", "Excel", "表格"],
            "text": ["文本", "纯文本"],
            "markdown": ["文档", "Markdown"],
        }
        
        doc_type_lower = document_type.lower()
        if doc_type_lower in type_mapping:
            return [
                {
                    "tag": tag,
                    "score": 0.3,
                    "confidence": 0.5,
                    "source": "type_inference"
                }
                for tag in type_mapping[doc_type_lower]
            ]
        
        return []
    
    def suggest_tags(
        self,
        text: str,
        existing_tags: Optional[List[str]] = None,
        min_confidence: float = 0.3
    ) -> List[str]:
        """
        建议标签（简化版，只返回标签名称）
        
        Args:
            text: 文档内容
            existing_tags: 已有标签
            min_confidence: 最小置信度阈值
        
        Returns:
            标签名称列表
        """
        tags = self.generate_tags(text, existing_tags=existing_tags)
        return [
            tag["tag"]
            for tag in tags
            if tag["confidence"] >= min_confidence
        ]


def get_auto_tagger(max_tags: int = 10, min_score: float = 0.1) -> AutoTagger:
    """获取自动标签生成器实例"""
    return AutoTagger(max_tags=max_tags, min_score=min_score)









