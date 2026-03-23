"""
状态管理器
跟踪执行状态，管理执行记录
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ExecutionState(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StateManager:
    """状态管理器"""
    
    def __init__(self):
        # 内存存储（生产环境应使用Redis或数据库）
        self._executions: Dict[str, Dict[str, Any]] = {}
    
    async def create_execution(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建执行记录
        
        Args:
            task: 任务描述
            context: 上下文信息
            metadata: 元数据
            
        Returns:
            执行ID
        """
        execution_id = str(uuid.uuid4())
        
        execution_record = {
            "execution_id": execution_id,
            "task": task,
            "context": context or {},
            "metadata": metadata or {},
            "state": ExecutionState.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "steps": [],
            "result": None,
            "error": None
        }
        
        self._executions[execution_id] = execution_record
        logger.info(f"Created execution record: {execution_id}")
        
        return execution_id
    
    async def update_execution_state(
        self,
        execution_id: str,
        state: ExecutionState,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        更新执行状态
        
        Args:
            execution_id: 执行ID
            state: 新状态
            result: 执行结果
            error: 错误信息
            
        Returns:
            是否成功
        """
        if execution_id not in self._executions:
            logger.warning(f"Execution not found: {execution_id}")
            return False
        
        execution = self._executions[execution_id]
        execution["state"] = state.value
        execution["updated_at"] = datetime.utcnow().isoformat()
        
        if result:
            execution["result"] = result
        
        if error:
            execution["error"] = error
        
        logger.info(f"Updated execution {execution_id} state to {state.value}")
        return True
    
    async def add_execution_step(
        self,
        execution_id: str,
        step_name: str,
        step_result: Dict[str, Any]
    ) -> bool:
        """
        添加执行步骤
        
        Args:
            execution_id: 执行ID
            step_name: 步骤名称
            step_result: 步骤结果
            
        Returns:
            是否成功
        """
        if execution_id not in self._executions:
            logger.warning(f"Execution not found: {execution_id}")
            return False
        
        execution = self._executions[execution_id]
        step = {
            "name": step_name,
            "result": step_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        execution["steps"].append(step)
        execution["updated_at"] = datetime.utcnow().isoformat()
        
        return True
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        获取执行记录
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行记录
        """
        return self._executions.get(execution_id)
    
    async def list_executions(
        self,
        limit: int = 100,
        offset: int = 0,
        state: Optional[ExecutionState] = None
    ) -> list:
        """
        列出执行记录
        
        Args:
            limit: 限制数量
            offset: 偏移量
            state: 状态过滤
            
        Returns:
            执行记录列表
        """
        executions = list(self._executions.values())
        
        # 状态过滤
        if state:
            executions = [e for e in executions if e.get("state") == state.value]
        
        # 按更新时间排序
        executions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # 分页
        return executions[offset:offset + limit]
    
    async def store_to_knowledge_base(
        self,
        execution_id: str
    ) -> bool:
        """
        将执行记录存储到知识库
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否成功
        """
        execution = await self.get_execution(execution_id)
        if not execution:
            return False
        
        try:
            from ..services.knowledge_client import knowledge_client
            
            success = await knowledge_client.store_execution_record(
                execution_id=execution_id,
                task=execution.get("task", ""),
                result=execution.get("result", {}),
                metadata={
                    "execution_id": execution_id,
                    "state": execution.get("state"),
                    "created_at": execution.get("created_at"),
                    "steps_count": len(execution.get("steps", []))
                }
            )
            
            if success:
                logger.info(f"Stored execution {execution_id} to knowledge base")
            
            return success
        except Exception as e:
            logger.error(f"Failed to store execution to knowledge base: {e}")
            return False


# 全局状态管理器实例
state_manager = StateManager()




