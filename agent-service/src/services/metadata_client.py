"""
元数据服务客户端
用于将智能体注册到metadata-service
"""
import logging
import httpx
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MetadataClient:
    """元数据服务客户端"""
    
    def __init__(self):
        self.base_url = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")
        self.timeout = 30.0
    
    async def register_agent_as_business_entity(
        self,
        agent_id: str,
        agent_name: str,
        agent_description: str,
        capabilities: list,
        config: Dict[str, Any],
        metadata: Dict[str, Any],
        status: str = "active"
    ) -> Optional[Dict[str, Any]]:
        """
        将智能体注册为业务实体元数据
        
        Args:
            agent_id: 智能体ID
            agent_name: 智能体名称
            agent_description: 智能体描述
            capabilities: 能力列表
            config: 配置信息
            metadata: 元数据
            status: 状态
            
        Returns:
            注册结果，如果失败返回None
        """
        try:
            # 构建业务实体元数据
            # 使用"concept"作为entity_type，因为"agent"不在允许的枚举值中
            # 注意：枚举值必须是小写，与数据库枚举类型匹配
            entity_data = {
                "name": f"agent_{agent_id}",
                "display_name": agent_name,
                "description": agent_description,
                "entity_type": "concept",  # 使用concept类型（小写），因为agent不在允许的枚举值中
                "business_definition": f"智能体：{agent_name}，能力：{', '.join(capabilities)}",
                "tags": ["agent", f"agent:{agent_id}"] + [f"capability:{cap}" for cap in capabilities],
                "metadata": {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "capabilities": capabilities,
                    "config": config,
                    "agent_metadata": metadata,
                    "status": status,
                    "source": "agent-service"
                }
            }
            
            # 如果有MCP工具集成，添加到元数据
            if config.get("use_tool_integration"):
                entity_data["metadata"]["mcp_integration"] = {
                    "enabled": True,
                    "preferred_tools": config.get("preferred_tools", []),
                    "mcp_server": metadata.get("mcp_server"),
                    "mcp_server_project": metadata.get("mcp_server_project")
                }
            
            # 调用metadata-service API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 先尝试查询是否已存在
                check_response = await client.get(
                    f"{self.base_url}/api/business-entities",
                    params={"name": f"agent_{agent_id}"}
                )
                
                if check_response.status_code == 200:
                    existing_entities = check_response.json()
                    if isinstance(existing_entities, list) and len(existing_entities) > 0:
                        # 已存在，执行更新
                        entity_id = existing_entities[0].get('id')
                        update_response = await client.put(
                            f"{self.base_url}/api/business-entities/{entity_id}",
                            json=entity_data
                        )
                        if update_response.status_code in [200, 201]:
                            result = update_response.json()
                            logger.info(f"Updated existing agent {agent_id} as business entity: {result.get('id')}")
                            return result
                        else:
                            logger.warning(f"Failed to update agent {agent_id}: {update_response.status_code}")
                
                # 不存在或更新失败，执行创建
                response = await client.post(
                    f"{self.base_url}/api/business-entities",
                    json=entity_data
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    logger.info(f"Successfully registered agent {agent_id} as business entity: {result.get('id')}")
                    return result
                elif response.status_code == 409:  # Conflict - 重复键
                    # 如果是409错误，尝试更新
                    logger.info(f"Agent {agent_id} already exists, attempting update...")
                    # 重新查询并更新
                    check_response = await client.get(
                        f"{self.base_url}/api/business-entities",
                        params={"name": f"agent_{agent_id}"}
                    )
                    if check_response.status_code == 200:
                        existing_entities = check_response.json()
                        if isinstance(existing_entities, list) and len(existing_entities) > 0:
                            entity_id = existing_entities[0].get('id')
                            update_response = await client.put(
                                f"{self.base_url}/api/business-entities/{entity_id}",
                                json=entity_data
                            )
                            if update_response.status_code in [200, 201]:
                                result = update_response.json()
                                logger.info(f"Updated agent {agent_id} as business entity: {result.get('id')}")
                                return result
                    logger.warning(
                        f"Failed to register/update agent {agent_id} as business entity: "
                        f"{response.status_code} - {response.text}"
                    )
                    return None
                else:
                    logger.warning(
                        f"Failed to register agent {agent_id} as business entity: "
                        f"{response.status_code} - {response.text}"
                    )
                    return None
                    
        except Exception as e:
            logger.error(f"Error registering agent {agent_id} as business entity: {e}", exc_info=True)
            return None
    
    async def register_agent_as_ai_model(
        self,
        agent_id: str,
        agent_name: str,
        agent_description: str,
        capabilities: list,
        config: Dict[str, Any],
        metadata: Dict[str, Any],
        status: str = "active"
    ) -> Optional[Dict[str, Any]]:
        """
        将智能体注册为AI模型元数据
        
        Args:
            agent_id: 智能体ID
            agent_name: 智能体名称
            agent_description: 智能体描述
            capabilities: 能力列表
            config: 配置信息
            metadata: 元数据
            status: 状态
            
        Returns:
            注册结果，如果失败返回None
        """
        try:
            # 构建AI模型元数据
            # 注意：枚举值必须是小写，与数据库枚举类型匹配
            ai_model_data = {
                "name": f"agent_{agent_id}",
                "display_name": agent_name,
                "description": agent_description,
                "model_type": "llm",  # 智能体使用LLM（小写）
                "status": status.lower() if isinstance(status, str) else status,  # 确保状态是小写
                "framework": "agent-service",
                "model_version": metadata.get("version", "1.0.0"),
                "deployment_endpoint": f"/api/v1/agents/{agent_id}/execute",
                "tags": [f"agent:{agent_id}", "agent"] + [f"capability:{cap}" for cap in capabilities],
                "use_cases": capabilities,
                "metadata": {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "capabilities": capabilities,
                    "config": config,
                    "agent_metadata": metadata,
                    "source": "agent-service"
                }
            }
            
            # 如果有MCP工具集成，添加到元数据
            if config.get("use_tool_integration"):
                ai_model_data["metadata"]["mcp_integration"] = {
                    "enabled": True,
                    "preferred_tools": config.get("preferred_tools", []),
                    "mcp_server": metadata.get("mcp_server"),
                    "mcp_server_project": metadata.get("mcp_server_project")
                }
            
            # 调用metadata-service API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/ai-models",
                    json=ai_model_data
                )
                
                # 先尝试查询是否已存在
                check_response = await client.get(
                    f"{self.base_url}/api/ai-models",
                    params={"name": f"agent_{agent_id}"}
                )
                
                if check_response.status_code == 200:
                    existing_models = check_response.json()
                    if isinstance(existing_models, list) and len(existing_models) > 0:
                        # 已存在，执行更新
                        model_id = existing_models[0].get('id')
                        update_response = await client.put(
                            f"{self.base_url}/api/ai-models/{model_id}",
                            json=ai_model_data
                        )
                        if update_response.status_code in [200, 201]:
                            result = update_response.json()
                            logger.info(f"Updated existing agent {agent_id} as AI model: {result.get('id')}")
                            return result
                        else:
                            logger.warning(f"Failed to update agent {agent_id}: {update_response.status_code}")
                
                # 不存在或更新失败，执行创建
                response = await client.post(
                    f"{self.base_url}/api/ai-models",
                    json=ai_model_data
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    logger.info(f"Successfully registered agent {agent_id} as AI model: {result.get('id')}")
                    return result
                elif response.status_code == 409:  # Conflict - 重复键
                    # 如果是409错误，尝试更新
                    logger.info(f"Agent {agent_id} already exists, attempting update...")
                    # 重新查询并更新
                    check_response = await client.get(
                        f"{self.base_url}/api/ai-models",
                        params={"name": f"agent_{agent_id}"}
                    )
                    if check_response.status_code == 200:
                        existing_models = check_response.json()
                        if isinstance(existing_models, list) and len(existing_models) > 0:
                            model_id = existing_models[0].get('id')
                            update_response = await client.put(
                                f"{self.base_url}/api/ai-models/{model_id}",
                                json=ai_model_data
                            )
                            if update_response.status_code in [200, 201]:
                                result = update_response.json()
                                logger.info(f"Updated agent {agent_id} as AI model: {result.get('id')}")
                                return result
                    logger.warning(
                        f"Failed to register/update agent {agent_id} as AI model: "
                        f"{response.status_code} - {response.text}"
                    )
                    return None
                else:
                    logger.warning(
                        f"Failed to register agent {agent_id} as AI model: "
                        f"{response.status_code} - {response.text}"
                    )
                    return None
                    
        except Exception as e:
            logger.error(f"Error registering agent {agent_id} as AI model: {e}", exc_info=True)
            return None
    
    async def update_agent_metadata(
        self,
        agent_id: str,
        agent_name: str,
        agent_description: str,
        capabilities: list,
        config: Dict[str, Any],
        metadata: Dict[str, Any],
        status: str = "active"
    ) -> Optional[Dict[str, Any]]:
        """
        更新智能体的AI模型元数据
        
        Args:
            agent_id: 智能体ID
            agent_name: 智能体名称
            agent_description: 智能体描述
            capabilities: 能力列表
            config: 配置信息
            metadata: 元数据
            status: 状态
            
        Returns:
            更新结果，如果失败返回None
        """
        try:
            # 首先查找对应的AI模型（通过metadata中的agent_id）
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 搜索包含该agent_id的AI模型
                search_response = await client.get(
                    f"{self.base_url}/api/ai-models",
                    params={"search": agent_id, "limit": 100}
                )
                
                if search_response.status_code == 200:
                    models = search_response.json()
                    # 查找匹配的模型
                    target_model = None
                    for model in models:
                        if (isinstance(model, dict) and 
                            model.get("metadata", {}).get("agent_id") == agent_id):
                            target_model = model
                            break
                    
                    if target_model:
                        model_id = target_model["id"]
                        
                        # 构建更新数据
                        update_data = {
                            "display_name": agent_name,
                            "description": agent_description,
                            "status": status,
                            "tags": [f"agent:{agent_id}", "agent"] + [f"capability:{cap}" for cap in capabilities],
                            "use_cases": capabilities,
                            "metadata": {
                                "agent_id": agent_id,
                                "agent_name": agent_name,
                                "capabilities": capabilities,
                                "config": config,
                                "agent_metadata": metadata,
                                "source": "agent-service"
                            }
                        }
                        
                        # 如果有MCP工具集成，添加到元数据
                        if config.get("use_tool_integration"):
                            update_data["metadata"]["mcp_integration"] = {
                                "enabled": True,
                                "preferred_tools": config.get("preferred_tools", []),
                                "mcp_server": metadata.get("mcp_server"),
                                "mcp_server_project": metadata.get("mcp_server_project")
                            }
                        
                        # 更新AI模型
                        update_response = await client.put(
                            f"{self.base_url}/api/ai-models/{model_id}",
                            json=update_data
                        )
                        
                        if update_response.status_code == 200:
                            result = update_response.json()
                            logger.info(f"Successfully updated agent {agent_id} metadata: {result.get('id')}")
                            return result
                        else:
                            logger.warning(
                                f"Failed to update agent {agent_id} metadata: "
                                f"{update_response.status_code} - {update_response.text}"
                            )
                            return None
                    else:
                        # 如果找不到，尝试创建
                        logger.info(f"AI model for agent {agent_id} not found, creating new one")
                        return await self.register_agent_as_ai_model(
                            agent_id, agent_name, agent_description,
                            capabilities, config, metadata, status
                        )
                else:
                    logger.warning(f"Failed to search AI models: {search_response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error updating agent {agent_id} metadata: {e}", exc_info=True)
            return None
    
    async def save_conversation_metadata(
        self,
        user_input: str,
        ai_response: str,
        intent_analysis: Dict[str, Any],
        routing_decision: Dict[str, Any],
        execution_metadata: Dict[str, Any],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        保存对话元数据到metadata-service
        
        将用户问题和AI回复保存为业务实体，用于后续意图识别训练
        
        Args:
            user_input: 用户输入
            ai_response: AI回复
            intent_analysis: 意图分析结果
            routing_decision: 路由决策
            execution_metadata: 执行元数据
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            保存结果，如果失败返回None
        """
        try:
            # 构建对话元数据作为业务实体
            # 使用entity_type="conversation"来标识对话记录
            conversation_data = {
                "name": f"conversation_{execution_metadata.get('execution_timestamp', '').replace(':', '-').split('.')[0]}",
                "display_name": f"对话记录 - {user_input[:50]}{'...' if len(user_input) > 50 else ''}",
                "description": f"用户问题: {user_input}\n\nAI回复: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}",
                "entity_type": "conversation",
                "business_definition": f"用户与AI助手的对话记录，用于意图识别和模式分析",
                "tags": [
                    "conversation",
                    "intent_training",
                    intent_analysis.get("task_type", "unknown"),
                    routing_decision.get("strategy", "unknown")
                ],
                "metadata": {
                    "user_input": user_input,
                    "ai_response": ai_response,
                    "intent_analysis": intent_analysis,
                    "routing_decision": routing_decision,
                    "execution_metadata": execution_metadata,
                    "session_id": session_id,
                    "user_id": user_id,
                    "timestamp": execution_metadata.get("execution_timestamp"),
                    "execution_time_seconds": execution_metadata.get("execution_time_seconds"),
                    "success": execution_metadata.get("success", True)
                }
            }
            
            # 调用metadata-service API保存为业务实体
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/business-entities",
                    json=conversation_data
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    logger.info(f"Successfully saved conversation metadata: {result.get('id')}")
                    return result
                else:
                    logger.warning(
                        f"Failed to save conversation metadata: "
                        f"{response.status_code} - {response.text}"
                    )
                    return None
                    
        except Exception as e:
            logger.error(f"Error saving conversation metadata: {e}", exc_info=True)
            return None
    
    async def get_realtime_metadata(
        self,
        user_input: str,
        context: Dict[str, Any],
        use_cache: bool = True,
        limit_per_type: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        获取实时元数据
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            use_cache: 是否使用缓存
            limit_per_type: 每种类型的返回数量限制
            
        Returns:
            元数据查询结果
        """
        try:
            url = f"{self.base_url}/api/v1/metadata/realtime-query"  # realtime_metadata使用v1前缀
            payload = {
                "user_input": user_input,
                "context": context,
                "use_cache": use_cache,
                "limit_per_type": limit_per_type
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.debug(f"Successfully retrieved realtime metadata for: {user_input[:50]}")
                    return result
                else:
                    logger.warning(
                        f"Failed to get realtime metadata: "
                        f"{response.status_code} - {response.text}"
                    )
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting realtime metadata: {e}", exc_info=True)
            return None


# 创建全局实例
metadata_client = MetadataClient()

