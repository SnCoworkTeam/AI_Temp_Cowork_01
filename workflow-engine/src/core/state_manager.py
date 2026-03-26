"""
工作流状态管理器
管理工作流执行状态的持久化和恢复
- PostgreSQL: 长期状态存储
- Redis: 活跃执行状态缓存
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID
import json

from sqlalchemy.orm import Session

# 导入Redis客户端
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.redis_client import get_async_redis_client

logger = logging.getLogger(__name__)


class WorkflowStateManager:
    """工作流状态管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self._redis = None
        self._cache_prefix = "workflow:state:"
        self._cache_ttl = 3600  # 1小时
        self._active_cache_prefix = "workflow:active:"
        self._active_cache_ttl = 86400  # 24小时
    
    async def _get_redis(self):
        """获取Redis客户端（延迟初始化）"""
        if self._redis is None:
            self._redis = await get_async_redis_client()
        return self._redis
    
    async def save_state(
        self,
        execution_id: str,
        state: Dict[str, Any],
        is_active: bool = True
    ) -> bool:
        """
        保存工作流状态
        
        Args:
            execution_id: 执行ID
            state: 状态数据
            is_active: 是否为活跃执行
        
        Returns:
            是否成功
        """
        try:
            # 1. 保存到数据库（长期存储）
            from ..repositories.execution_repository import ExecutionRepository
            execution_repo = ExecutionRepository(self.db)
            
            execution = execution_repo.get_by_id(execution_id)
            if execution:
                # 更新执行记录的元数据，包含状态快照
                if execution.metadata is None:
                    execution.metadata = {}
                execution.metadata["state_snapshot"] = {
                    "data": state,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.db.commit()
            
            # 2. 保存到Redis（活跃执行快速访问）
            if is_active:
                redis_client = await self._get_redis()
                if redis_client:
                    cache_key = f"{self._active_cache_prefix}{execution_id}"
                    await redis_client.set(
                        cache_key,
                        json.dumps(state, ensure_ascii=False),
                        ex=self._active_cache_ttl
                    )
                    
                    # 添加到活跃执行列表
                    active_list_key = "workflow:active:list"
                    await redis_client.sadd(active_list_key, execution_id)
                    await redis_client.expire(active_list_key, self._active_cache_ttl)
            
            logger.debug(f"State saved for execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    async def load_state(
        self,
        execution_id: str,
        prefer_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        加载工作流状态
        
        Args:
            execution_id: 执行ID
            prefer_cache: 是否优先从缓存加载
        
        Returns:
            状态数据，如果不存在则返回None
        """
        try:
            # 1. 优先从Redis缓存加载（活跃执行）
            if prefer_cache:
                redis_client = await self._get_redis()
                if redis_client:
                    cache_key = f"{self._active_cache_prefix}{execution_id}"
                    cached_state = await redis_client.get(cache_key)
                    if cached_state:
                        try:
                            state = json.loads(cached_state)
                            logger.debug(f"State loaded from cache: {execution_id}")
                            return state
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid cached state format: {execution_id}")
            
            # 2. 从数据库加载
            from ..repositories.execution_repository import ExecutionRepository
            execution_repo = ExecutionRepository(self.db)
            
            execution = execution_repo.get_by_id(execution_id)
            if execution and execution.metadata:
                state_snapshot = execution.metadata.get("state_snapshot")
                if state_snapshot and "data" in state_snapshot:
                    state = state_snapshot["data"]
                    
                    # 如果状态存在且执行仍在运行，更新缓存
                    if execution.status.value == "running":
                        redis_client = await self._get_redis()
                        if redis_client:
                            cache_key = f"{self._active_cache_prefix}{execution_id}"
                            await redis_client.set(
                                cache_key,
                                json.dumps(state, ensure_ascii=False),
                                ex=self._active_cache_ttl
                            )
                    
                    logger.debug(f"State loaded from database: {execution_id}")
                    return state
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}", exc_info=True)
            return None
    
    async def update_state(
        self,
        execution_id: str,
        updates: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """
        更新工作流状态
        
        Args:
            execution_id: 执行ID
            updates: 要更新的状态数据
            merge: 是否合并更新（True）或替换（False）
        
        Returns:
            是否成功
        """
        try:
            # 加载当前状态
            current_state = await self.load_state(execution_id)
            
            if current_state is None:
                current_state = {}
            
            # 合并或替换
            if merge:
                current_state.update(updates)
            else:
                current_state = updates
            
            # 保存更新后的状态
            return await self.save_state(execution_id, current_state, is_active=True)
            
        except Exception as e:
            logger.error(f"Error updating state: {str(e)}", exc_info=True)
            return False
    
    async def delete_state(self, execution_id: str, clear_cache: bool = True) -> bool:
        """
        删除工作流状态
        
        Args:
            execution_id: 执行ID
            clear_cache: 是否清除缓存
        
        Returns:
            是否成功
        """
        try:
            # 从Redis缓存删除
            if clear_cache:
                redis_client = await self._get_redis()
                if redis_client:
                    cache_key = f"{self._active_cache_prefix}{execution_id}"
                    await redis_client.delete(cache_key)
                    
                    # 从活跃执行列表移除
                    active_list_key = "workflow:active:list"
                    await redis_client.srem(active_list_key, execution_id)
            
            # 数据库中的状态保留在元数据中（不删除）
            logger.debug(f"State cache cleared for execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting state: {str(e)}", exc_info=True)
            return False
    
    async def get_active_executions(self) -> List[str]:
        """获取所有活跃执行ID列表"""
        try:
            redis_client = await self._get_redis()
            if redis_client:
                active_list_key = "workflow:active:list"
                execution_ids = await redis_client.smembers(active_list_key)
                return [eid.decode('utf-8') if isinstance(eid, bytes) else eid for eid in execution_ids]
            return []
        except Exception as e:
            logger.error(f"Error getting active executions: {str(e)}", exc_info=True)
            return []
    
    async def save_checkpoint(
        self,
        execution_id: str,
        checkpoint_name: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        保存检查点（用于断点续传）
        
        Args:
            execution_id: 执行ID
            checkpoint_name: 检查点名称
            state: 状态数据
            metadata: 检查点元数据
        
        Returns:
            是否成功
        """
        try:
            # 保存到数据库
            from ..repositories.execution_repository import ExecutionRepository
            execution_repo = ExecutionRepository(self.db)
            
            execution = execution_repo.get_by_id(execution_id)
            if execution:
                if execution.metadata is None:
                    execution.metadata = {}
                
                if "checkpoints" not in execution.metadata:
                    execution.metadata["checkpoints"] = {}
                
                execution.metadata["checkpoints"][checkpoint_name] = {
                    "state": state,
                    "metadata": metadata or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # 保存最新的检查点名称
                execution.metadata["latest_checkpoint"] = checkpoint_name
                
                self.db.commit()
                
                logger.info(f"Checkpoint saved: {execution_id}@{checkpoint_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving checkpoint: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    async def load_checkpoint(
        self,
        execution_id: str,
        checkpoint_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        加载检查点
        
        Args:
            execution_id: 执行ID
            checkpoint_name: 检查点名称，如果为None则加载最新检查点
        
        Returns:
            检查点数据（包含state和metadata），如果不存在则返回None
        """
        try:
            from ..repositories.execution_repository import ExecutionRepository
            execution_repo = ExecutionRepository(self.db)
            
            execution = execution_repo.get_by_id(execution_id)
            if execution and execution.metadata:
                checkpoints = execution.metadata.get("checkpoints", {})
                
                if checkpoint_name is None:
                    # 加载最新检查点
                    checkpoint_name = execution.metadata.get("latest_checkpoint")
                
                if checkpoint_name and checkpoint_name in checkpoints:
                    checkpoint_data = checkpoints[checkpoint_name]
                    logger.info(f"Checkpoint loaded: {execution_id}@{checkpoint_name}")
                    return checkpoint_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading checkpoint: {str(e)}", exc_info=True)
            return None
    
    async def list_checkpoints(self, execution_id: str) -> List[Dict[str, Any]]:
        """列出所有检查点"""
        try:
            from ..repositories.execution_repository import ExecutionRepository
            execution_repo = ExecutionRepository(self.db)
            
            execution = execution_repo.get_by_id(execution_id)
            if execution and execution.metadata:
                checkpoints = execution.metadata.get("checkpoints", {})
                return [
                    {
                        "name": name,
                        "timestamp": cp.get("timestamp"),
                        "metadata": cp.get("metadata", {})
                    }
                    for name, cp in checkpoints.items()
                ]
            return []
            
        except Exception as e:
            logger.error(f"Error listing checkpoints: {str(e)}", exc_info=True)
            return []
    
    async def resume_from_checkpoint(
        self,
        execution_id: str,
        checkpoint_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        从检查点恢复执行
        
        Args:
            execution_id: 执行ID
            checkpoint_name: 检查点名称，如果为None则使用最新检查点
        
        Returns:
            恢复的状态数据，如果失败则返回None
        """
        try:
            checkpoint = await self.load_checkpoint(execution_id, checkpoint_name)
            if checkpoint:
                state = checkpoint.get("state")
                if state:
                    # 恢复状态
                    await self.save_state(execution_id, state, is_active=True)
                    
                    # 更新执行记录
                    from ..repositories.execution_repository import ExecutionRepository
                    execution_repo = ExecutionRepository(self.db)
                    
                    execution = execution_repo.get_by_id(execution_id)
                    if execution:
                        from database.src.models.workflow_models import ExecutionStatus
                        execution.status = ExecutionStatus.RUNNING
                        if execution.metadata is None:
                            execution.metadata = {}
                        execution.metadata["resumed_from_checkpoint"] = checkpoint_name or "latest"
                        self.db.commit()
                    
                    logger.info(f"Execution resumed from checkpoint: {execution_id}@{checkpoint_name}")
                    return state
            
            return None
            
        except Exception as e:
            logger.error(f"Error resuming from checkpoint: {str(e)}", exc_info=True)
            self.db.rollback()
            return None

