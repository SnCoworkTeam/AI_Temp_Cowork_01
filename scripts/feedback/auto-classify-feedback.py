#!/usr/bin/env python3
"""
自动分类和路由用户反馈
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class FeedbackClassifier:
    """反馈分类器"""
    
    def __init__(self):
        # 关键词映射
        self.keywords = {
            "feature": ["功能", "feature", "需要", "希望", "建议", "添加"],
            "bug": ["错误", "bug", "问题", "故障", "无法", "不能", "失败"],
            "usability": ["体验", "usability", "界面", "操作", "使用", "方便", "简单"]
        }
    
    def classify(self, text: str) -> Tuple[str, float]:
        """
        分类反馈文本
        
        Args:
            text: 反馈文本
            
        Returns:
            (分类, 置信度)
        """
        text_lower = text.lower()
        
        scores = {}
        for category, keywords in self.keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[category] = score / len(keywords) if keywords else 0
        
        if not scores or max(scores.values()) == 0:
            return "unknown", 0.0
        
        best_category = max(scores.items(), key=lambda x: x[1])
        return best_category[0], best_category[1]
    
    def route(self, feedback_file: Path) -> Dict:
        """
        路由反馈文件
        
        Args:
            feedback_file: 反馈文件路径
            
        Returns:
            路由信息
        """
        try:
            content = feedback_file.read_text(encoding='utf-8')
            
            # 提取标题和描述
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else ""
            
            # 分类
            category, confidence = self.classify(title + " " + content)
            
            # 确定路由
            routing = {
                "file": str(feedback_file),
                "category": category,
                "confidence": confidence,
                "routed_to": self._get_routing_path(category)
            }
            
            return routing
        except Exception as e:
            return {
                "file": str(feedback_file),
                "category": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _get_routing_path(self, category: str) -> str:
        """获取路由路径"""
        routes = {
            "feature": "user-feedback/feature-requests",
            "bug": "user-feedback/bug-reports",
            "usability": "user-feedback/usability-feedback",
            "unknown": "user-feedback/unknown"
        }
        return routes.get(category, "user-feedback/unknown")


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent
    feedback_dir = project_root / "feedback-loop"
    
    classifier = FeedbackClassifier()
    
    # 处理用户反馈目录
    results = []
    for feedback_type_dir in feedback_dir.glob("user-feedback/*"):
        if feedback_type_dir.is_dir():
            for feedback_file in feedback_type_dir.glob("*.md"):
                if feedback_file.name != "template.md":
                    routing = classifier.route(feedback_file)
                    results.append(routing)
    
    # 输出结果
    print("反馈分类结果:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # 保存结果
    output_file = feedback_dir / "classification-results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    main()









