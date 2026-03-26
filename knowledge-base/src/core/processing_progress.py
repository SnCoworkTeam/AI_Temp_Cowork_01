"""
处理进度跟踪
支持进度百分比、处理时间预估、实时进度更新
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ProcessingStage(str, Enum):
    """处理阶段"""
    UPLOADING = "uploading"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingProgress:
    """处理进度信息"""
    document_id: str
    stage: ProcessingStage
    progress_percentage: float = 0.0  # 0-100
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    estimated_time_remaining: Optional[float] = None  # 秒
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class ProgressTracker:
    """进度跟踪器"""
    
    # 各阶段预估时间（秒）
    STAGE_ESTIMATES = {
        ProcessingStage.UPLOADING: 1.0,
        ProcessingStage.PARSING: 5.0,
        ProcessingStage.CHUNKING: 2.0,
        ProcessingStage.EMBEDDING: 10.0,  # 取决于文档大小
        ProcessingStage.STORING: 3.0,
    }
    
    # 各阶段进度权重
    STAGE_WEIGHTS = {
        ProcessingStage.UPLOADING: 5,
        ProcessingStage.PARSING: 15,
        ProcessingStage.CHUNKING: 10,
        ProcessingStage.EMBEDDING: 60,
        ProcessingStage.STORING: 10,
    }
    
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.progress = ProcessingProgress(
            document_id=document_id,
            stage=ProcessingStage.UPLOADING,
            started_at=datetime.utcnow()
        )
        self.stage_start_times: Dict[ProcessingStage, datetime] = {}
        self.stage_durations: Dict[ProcessingStage, float] = {}
    
    def start_stage(self, stage: ProcessingStage, details: Optional[Dict[str, Any]] = None):
        """开始处理阶段"""
        self.progress.stage = stage
        self.progress.current_step = stage.value
        self.stage_start_times[stage] = datetime.utcnow()
        self.progress.updated_at = datetime.utcnow()
        
        if details:
            self.progress.details.update(details)
        
        self._update_progress()
        logger.info(f"Document {self.document_id} started stage: {stage.value}")
    
    def update_step(self, step_name: str, completed: int = None, total: int = None):
        """更新步骤进度"""
        self.progress.current_step = step_name
        if completed is not None:
            self.progress.completed_steps = completed
        if total is not None:
            self.progress.total_steps = total
        
        self._update_progress()
    
    def complete_stage(self, stage: ProcessingStage):
        """完成处理阶段"""
        if stage in self.stage_start_times:
            duration = (datetime.utcnow() - self.stage_start_times[stage]).total_seconds()
            self.stage_durations[stage] = duration
        
        self._update_progress()
        logger.info(f"Document {self.document_id} completed stage: {stage.value}")
    
    def set_error(self, error: str):
        """设置错误"""
        self.progress.stage = ProcessingStage.FAILED
        self.progress.error = error
        self.progress.updated_at = datetime.utcnow()
        logger.error(f"Document {self.document_id} error: {error}")
    
    def _update_progress(self):
        """更新进度百分比和预估时间"""
        # 计算当前阶段的基础进度
        stage_order = [
            ProcessingStage.UPLOADING,
            ProcessingStage.PARSING,
            ProcessingStage.CHUNKING,
            ProcessingStage.EMBEDDING,
            ProcessingStage.STORING,
        ]
        
        current_stage_index = stage_order.index(self.progress.stage) if self.progress.stage in stage_order else 0
        
        # 计算已完成阶段的进度
        completed_progress = 0.0
        for i, stage in enumerate(stage_order):
            if i < current_stage_index:
                weight = self.STAGE_WEIGHTS.get(stage, 0)
                completed_progress += weight
            elif i == current_stage_index:
                # 当前阶段的进度
                weight = self.STAGE_WEIGHTS.get(stage, 0)
                stage_progress = self._calculate_stage_progress(stage)
                completed_progress += weight * stage_progress
        
        self.progress.progress_percentage = min(100.0, completed_progress)
        
        # 计算预估剩余时间
        self._estimate_remaining_time()
        
        self.progress.updated_at = datetime.utcnow()
    
    def _calculate_stage_progress(self, stage: ProcessingStage) -> float:
        """计算当前阶段的进度（0-1）"""
        if self.progress.total_steps > 0:
            return min(1.0, self.progress.completed_steps / self.progress.total_steps)
        
        # 根据阶段类型估算
        if stage == ProcessingStage.EMBEDDING:
            # 嵌入阶段通常较慢，根据已用时间估算
            if stage in self.stage_start_times:
                elapsed = (datetime.utcnow() - self.stage_start_times[stage]).total_seconds()
                estimated = self.STAGE_ESTIMATES.get(stage, 10.0)
                return min(0.9, elapsed / estimated)  # 最多显示90%，直到完成
        
        return 0.5  # 默认50%
    
    def _estimate_remaining_time(self):
        """估算剩余时间"""
        if self.progress.stage == ProcessingStage.COMPLETED:
            self.progress.estimated_time_remaining = 0.0
            return
        
        if self.progress.stage == ProcessingStage.FAILED:
            self.progress.estimated_time_remaining = None
            return
        
        # 计算已用时间
        if self.progress.started_at:
            elapsed = (datetime.utcnow() - self.progress.started_at).total_seconds()
        else:
            elapsed = 0.0
        
        # 根据当前进度估算总时间
        if self.progress.progress_percentage > 0:
            estimated_total = elapsed / (self.progress.progress_percentage / 100.0)
            remaining = max(0.0, estimated_total - elapsed)
            self.progress.estimated_time_remaining = remaining
        else:
            # 使用阶段预估时间
            stage_order = [
                ProcessingStage.UPLOADING,
                ProcessingStage.PARSING,
                ProcessingStage.CHUNKING,
                ProcessingStage.EMBEDDING,
                ProcessingStage.STORING,
            ]
            
            current_index = stage_order.index(self.progress.stage) if self.progress.stage in stage_order else 0
            remaining_time = 0.0
            
            # 当前阶段剩余时间
            if self.progress.stage in self.STAGE_ESTIMATES:
                stage_progress = self._calculate_stage_progress(self.progress.stage)
                remaining_time += self.STAGE_ESTIMATES[self.progress.stage] * (1 - stage_progress)
            
            # 后续阶段预估时间
            for i in range(current_index + 1, len(stage_order)):
                stage = stage_order[i]
                if stage in self.STAGE_ESTIMATES:
                    remaining_time += self.STAGE_ESTIMATES[stage]
            
            self.progress.estimated_time_remaining = remaining_time
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度信息（字典格式）"""
        return {
            "document_id": self.progress.document_id,
            "stage": self.progress.stage.value,
            "progress_percentage": round(self.progress.progress_percentage, 2),
            "current_step": self.progress.current_step,
            "total_steps": self.progress.total_steps,
            "completed_steps": self.progress.completed_steps,
            "estimated_time_remaining": self.progress.estimated_time_remaining,
            "started_at": self.progress.started_at.isoformat() if self.progress.started_at else None,
            "updated_at": self.progress.updated_at.isoformat() if self.progress.updated_at else None,
            "details": self.progress.details,
            "error": self.progress.error
        }


# 全局进度跟踪器存储
_progress_trackers: Dict[str, ProgressTracker] = {}


def get_progress_tracker(document_id: str) -> ProgressTracker:
    """获取或创建进度跟踪器"""
    if document_id not in _progress_trackers:
        _progress_trackers[document_id] = ProgressTracker(document_id)
    return _progress_trackers[document_id]


def remove_progress_tracker(document_id: str):
    """移除进度跟踪器"""
    if document_id in _progress_trackers:
        del _progress_trackers[document_id]


