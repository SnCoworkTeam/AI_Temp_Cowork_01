"""
质量等级枚举
定义数据质量相关的枚举类型
"""
from enum import Enum


class QualityLevel(str, Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"  # 优秀 (90-100)
    GOOD = "good"           # 良好 (75-89)
    FAIR = "fair"           # 一般 (60-74)
    POOR = "poor"           # 较差 (40-59)
    CRITICAL = "critical"   # 严重 (0-39)
    UNKNOWN = "unknown"     # 未知


class QualityScore(float, Enum):
    """质量分数范围"""
    EXCELLENT_MIN = 0.90
    GOOD_MIN = 0.75
    FAIR_MIN = 0.60
    POOR_MIN = 0.40
    CRITICAL_MAX = 0.39
    
    @classmethod
    def get_level(cls, score: float) -> "QualityLevel":
        """根据分数获取质量等级"""
        if score >= cls.EXCELLENT_MIN:
            return QualityLevel.EXCELLENT
        elif score >= cls.GOOD_MIN:
            return QualityLevel.GOOD
        elif score >= cls.FAIR_MIN:
            return QualityLevel.FAIR
        elif score >= cls.POOR_MIN:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL


class CompletenessLevel(str, Enum):
    """完整性等级"""
    COMPLETE = "complete"      # 完整 (100%)
    MOSTLY_COMPLETE = "mostly_complete"  # 基本完整 (90-99%)
    PARTIALLY_COMPLETE = "partially_complete"  # 部分完整 (50-89%)
    INCOMPLETE = "incomplete"  # 不完整 (<50%)
    UNKNOWN = "unknown"


class AccuracyLevel(str, Enum):
    """准确性等级"""
    HIGHLY_ACCURATE = "highly_accurate"  # 高度准确 (95-100%)
    ACCURATE = "accurate"                # 准确 (85-94%)
    MODERATELY_ACCURATE = "moderately_accurate"  # 中等准确 (70-84%)
    INACCURATE = "inaccurate"            # 不准确 (<70%)
    UNKNOWN = "unknown"

