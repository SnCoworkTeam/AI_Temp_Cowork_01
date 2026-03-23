"""
数据分类定时任务
"""
import asyncio
import logging
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .data_classifier import DataClassifier

logger = logging.getLogger(__name__)


class ClassificationScheduler:
    """数据分类定时任务调度器"""
    
    def __init__(self, db: Session, interval_minutes: int = 60):
        self.db = db
        self.interval_minutes = interval_minutes
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
    
    async def start(self):
        """启动定时任务"""
        if self.is_running:
            logger.warning("Classification scheduler is already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_periodically())
        logger.info(f"Classification scheduler started (interval: {self.interval_minutes} minutes)")
    
    async def stop(self):
        """停止定时任务"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Classification scheduler stopped")
    
    async def _run_periodically(self):
        """周期性执行分类任务"""
        while self.is_running:
            try:
                await self._run_classification()
                await asyncio.sleep(self.interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error in classification scheduler: {e}", exc_info=True)
                # 出错后等待一段时间再重试
                await asyncio.sleep(60)
    
    async def _run_classification(self):
        """执行分类任务"""
        try:
            logger.info("Starting scheduled data classification...")
            start_time = datetime.now()
            
            classifier = DataClassifier(self.db)
            try:
                result = await classifier.classify_data_assets(persist=True)
                
                self.last_run = datetime.now()
                self.run_count += 1
                duration = (self.last_run - start_time).total_seconds()
                
                logger.info(
                    f"Classification completed: {result.get('classified_assets', 0)} assets, "
                    f"{result.get('persisted_assets', 0)} persisted, "
                    f"duration: {duration:.2f}s"
                )
            finally:
                await classifier.close()
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to run classification: {e}", exc_info=True)
            raise
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "next_run_estimate": (
                (self.last_run + timedelta(minutes=self.interval_minutes)).isoformat()
                if self.last_run else None
            )
        }

