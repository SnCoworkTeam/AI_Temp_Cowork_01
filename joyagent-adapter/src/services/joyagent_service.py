"""
JoyAgent Client Service

Core service for interacting with JoyAgent-JDGenie backend and Python client.
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import httpx
import aioredis
from fastapi import HTTPException
import structlog

from ..config import settings, get_joyagent_base_url, get_joyagent_client_url, get_redis_url
from ..models import (
    JoyAgentTaskRequest,
    JoyAgentTaskResponse,
    TaskStatus,
    TaskType,
    AgentMode,
    JoyAgentCapability,
    JoyAgentStatus
)

logger = structlog.get_logger(__name__)


class JoyAgentClientService:
    """Service for managing JoyAgent tasks and communication"""

    def __init__(self):
        self.backend_url = get_joyagent_base_url()
        self.client_url = get_joyagent_client_url()
        self.redis_url = get_redis_url()
        self.redis_client: Optional[aioredis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the service"""
        try:
            # Initialize Redis connection
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

            # Initialize HTTP client with longer timeout for JoyAgent
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.joyagent_api_timeout),
                limits=httpx.Limits(max_connections=20)
            )

            # Test connections
            await self._health_check()

            logger.info("JoyAgent client service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize JoyAgent client service: {e}")
            raise

    async def shutdown(self):
        """Shutdown the service"""
        try:
            if self.http_client:
                await self.http_client.aclose()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("JoyAgent client service shut down successfully")
        except Exception as e:
            logger.error(f"Error during service shutdown: {e}")

    async def _health_check(self) -> bool:
        """Check JoyAgent service health"""
        try:
            # Check JoyAgent backend health
            response = await self.http_client.get(f"{self.backend_url}/health")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail=f"JoyAgent backend unhealthy: {response.status_code}"
                )

            # Check JoyAgent Python client health
            client_response = await self.http_client.get(f"{self.client_url}/health")
            if client_response.status_code != 200:
                logger.warning(f"JoyAgent Python client unhealthy: {client_response.status_code}")

            return True

        except Exception as e:
            logger.error(f"JoyAgent health check failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"JoyAgent service unavailable: {str(e)}"
            )

    async def create_task(self, task_request: JoyAgentTaskRequest) -> JoyAgentTaskResponse:
        """Create a new JoyAgent task"""
        try:
            task_id = str(uuid.uuid4())
            created_at = datetime.now()

            # Prepare JoyAgent request
            joyagent_payload = {
                "query": task_request.query,
                "mode": task_request.mode.value,
                "parameters": task_request.parameters or {},
                "context": task_request.context or {},
                "timeout": task_request.timeout
            }

            # Store task in Redis with expiration
            task_data = {
                "task_id": task_id,
                "status": TaskStatus.PENDING.value,
                "request": task_request.model_dump(),
                "created_at": created_at.isoformat(),
                "progress": 0
            }

            await self.redis_client.setex(
                f"joyagent:task:{task_id}",
                settings.context_ttl,
                json.dumps(task_data)
            )

            # Submit task to JoyAgent backend
            response = await self._submit_to_joyagent(task_id, joyagent_payload)

            # Update task status
            task_data["status"] = TaskStatus.RUNNING.value
            task_data["started_at"] = datetime.now().isoformat()
            task_data["joyagent_response"] = response

            await self.redis_client.setex(
                f"joyagent:task:{task_id}",
                settings.context_ttl,
                json.dumps(task_data)
            )

            # Add to active tasks for monitoring
            self.active_tasks[task_id] = task_data

            return JoyAgentTaskResponse(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                created_at=created_at,
                started_at=datetime.now(),
                progress=10
            )

        except Exception as e:
            logger.error(f"Failed to create JoyAgent task: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create task: {str(e)}"
            )

    async def _submit_to_joyagent(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit task to JoyAgent backend"""
        try:
            # Determine the best endpoint based on task type
            endpoint = "/api/agent/chat"  # Default JoyAgent chat endpoint

            response = await self.http_client.post(
                f"{self.backend_url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"JoyAgent API error: {response.text}"
                )

            return response.json()

        except httpx.RequestError as e:
            logger.error(f"JoyAgent request failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"JoyAgent service unavailable: {str(e)}"
            )

    async def get_task_status(self, task_id: str) -> JoyAgentTaskResponse:
        """Get task status and results"""
        try:
            # Get task data from Redis
            task_data_str = await self.redis_client.get(f"joyagent:task:{task_id}")
            if not task_data_str:
                raise HTTPException(
                    status_code=404,
                    detail=f"Task {task_id} not found"
                )

            task_data = json.loads(task_data_str)

            # Check if task is still running and update status
            if task_data["status"] == TaskStatus.RUNNING.value:
                updated_task = await self._check_task_progress(task_id, task_data)
                task_data.update(updated_task)

            # Convert to response model
            return JoyAgentTaskResponse(
                task_id=task_data["task_id"],
                status=TaskStatus(task_data["status"]),
                result=task_data.get("result"),
                error=task_data.get("error"),
                progress=task_data.get("progress", 0),
                created_at=datetime.fromisoformat(task_data["created_at"]),
                started_at=datetime.fromisoformat(task_data["started_at"]) if task_data.get("started_at") else None,
                completed_at=datetime.fromisoformat(task_data["completed_at"]) if task_data.get("completed_at") else None,
                execution_time=task_data.get("execution_time")
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get task status: {str(e)}"
            )

    async def _check_task_progress(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check task progress with JoyAgent"""
        try:
            # This would typically poll JoyAgent's status endpoint
            # For now, we'll simulate progress checking

            # Check if task has been running too long
            created_at = datetime.fromisoformat(task_data["created_at"])
            elapsed = (datetime.now() - created_at).total_seconds()

            if elapsed > settings.task_timeout:
                # Task timeout
                updated_data = {
                    "status": TaskStatus.FAILED.value,
                    "error": "Task timeout",
                    "completed_at": datetime.now().isoformat(),
                    "execution_time": elapsed
                }

                # Update in Redis
                task_data.update(updated_data)
                await self.redis_client.setex(
                    f"joyagent:task:{task_id}",
                    settings.context_ttl,
                    json.dumps(task_data)
                )

                return updated_data

            # Simulate progress update (in real implementation, this would check JoyAgent status)
            progress = min(90, task_data.get("progress", 0) + 10)

            # Simulate completion for demo (remove this in production)
            if progress >= 90 and elapsed > 30:  # Complete after 30 seconds for demo
                result = {
                    "type": "text",
                    "content": f"JoyAgent completed task: {task_data['request']['query']}",
                    "metadata": {
                        "task_type": task_data['request'].get('task_type', 'query'),
                        "mode": task_data['request'].get('mode', 'auto'),
                        "generated_at": datetime.now().isoformat()
                    }
                }

                updated_data = {
                    "status": TaskStatus.COMPLETED.value,
                    "result": result,
                    "progress": 100,
                    "completed_at": datetime.now().isoformat(),
                    "execution_time": elapsed
                }
            else:
                updated_data = {
                    "progress": progress
                }

            # Update in Redis
            task_data.update(updated_data)
            await self.redis_client.setex(
                f"joyagent:task:{task_id}",
                settings.context_ttl,
                json.dumps(task_data)
            )

            return updated_data

        except Exception as e:
            logger.error(f"Failed to check task progress: {e}")
            return {"error": f"Progress check failed: {str(e)}"}

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        try:
            task_data_str = await self.redis_client.get(f"joyagent:task:{task_id}")
            if not task_data_str:
                raise HTTPException(
                    status_code=404,
                    detail=f"Task {task_id} not found"
                )

            task_data = json.loads(task_data_str)

            if task_data["status"] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Task {task_id} already completed"
                )

            # Update task status to cancelled
            task_data.update({
                "status": TaskStatus.CANCELLED.value,
                "completed_at": datetime.now().isoformat(),
                "error": "Task cancelled by user"
            })

            await self.redis_client.setex(
                f"joyagent:task:{task_id}",
                settings.context_ttl,
                json.dumps(task_data)
            )

            # Remove from active tasks
            self.active_tasks.pop(task_id, None)

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cancel task: {str(e)}"
            )

    async def list_tasks(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """List all tasks with pagination"""
        try:
            # Get all task keys from Redis
            keys = await self.redis_client.keys("joyagent:task:*")

            # Calculate pagination
            total = len(keys)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            # Get tasks for current page
            page_keys = keys[start_idx:end_idx]
            tasks = []

            for key in page_keys:
                task_data_str = await self.redis_client.get(key)
                if task_data_str:
                    task_data = json.loads(task_data_str)

                    task_response = JoyAgentTaskResponse(
                        task_id=task_data["task_id"],
                        status=TaskStatus(task_data["status"]),
                        result=task_data.get("result"),
                        error=task_data.get("error"),
                        progress=task_data.get("progress", 0),
                        created_at=datetime.fromisoformat(task_data["created_at"]),
                        started_at=datetime.fromisoformat(task_data["started_at"]) if task_data.get("started_at") else None,
                        completed_at=datetime.fromisoformat(task_data["completed_at"]) if task_data.get("completed_at") else None,
                        execution_time=task_data.get("execution_time")
                    )

                    tasks.append(task_response)

            return {
                "tasks": tasks,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_next": end_idx < total
            }

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list tasks: {str(e)}"
            )

    async def get_service_status(self) -> JoyAgentStatus:
        """Get JoyAgent service status and capabilities"""
        try:
            await self._health_check()

            # Get service information
            uptime = 0  # TODO: Calculate actual uptime
            active_task_count = len(self.active_tasks)

            # Get total tasks from Redis
            keys = await self.redis_client.keys("joyagent:task:*")
            total_task_count = len(keys)

            # Define available capabilities
            capabilities = [
                JoyAgentCapability(
                    name="Query Processing",
                    description="Process natural language queries",
                    type=TaskType.QUERY,
                    enabled=True
                ),
                JoyAgentCapability(
                    name="Report Generation",
                    description="Generate analytical reports",
                    type=TaskType.REPORT_GENERATION,
                    enabled=True
                ),
                JoyAgentCapability(
                    name="Code Generation",
                    description="Generate and analyze code",
                    type=TaskType.CODE_GENERATION,
                    enabled=True
                ),
                JoyAgentCapability(
                    name="PPT Generation",
                    description="Create PowerPoint presentations",
                    type=TaskType.PPT_GENERATION,
                    enabled=True
                ),
                JoyAgentCapability(
                    name="Data Analysis",
                    description="Analyze data and generate insights",
                    type=TaskType.DATA_ANALYSIS,
                    enabled=True
                )
            ]

            return JoyAgentStatus(
                service_name="JoyAgent-JDGenie Adapter",
                status="healthy",
                version="1.0.0",
                uptime=uptime,
                active_tasks=active_task_count,
                total_tasks=total_task_count,
                capabilities=capabilities,
                last_health_check=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get service status: {str(e)}"
            )


# Create global service instance
joyagent_service = JoyAgentClientService()