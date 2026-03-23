"""
增量更新
支持文档版本管理、增量更新、差异检测、增量向量化
"""
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """变更类型"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass
class DocumentChange:
    """文档变更"""
    change_type: ChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    start_position: int = 0
    end_position: int = 0
    chunk_id: Optional[str] = None


@dataclass
class DocumentVersion:
    """文档版本"""
    version: int
    content_hash: str
    created_at: datetime
    changes: List[DocumentChange] = field(default_factory=list)


class IncrementalUpdater:
    """增量更新器"""
    
    def __init__(self):
        self.document_versions: Dict[str, List[DocumentVersion]] = {}
    
    def calculate_content_hash(self, text: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def detect_changes(
        self,
        old_text: str,
        new_text: str
    ) -> List[DocumentChange]:
        """
        检测文档变更
        
        Args:
            old_text: 旧文本
            new_text: 新文本
        
        Returns:
            变更列表
        """
        changes = []
        
        # 简单的差异检测（实际应该使用更复杂的diff算法）
        if old_text == new_text:
            return []
        
        old_hash = self.calculate_content_hash(old_text)
        new_hash = self.calculate_content_hash(new_text)
        
        if old_hash == new_hash:
            return []
        
        # 检测添加的内容
        if len(new_text) > len(old_text):
            # 检查是否是追加
            if new_text.startswith(old_text):
                added = new_text[len(old_text):]
                changes.append(DocumentChange(
                    change_type=ChangeType.ADDED,
                    new_content=added,
                    start_position=len(old_text),
                    end_position=len(new_text)
                ))
            else:
                # 内容被修改
                changes.append(DocumentChange(
                    change_type=ChangeType.MODIFIED,
                    old_content=old_text,
                    new_content=new_text,
                    start_position=0,
                    end_position=len(new_text)
                ))
        elif len(new_text) < len(old_text):
            # 检测删除的内容
            if old_text.startswith(new_text):
                deleted = old_text[len(new_text):]
                changes.append(DocumentChange(
                    change_type=ChangeType.DELETED,
                    old_content=deleted,
                    start_position=len(new_text),
                    end_position=len(old_text)
                ))
            else:
                # 内容被修改
                changes.append(DocumentChange(
                    change_type=ChangeType.MODIFIED,
                    old_content=old_text,
                    new_content=new_text,
                    start_position=0,
                    end_position=len(new_text)
                ))
        else:
            # 长度相同但内容不同
            changes.append(DocumentChange(
                change_type=ChangeType.MODIFIED,
                old_content=old_text,
                new_content=new_text,
                start_position=0,
                end_position=len(new_text)
            ))
        
        return changes
    
    def create_version(
        self,
        document_id: str,
        text: str,
        changes: Optional[List[DocumentChange]] = None
    ) -> DocumentVersion:
        """
        创建文档版本
        
        Args:
            document_id: 文档ID
            text: 文档文本
            changes: 变更列表
        
        Returns:
            文档版本
        """
        content_hash = self.calculate_content_hash(text)
        
        # 获取当前版本号
        if document_id in self.document_versions:
            version = len(self.document_versions[document_id]) + 1
        else:
            version = 1
            self.document_versions[document_id] = []
        
        version_obj = DocumentVersion(
            version=version,
            content_hash=content_hash,
            created_at=datetime.utcnow(),
            changes=changes or []
        )
        
        self.document_versions[document_id].append(version_obj)
        
        return version_obj
    
    def get_latest_version(self, document_id: str) -> Optional[DocumentVersion]:
        """获取最新版本"""
        if document_id not in self.document_versions:
            return None
        
        versions = self.document_versions[document_id]
        return versions[-1] if versions else None
    
    def get_version_history(self, document_id: str) -> List[DocumentVersion]:
        """获取版本历史"""
        return self.document_versions.get(document_id, [])
    
    def should_incremental_update(
        self,
        document_id: str,
        new_text: str
    ) -> Tuple[bool, Optional[List[DocumentChange]]]:
        """
        判断是否应该增量更新
        
        Args:
            document_id: 文档ID
            new_text: 新文本
        
        Returns:
            (是否应该增量更新, 变更列表)
        """
        latest_version = self.get_latest_version(document_id)
        if not latest_version:
            return False, None
        
        # 计算新文本哈希
        new_hash = self.calculate_content_hash(new_text)
        
        # 如果哈希相同，无需更新
        if new_hash == latest_version.content_hash:
            return False, []
        
        # 检测变更
        # 注意：这里需要从数据库获取旧文本，简化实现
        changes = []  # 实际应该调用 detect_changes
        
        # 如果变更较小，可以增量更新
        # 这里简化判断：如果变更数量少于总块数的50%，则增量更新
        return True, changes


# 全局增量更新器实例
_incremental_updater: Optional[IncrementalUpdater] = None


def get_incremental_updater() -> IncrementalUpdater:
    """获取增量更新器单例"""
    global _incremental_updater
    if _incremental_updater is None:
        _incremental_updater = IncrementalUpdater()
    return _incremental_updater


