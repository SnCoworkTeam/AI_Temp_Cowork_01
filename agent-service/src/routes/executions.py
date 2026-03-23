"""
执行管理路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging
from datetime import datetime
import uuid

from ..models.execution_models import (
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatus
)
from ..core.agent_manager import agent_manager
from ..core.state_manager import state_manager

router = APIRouter(prefix="/api/v1/executions", tags=["执行管理"])
logger = logging.getLogger(__name__)

# 内存存储（生产环境应使用数据库）
_executions: dict = {}


@router.post("", response_model=ExecutionResponse, summary="创建执行任务")
async def create_execution(request: ExecutionRequest):
    """
    创建执行任务

    - **agent_id**: 智能体ID
    - **task**: 任务描述
    - **context**: 上下文信息
    - **parameters**: 执行参数
    """
    try:
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        execution = ExecutionResponse(
            execution_id=execution_id,
            agent_id=request.agent_id,
            status=ExecutionStatus.PENDING,
            started_at=started_at,
        )

        _executions[execution_id] = execution

        # 异步执行（简化版本，实际应该使用后台任务）
        # 这里直接执行
        try:
            result = await agent_manager.execute_agent(
                request.agent_id,
                request.task,
                request.context,
                request.parameters
            )

            execution.status = ExecutionStatus.COMPLETED if result.get("success") else ExecutionStatus.FAILED
            execution.result = result
            execution.error_message = None if result.get("success") else result.get("error")
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)

        execution.completed_at = datetime.utcnow()
        if execution.completed_at and execution.started_at:
            execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()

        return execution
    except Exception as e:
        logger.error(f"Failed to create execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create execution: {str(e)}")


@router.get("/{execution_id}", response_model=ExecutionResponse, summary="获取执行详情")
async def get_execution(execution_id: str):
    """
    获取执行详情

    - **execution_id**: 执行ID
    """
    execution = _executions.get(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")
    return execution


@router.get("", response_model=List[ExecutionResponse], summary="获取执行列表")
async def list_executions(
    agent_id: str = None,
    status: ExecutionStatus = None,
    limit: int = 100,
    offset: int = 0
):
    """
    获取执行列表

    - **agent_id**: 智能体ID过滤（可选）
    - **status**: 状态过滤（可选）
    - **limit**: 限制数量（默认100）
    - **offset**: 偏移量（默认0）
    """
    executions = list(_executions.values())

    # 过滤
    if agent_id:
        executions = [e for e in executions if e.agent_id == agent_id]
    if status:
        executions = [e for e in executions if e.status == status]

    # 排序（按开始时间倒序）
    executions.sort(key=lambda x: x.started_at, reverse=True)

    # 分页
    return executions


@router.get("/intents", summary="获取意图历史")
async def list_intents(
    limit: int = 100,
    offset: int = 0
):
    """
    获取意图历史（从执行记录中提取）

    - **limit**: 限制数量（默认100）
    - **offset**: 偏移量（默认0）
    """
    try:
        # 从执行记录中提取意图信息
        executions = await state_manager.list_executions(limit=limit * 2, offset=0)  # 获取更多以聚合

        # 聚合意图信息
        intent_map = {}
        for execution in executions:
            intent_info = execution.get("metadata", {}).get("intent_analysis")
            if intent_info:
                intent_type = intent_info.get("task_type", "unknown")
                if intent_type not in intent_map:
                    intent_map[intent_type] = {
                        "intent_type": intent_type,
                        "usage_count": 0,
                        "total_confidence": 0.0,
                        "execution_strategies": {},
                        "target_services": {},
                        "required_tools": set()
                    }

                intent_data = intent_map[intent_type]
                intent_data["usage_count"] += 1
                intent_data["total_confidence"] += intent_info.get("confidence", 0.0)

                # 统计执行策略
                strategy = execution.get("metadata", {}).get("routing_decision", {}).get("strategy", "unknown")
                intent_data["execution_strategies"][strategy] = intent_data["execution_strategies"].get(strategy, 0) + 1

                # 统计目标服务
                target_service = execution.get("metadata", {}).get("routing_decision", {}).get("target_service")
                if target_service:
                    intent_data["target_services"][target_service] = intent_data["target_services"].get(target_service, 0) + 1

                # 收集所需工具
                required_tools = intent_info.get("required_tools", [])
                intent_data["required_tools"].update(required_tools)

        # 转换为列表并计算平均值
        intents = []
        for intent_type, data in intent_map.items():
            intents.append({
                "intent_type": intent_type,
                "usage_count": data["usage_count"],
                "average_confidence": data["total_confidence"] / data["usage_count"] if data["usage_count"] > 0 else 0.0,
                "execution_strategies": data["execution_strategies"],
                "target_services": data["target_services"],
                "required_tools": list(data["required_tools"]),
                "success_rate": 0.0  # TODO: 从执行结果计算
            })

        # 按使用频率排序
        intents.sort(key=lambda x: x["usage_count"], reverse=True)

        return intents[offset:offset + limit]

    except Exception as e:
        logger.error(f"Failed to list intents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list intents: {str(e)}")


@router.get("/patterns", summary="获取执行模式")
async def list_execution_patterns(
    task_type: str = None,
    limit: int = 100,
    offset: int = 0
):
    """
    获取执行模式（聚合的执行路径）

    - **task_type**: 任务类型过滤（可选）
    - **limit**: 限制数量（默认100）
    - **offset**: 偏移量（默认0）
    """
    try:
        # 从执行记录中提取执行模式
        executions = await state_manager.list_executions(limit=limit * 2, offset=0)

        # 按任务类型聚合执行路径
        pattern_map = {}
        for execution in executions:
            exec_metadata = execution.get("metadata", {})
            intent_info = exec_metadata.get("intent_analysis", {})
            routing_info = exec_metadata.get("routing_decision", {})

            exec_task_type = intent_info.get("task_type", "unknown")
            if task_type and exec_task_type != task_type:
                continue

            exec_strategy = routing_info.get("strategy", "unknown")
            exec_path = execution.get("execution_path", [])

            pattern_key = f"{exec_task_type}_{exec_strategy}"
            if pattern_key not in pattern_map:
                pattern_map[pattern_key] = {
                    "task_type": exec_task_type,
                    "execution_strategy": exec_strategy,
                    "usage_count": 0,
                    "execution_paths": [],
                    "used_services": set(),
                    "total_execution_time": 0.0,
                    "success_count": 0
                }

            pattern_data = pattern_map[pattern_key]
            pattern_data["usage_count"] += 1
            pattern_data["execution_paths"].append(exec_path)

            # 收集使用的服务
            used_services = execution.get("used_services", [])
            pattern_data["used_services"].update(used_services)

            # 累计执行时间
            exec_time = execution.get("execution_time", 0.0)
            if exec_time:
                pattern_data["total_execution_time"] += exec_time

            # 统计成功次数
            if execution.get("result") and execution.get("result", {}).get("success"):
                pattern_data["success_count"] += 1

        # 转换为列表
        patterns = []
        for pattern_key, data in pattern_map.items():
            patterns.append({
                "pattern_id": pattern_key,
                "pattern_name": f"{data['task_type']} - {data['execution_strategy']}",
                "task_type": data["task_type"],
                "execution_strategy": data["execution_strategy"],
                "usage_count": data["usage_count"],
                "execution_path": data["execution_paths"][0] if data["execution_paths"] else [],  # 使用第一个作为示例
                "used_services": list(data["used_services"]),
                "average_execution_time": data["total_execution_time"] / data["usage_count"] if data["usage_count"] > 0 else 0.0,
                "success_rate": data["success_count"] / data["usage_count"] if data["usage_count"] > 0 else 0.0
            })

        # 按使用频率排序
        patterns.sort(key=lambda x: x["usage_count"], reverse=True)

        return patterns[offset:offset + limit]

    except Exception as e:
        logger.error(f"Failed to list execution patterns: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list execution patterns: {str(e)}")[offset:offset + limit]

