"""
过时内容检测器
检测知识库中的过时文档
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OutdatedDetector:
    """过时内容检测器"""
    
    def __init__(
        self,
        max_age_days: int = 365,
        check_metadata: bool = True,
        check_content: bool = True
    ):
        """
        初始化过时内容检测器
        
        Args:
            max_age_days: 文档最大年龄（天数），超过此值视为可能过时
            check_metadata: 是否检查元数据中的日期
            check_content: 是否检查内容中的日期信息
        """
        self.max_age_days = max_age_days
        self.check_metadata = check_metadata
        self.check_content = check_content
    
    def detect_outdated(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        检测过时文档
        
        Args:
            documents: 文档列表，每个文档包含id、metadata、uploaded_at等字段
        
        Returns:
            过时文档列表，包含文档ID、过时原因、建议等
        """
        outdated_docs = []
        
        current_date = datetime.now()
        max_age = timedelta(days=self.max_age_days)
        
        for doc in documents:
            outdated_info = self._check_document(doc, current_date, max_age)
            
            if outdated_info["is_outdated"]:
                outdated_docs.append({
                    "document_id": doc.get("id"),
                    "filename": doc.get("filename"),
                    "outdated_reasons": outdated_info["reasons"],
                    "suggestions": outdated_info["suggestions"],
                    "last_updated": outdated_info["last_updated"],
                    "age_days": outdated_info["age_days"],
                    "severity": outdated_info["severity"]
                })
        
        return outdated_docs
    
    def _check_document(
        self,
        document: Dict[str, Any],
        current_date: datetime,
        max_age: timedelta
    ) -> Dict[str, Any]:
        """检查单个文档是否过时"""
        reasons = []
        suggestions = []
        last_updated = None
        age_days = 0
        severity = "low"
        
        # 1. 检查上传时间
        uploaded_at = document.get("uploaded_at")
        if uploaded_at:
            if isinstance(uploaded_at, str):
                try:
                    uploaded_at = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
                except:
                    uploaded_at = None
        
        if uploaded_at:
            age = current_date - uploaded_at.replace(tzinfo=None)
            age_days = age.days
            last_updated = uploaded_at
            
            if age > max_age:
                reasons.append(f"文档上传时间超过{self.max_age_days}天（{age_days}天前）")
                suggestions.append("建议更新文档内容或确认文档仍然有效")
                severity = "medium"
        
        # 2. 检查元数据中的日期
        if self.check_metadata:
            metadata = document.get("metadata", {})
            
            # 检查创建日期
            creation_date = metadata.get("creation_date")
            if creation_date:
                if isinstance(creation_date, str):
                    try:
                        creation_date = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
                    except:
                        creation_date = None
                
                if creation_date:
                    age = current_date - creation_date.replace(tzinfo=None)
                    if age.days > self.max_age_days * 2:  # 创建日期更严格
                        reasons.append(f"文档创建时间超过{self.max_age_days * 2}天")
                        suggestions.append("建议检查文档内容是否仍然准确")
                        severity = "high"
            
            # 检查修改日期
            modification_date = metadata.get("modification_date")
            if modification_date:
                if isinstance(modification_date, str):
                    try:
                        modification_date = datetime.fromisoformat(modification_date.replace('Z', '+00:00'))
                    except:
                        modification_date = None
                
                if modification_date:
                    age = current_date - modification_date.replace(tzinfo=None)
                    if age > max_age:
                        reasons.append(f"文档最后修改时间超过{self.max_age_days}天")
                        suggestions.append("建议更新文档内容")
                        if severity == "low":
                            severity = "medium"
                    
                    # 更新最后更新时间
                    if last_updated is None or modification_date > last_updated:
                        last_updated = modification_date
                        age_days = age.days
        
        # 3. 检查内容中的日期信息
        if self.check_content:
            content = document.get("content", "")
            if content:
                date_info = self._extract_dates_from_content(content)
                if date_info:
                    for date_str, date_obj in date_info:
                        age = current_date - date_obj
                        if age.days > self.max_age_days:
                            reasons.append(f"文档内容中提到日期：{date_str}（{age.days}天前）")
                            suggestions.append("建议检查相关内容是否仍然有效")
                            if severity != "high":
                                severity = "medium"
        
        # 4. 检查版本信息
        version = document.get("version", 1)
        if version == 1 and age_days > self.max_age_days:
            reasons.append("文档从未更新过（版本为1）")
            suggestions.append("建议定期审查和更新文档")
        
        is_outdated = len(reasons) > 0
        
        return {
            "is_outdated": is_outdated,
            "reasons": reasons,
            "suggestions": suggestions,
            "last_updated": last_updated.isoformat() if last_updated else None,
            "age_days": age_days,
            "severity": severity
        }
    
    def _extract_dates_from_content(self, content: str) -> List[Tuple[str, datetime]]:
        """从内容中提取日期"""
        import re
        from datetime import datetime
        
        dates = []
        
        # 匹配日期格式：YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY等
        date_patterns = [
            (r'\d{4}-\d{2}-\d{2}', '%Y-%m-%d'),
            (r'\d{4}/\d{2}/\d{2}', '%Y/%m/%d'),
            (r'\d{2}/\d{2}/\d{4}', '%d/%m/%Y'),
            (r'\d{4}年\d{1,2}月\d{1,2}日', None),  # 中文日期
        ]
        
        for pattern, date_format in date_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                date_str = match.group()
                try:
                    if date_format:
                        date_obj = datetime.strptime(date_str, date_format)
                    else:
                        # 处理中文日期
                        import re as re2
                        nums = re2.findall(r'\d+', date_str)
                        if len(nums) == 3:
                            date_obj = datetime(int(nums[0]), int(nums[1]), int(nums[2]))
                        else:
                            continue
                    
                    dates.append((date_str, date_obj))
                except:
                    continue
        
        return dates


def get_outdated_detector(
    max_age_days: int = 365,
    check_metadata: bool = True,
    check_content: bool = True
) -> OutdatedDetector:
    """获取过时内容检测器实例"""
    return OutdatedDetector(
        max_age_days=max_age_days,
        check_metadata=check_metadata,
        check_content=check_content
    )

