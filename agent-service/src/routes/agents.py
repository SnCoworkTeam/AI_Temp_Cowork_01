"""
智能体管理路由
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List
from pydantic import BaseModel
import logging
import json

from ..models.agent_models import (
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentStatus,
    AgentCapability
)
from ..core.agent_manager import agent_manager
from ..services.metadata_client import metadata_client

router = APIRouter(prefix="/agents", tags=["智能体管理"])
logger = logging.getLogger(__name__)


class ExecuteAgentRequest(BaseModel):
    """执行智能体请求"""
    task: str
    context: dict = {}
    parameters: dict = {}
    stream: bool = False  # 是否流式输出


@router.post("", response_model=Agent, summary="创建智能体")
async def create_agent(agent_data: AgentCreate):
    """
    创建新智能体

    - **name**: 智能体名称
    - **description**: 智能体描述
    - **capabilities**: 能力列表
    - **system_prompt**: 系统提示词
    """
    try:
        agent = await agent_manager.create_agent(agent_data)
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get("", response_model=List[Agent], summary="获取智能体列表")
async def list_agents(
    status: AgentStatus = None,
    capability: AgentCapability = None,
    limit: int = 100,
    offset: int = 0
):
    """
    获取智能体列表

    - **status**: 状态过滤（可选）
    - **capability**: 能力过滤（可选）
    - **limit**: 限制数量（默认100）
    - **offset**: 偏移量（默认0）
    """
    try:
        agents = await agent_manager.list_agents(status, capability, limit, offset)
        return agents
    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/{agent_id}", response_model=Agent, summary="获取智能体详情")
async def get_agent(agent_id: str):
    """
    获取智能体详情

    - **agent_id**: 智能体ID
    """
    agent = await agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent


@router.put("/{agent_id}", response_model=Agent, summary="更新智能体")
async def update_agent(agent_id: str, agent_data: AgentUpdate):
    """
    更新智能体

    - **agent_id**: 智能体ID
    - **agent_data**: 更新数据
    """
    agent = await agent_manager.update_agent(agent_id, agent_data)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent


@router.delete("/{agent_id}", summary="删除智能体")
async def delete_agent(agent_id: str):
    """
    删除智能体

    - **agent_id**: 智能体ID
    """
    success = await agent_manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {"message": "Agent deleted successfully"}


@router.post("/{agent_id}/execute", summary="执行智能体")
async def execute_agent(
    agent_id: str,
    request: ExecuteAgentRequest
):
    """
    执行智能体

    - **agent_id**: 智能体ID
    - **task**: 任务描述
    - **context**: 上下文信息（可选）
    - **parameters**: 执行参数（可选）
    - **stream**: 是否流式输出（可选，默认False）
    """
    try:
        # 如果是流式输出
        if request.stream:
            async def generate_stream():
                try:
                    # 获取智能体信息
                    agent = await agent_manager.get_agent(agent_id)
                    if not agent:
                        error_msg = f'Agent not found: {agent_id}'
                        yield f"data: {json.dumps({'error': error_msg})}\n\n"
                        return

                    agent_config = agent.config or {}
                    agent_metadata = agent.metadata or {}
                    agent_type = agent_config.get("agent_type") or agent_metadata.get("integration_type")

                    # 如果是SSH智能体，使用流式输出
                    if agent_type == "server_operation" or agent_type == "ssh_executor":
                        from ..core.agents.server_operation_agent import ServerOperationAgent
                        import os

                        ssh_config = {
                            "host": os.getenv("SSH_HOST", "43.143.139.197"),
                            "username": os.getenv("SSH_USERNAME", "ubuntu"),
                            "private_key_path": os.getenv("SSH_PRIVATE_KEY_PATH", "/opt/enterprise-ai-platform/enterprise_ai_platform.pem"),
                            "base_workdir": os.getenv("SSH_BASE_WORKDIR", "/opt/enterprise-ai-platform"),
                            "port": int(os.getenv("SSH_PORT", "22")),
                            "connection_timeout": int(os.getenv("SSH_CONNECTION_TIMEOUT", "30"))
                        }

                        server_agent = ServerOperationAgent(
                            ssh_config=ssh_config,
                            agent_config=agent_config
                        )

                        # 流式生成计划
                        try:
                            stream_plan = await server_agent.generate_plan(
                                user_request=request.task,
                                context=request.context,
                                stream=True
                            )

                            # 检查是否是异步生成器
                            if hasattr(stream_plan, '__aiter__'):
                                async for chunk in stream_plan:
                                    if chunk:
                                        yield f"data: {json.dumps({'content': chunk, 'type': 'plan_generation'})}\n\n"
                            else:
                                # 如果不是生成器，直接发送
                                yield f"data: {json.dumps({'content': str(stream_plan), 'type': 'plan_generation'})}\n\n"
                        except Exception as plan_error:
                            logger.error(f"流式生成计划失败: {str(plan_error)}", exc_info=True)
                            yield f"data: {json.dumps({'error': f'生成计划失败: {str(plan_error)}', 'type': 'error'})}\n\n"
                            return

                        # 执行计划（如果需要）
                        if agent_config.get("auto_execute", True):
                            execution_start_msg = '\n\n开始执行计划...'
                            yield f"data: {json.dumps({'content': execution_start_msg, 'type': 'execution_start'})}\n\n"
                            result = await server_agent.process_request(
                                user_request=request.task,
                                project_id=request.context.get("project_id"),
                                context=request.context,
                                auto_execute=True
                            )

                            if "error" in result:
                                error_msg = f'执行失败: {result["error"]}'
                                yield f"data: {json.dumps({'content': error_msg, 'type': 'error'})}\n\n"
                            else:
                                execution_result = result.get("execution_result")
                                if execution_result:
                                    summary = execution_result.get("summary", "")
                                    complete_msg = f'执行完成: {summary}'
                                    yield f"data: {json.dumps({'content': complete_msg, 'type': 'execution_complete'})}\n\n"
                    else:
                        # 其他智能体暂不支持流式输出
                        result = await agent_manager.execute_agent(
                            agent_id,
                            request.task,
                            request.context,
                            request.parameters
                        )
                        result_content = str(result)
                        yield f"data: {json.dumps({'content': result_content, 'type': 'result'})}\n\n"
                except Exception as e:
                    logger.error(f"Stream execution failed: {str(e)}", exc_info=True)
                    error_content = str(e)
                    yield f"data: {json.dumps({'error': error_content, 'type': 'error'})}\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream"
            )
        else:
            # 非流式输出
            result = await agent_manager.execute_agent(
                agent_id,
                request.task,
                request.context,
                request.parameters
            )
            return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute agent: {str(e)}")


@router.post("/sync-to-metadata", summary="同步所有智能体到元数据服务")
async def sync_agents_to_metadata():
    """
    将现有所有智能体同步到metadata-service

    这个端点用于将已经创建的智能体同步到元数据服务，
    以便在元数据管理页面中查看。
    """
    try:
        # 获取所有智能体
        agents = await agent_manager.list_agents(limit=1000, offset=0)

        synced_count = 0
        failed_count = 0
        results = []

        for agent in agents:
            try:
                # 处理capabilities：可能是枚举对象或字符串
                def get_capability_value(cap):
                    if isinstance(cap, str):
                        return cap
                    elif hasattr(cap, 'value'):
                        return cap.value
                    else:
                        return str(cap)

                capabilities_list = [get_capability_value(cap) for cap in agent.capabilities]
                status_value = agent.status.value if hasattr(agent.status, 'value') else str(agent.status)

                # 注册为AI模型
                ai_model_result = await metadata_client.register_agent_as_ai_model(
                    agent.id,
                    agent.name,
                    agent.description,
                    capabilities_list,
                    agent.config or {},
                    agent.metadata or {},
                    status_value
                )

                # 注册为业务实体
                entity_result = await metadata_client.register_agent_as_business_entity(
                    agent.id,
                    agent.name,
                    agent.description,
                    capabilities_list,
                    agent.config or {},
                    agent.metadata or {},
                    status_value
                )

                if ai_model_result or entity_result:
                    synced_count += 1
                    results.append({
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "ai_model_synced": ai_model_result is not None,
                        "business_entity_synced": entity_result is not None
                    })
                else:
                    failed_count += 1
                    results.append({
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "error": "Failed to sync to metadata service"
                    })
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to sync agent {agent.id}: {e}", exc_info=True)
                results.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "error": str(e)
                })

        return {
            "message": f"Synced {synced_count} agents, {failed_count} failed",
            "total": len(agents),
            "synced": synced_count,
            "failed": failed_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to sync agents to metadata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to sync agents: {str(e)}")

