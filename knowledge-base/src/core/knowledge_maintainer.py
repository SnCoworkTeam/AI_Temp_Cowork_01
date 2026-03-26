"""
知识库维护器
执行知识库的维护任务
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .quality_assessor import get_quality_assessor
from .duplicate_detector import get_duplicate_detector
from .outdated_detector import get_outdated_detector
from .auto_summarizer import get_auto_summarizer

logger = logging.getLogger(__name__)


class KnowledgeMaintainer:
    """知识库维护器"""
    
    def __init__(self):
        """初始化知识库维护器"""
        self.quality_assessor = get_quality_assessor()
        self.duplicate_detector = get_duplicate_detector()
        self.outdated_detector = get_outdated_detector()
        self.auto_summarizer = get_auto_summarizer()
    
    def run_maintenance(
        self,
        documents: List[Dict[str, Any]],
        tasks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        运行维护任务
        
        Args:
            documents: 文档列表
            tasks: 要执行的任务列表（如果为None则执行所有任务）
        
        Returns:
            维护报告，包含各项检查结果和建议
        """
        if tasks is None:
            tasks = ["quality", "duplicates", "outdated", "health"]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_documents": len(documents),
            "tasks": {},
            "summary": {},
            "recommendations": []
        }
        
        # 质量检查
        if "quality" in tasks:
            quality_report = self._check_quality(documents)
            report["tasks"]["quality"] = quality_report
        
        # 重复检测
        if "duplicates" in tasks:
            duplicate_report = self._check_duplicates(documents)
            report["tasks"]["duplicates"] = duplicate_report
        
        # 过时内容检测
        if "outdated" in tasks:
            outdated_report = self._check_outdated(documents)
            report["tasks"]["outdated"] = outdated_report
        
        # 健康度评估
        if "health" in tasks:
            health_report = self._assess_health(documents, report["tasks"])
            report["tasks"]["health"] = health_report
        
        # 生成摘要
        report["summary"] = self._generate_summary(report["tasks"])
        report["recommendations"] = self._generate_recommendations(report["tasks"])
        
        return report
    
    def _check_quality(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查文档质量"""
        quality_results = []
        quality_scores = []
        
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            if content:
                assessment = self.quality_assessor.assess(content, metadata)
                quality_results.append({
                    "document_id": doc.get("id"),
                    "filename": doc.get("filename"),
                    "score": assessment["overall_score"],
                    "grade": assessment["grade"],
                    "issues": assessment["issues"]
                })
                quality_scores.append(assessment["overall_score"])
        
        avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # 统计各等级数量
        grade_distribution = {}
        for result in quality_results:
            grade = result["grade"]
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        return {
            "average_score": round(avg_score, 2),
            "total_assessed": len(quality_results),
            "grade_distribution": grade_distribution,
            "low_quality_docs": [
                r for r in quality_results
                if r["score"] < 0.6
            ],
            "results": quality_results[:10]  # 只返回前10个结果
        }
    
    def _check_duplicates(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查重复文档"""
        if len(documents) < 2:
            return {
                "duplicate_groups": [],
                "total_duplicates": 0,
                "message": "文档数量不足，无法进行重复检测"
            }
        
        duplicate_groups = self.duplicate_detector.detect_duplicates(
            documents,
            method="embedding"
        )
        
        total_duplicates = sum(len(group["documents"]) for group in duplicate_groups)
        
        return {
            "duplicate_groups": duplicate_groups,
            "total_duplicates": total_duplicates,
            "total_groups": len(duplicate_groups)
        }
    
    def _check_outdated(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查过时文档"""
        outdated_docs = self.outdated_detector.detect_outdated(documents)
        
        # 按严重程度分组
        by_severity = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for doc in outdated_docs:
            severity = doc.get("severity", "low")
            by_severity[severity].append(doc)
        
        return {
            "outdated_documents": outdated_docs,
            "total_outdated": len(outdated_docs),
            "by_severity": {
                k: len(v) for k, v in by_severity.items()
            },
            "high_priority": by_severity["high"]
        }
    
    def _assess_health(
        self,
        documents: List[Dict[str, Any]],
        task_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估知识库健康度"""
        health_scores = {}
        
        # 质量健康度
        if "quality" in task_results:
            quality_result = task_results["quality"]
            avg_score = quality_result.get("average_score", 0.0)
            health_scores["quality"] = avg_score
        
        # 重复健康度（重复越少越好）
        if "duplicates" in task_results:
            duplicate_result = task_results["duplicates"]
            total_docs = len(documents)
            duplicate_count = duplicate_result.get("total_duplicates", 0)
            if total_docs > 0:
                duplicate_ratio = duplicate_count / total_docs
                health_scores["duplicates"] = 1.0 - min(duplicate_ratio, 1.0)
            else:
                health_scores["duplicates"] = 1.0
        
        # 时效性健康度（过时文档越少越好）
        if "outdated" in task_results:
            outdated_result = task_results["outdated"]
            total_docs = len(documents)
            outdated_count = outdated_result.get("total_outdated", 0)
            if total_docs > 0:
                outdated_ratio = outdated_count / total_docs
                health_scores["timeliness"] = 1.0 - min(outdated_ratio, 0.5)  # 最多影响50%
            else:
                health_scores["timeliness"] = 1.0
        
        # 计算总体健康度
        if health_scores:
            overall_health = sum(health_scores.values()) / len(health_scores)
        else:
            overall_health = 1.0
        
        # 健康度评级
        if overall_health >= 0.8:
            health_status = "excellent"
        elif overall_health >= 0.6:
            health_status = "good"
        elif overall_health >= 0.4:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            "overall_health": round(overall_health, 2),
            "health_status": health_status,
            "dimension_scores": health_scores
        }
    
    def _generate_summary(self, task_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成维护摘要"""
        summary = {}
        
        if "quality" in task_results:
            quality = task_results["quality"]
            summary["average_quality"] = quality.get("average_score", 0.0)
            summary["low_quality_count"] = len(quality.get("low_quality_docs", []))
        
        if "duplicates" in task_results:
            duplicates = task_results["duplicates"]
            summary["duplicate_groups"] = duplicates.get("total_groups", 0)
            summary["duplicate_documents"] = duplicates.get("total_duplicates", 0)
        
        if "outdated" in task_results:
            outdated = task_results["outdated"]
            summary["outdated_documents"] = outdated.get("total_outdated", 0)
        
        if "health" in task_results:
            health = task_results["health"]
            summary["health_status"] = health.get("health_status", "unknown")
            summary["overall_health"] = health.get("overall_health", 0.0)
        
        return summary
    
    def _generate_recommendations(self, task_results: Dict[str, Any]) -> List[str]:
        """生成维护建议"""
        recommendations = []
        
        # 质量建议
        if "quality" in task_results:
            quality = task_results["quality"]
            low_quality_count = len(quality.get("low_quality_docs", []))
            if low_quality_count > 0:
                recommendations.append(
                    f"发现{low_quality_count}个低质量文档，建议改进内容质量"
                )
        
        # 重复建议
        if "duplicates" in task_results:
            duplicates = task_results["duplicates"]
            duplicate_count = duplicates.get("total_duplicates", 0)
            if duplicate_count > 0:
                recommendations.append(
                    f"发现{duplicate_count}个重复文档，建议合并或删除重复内容"
                )
        
        # 过时建议
        if "outdated" in task_results:
            outdated = task_results["outdated"]
            outdated_count = outdated.get("total_outdated", 0)
            if outdated_count > 0:
                recommendations.append(
                    f"发现{outdated_count}个过时文档，建议更新或确认内容有效性"
                )
        
        # 健康度建议
        if "health" in task_results:
            health = task_results["health"]
            health_status = health.get("health_status", "unknown")
            if health_status in ["fair", "poor"]:
                recommendations.append(
                    "知识库健康度较低，建议进行全面维护"
                )
        
        if not recommendations:
            recommendations.append("知识库状态良好，建议定期维护")
        
        return recommendations


def get_knowledge_maintainer() -> KnowledgeMaintainer:
    """获取知识库维护器实例"""
    return KnowledgeMaintainer()









