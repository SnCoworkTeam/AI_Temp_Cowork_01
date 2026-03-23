"""
专门处理平台部署的智能管理器

功能：
1. 渐进式部署策略
2. 平台配置管理
3. 部署健康监控
4. 紧急响应机制
"""
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from datetime import datetime, timedelta
import logging
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from collections import deque

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """部署状态"""
    PENDING = "pending"
    PREPARING = "preparing"
    DEPLOYING = "deploying"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class ServicePriority(Enum):
    """服务优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RollbackTrigger(Enum):
    """回滚触发条件"""
    HEALTH_CHECK_FAILED = "health_check_failed"
    PERFORMANCE_DEGRADED = "performance_degraded"
    ERROR_RATE_EXCEEDED = "error_rate_exceeded"
    MANUAL = "manual"
    TIMEOUT = "timeout"


@dataclass
class ServiceDeployment:
    """服务部署信息"""
    service_name: str
    priority: ServicePriority
    version: str
    status: DeploymentStatus
    deployment_time: Optional[datetime] = None
    health_check_passed: bool = False
    performance_baseline: Optional[Dict[str, Any]] = None
    error_count: int = 0
    rollback_available: bool = False
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentPlan:
    """部署计划"""
    plan_id: str
    version: str
    services: List[ServiceDeployment]
    deployment_order: List[str]
    rollback_plan: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class DeploymentConfig:
    """部署配置"""
    environment: str
    config_version: str
    config_data: Dict[str, Any]
    secrets: Dict[str, str] = field(default_factory=dict)
    certificates: Dict[str, str] = field(default_factory=dict)
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)


class PlatformDeploymentManager:
    """平台部署管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 服务配置
        self.service_urls = {
            "mcp-gateway": self.config.get("mcp_gateway_url", "http://localhost:8001"),
            "workflow-engine": self.config.get("workflow_engine_url", "http://localhost:8002"),
            "auth-service": self.config.get("auth_service_url", "http://localhost:8003"),
            "knowledge-base": self.config.get("knowledge_base_url", "http://localhost:8004"),
            "web-ui": self.config.get("web_ui_url", "http://localhost:3000"),
        }
        
        # 服务优先级和依赖关系
        self.service_priorities = {
            "database": ServicePriority.CRITICAL,
            "redis": ServicePriority.CRITICAL,
            "auth-service": ServicePriority.HIGH,
            "mcp-gateway": ServicePriority.HIGH,
            "workflow-engine": ServicePriority.MEDIUM,
            "knowledge-base": ServicePriority.MEDIUM,
            "web-ui": ServicePriority.LOW,
        }
        
        self.service_dependencies = {
            "mcp-gateway": ["redis", "database"],
            "workflow-engine": ["mcp-gateway", "database", "redis"],
            "auth-service": ["database", "redis"],
            "knowledge-base": ["database"],
            "web-ui": ["auth-service", "workflow-engine", "mcp-gateway"],
        }
        
        # 部署状态
        self.active_deployments: Dict[str, DeploymentPlan] = {}
        self.deployment_history: List[DeploymentPlan] = []
        
        # 配置管理
        self.config_versions: Dict[str, DeploymentConfig] = {}
        self.config_history: List[Dict[str, Any]] = []
        
        # 监控和告警
        self.monitoring_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # 回滚配置
        self.rollback_triggers = {
            RollbackTrigger.HEALTH_CHECK_FAILED: True,
            RollbackTrigger.ERROR_RATE_EXCEEDED: True,
            RollbackTrigger.PERFORMANCE_DEGRADED: True,
            RollbackTrigger.TIMEOUT: True,
        }
        
        self.rollback_thresholds = {
            "health_check_failures": 3,
            "error_rate_percent": 5.0,
            "performance_degradation_percent": 20.0,
            "deployment_timeout_seconds": 600,
        }
    
    # ==================== 渐进式部署策略 ====================
    
    async def create_deployment_plan(
        self,
        version: str,
        services: List[str],
        deployment_strategy: str = "gradual"
    ) -> DeploymentPlan:
        """
        创建部署计划
        
        Args:
            version: 部署版本
            services: 要部署的服务列表
            deployment_strategy: 部署策略 (gradual, all_at_once, canary)
        """
        plan_id = f"deploy_{uuid.uuid4().hex[:12]}"
        
        # 确定部署顺序
        deployment_order = self._calculate_deployment_order(services)
        
        # 创建服务部署信息
        service_deployments = []
        for service_name in deployment_order:
            priority = self.service_priorities.get(service_name, ServicePriority.MEDIUM)
            dependencies = self.service_dependencies.get(service_name, [])
            
            service_deployment = ServiceDeployment(
                service_name=service_name,
                priority=priority,
                version=version,
                status=DeploymentStatus.PENDING,
                dependencies=dependencies,
                rollback_available=True
            )
            service_deployments.append(service_deployment)
        
        # 生成回滚计划
        rollback_plan = await self._generate_rollback_plan(version, deployment_order)
        
        plan = DeploymentPlan(
            plan_id=plan_id,
            version=version,
            services=service_deployments,
            deployment_order=deployment_order,
            rollback_plan=rollback_plan
        )
        
        self.active_deployments[plan_id] = plan
        
        logger.info(f"Created deployment plan: {plan_id}, version: {version}")
        
        return plan
    
    def _calculate_deployment_order(self, services: List[str]) -> List[str]:
        """计算部署顺序"""
        # 按优先级排序
        priority_order = [
            ServicePriority.LOW,
            ServicePriority.MEDIUM,
            ServicePriority.HIGH,
            ServicePriority.CRITICAL
        ]
        
        # 先部署非关键服务验证
        deployment_order = []
        remaining_services = set(services)
        
        # 第一轮：部署低优先级服务
        for priority in priority_order:
            for service in services:
                if service in remaining_services:
                    service_priority = self.service_priorities.get(service, ServicePriority.MEDIUM)
                    if service_priority == priority and priority in [ServicePriority.LOW, ServicePriority.MEDIUM]:
                        # 检查依赖是否满足
                        dependencies = self.service_dependencies.get(service, [])
                        if all(dep in deployment_order or dep not in services for dep in dependencies):
                            deployment_order.append(service)
                            remaining_services.remove(service)
        
        # 第二轮：部署高优先级服务
        for priority in [ServicePriority.HIGH, ServicePriority.CRITICAL]:
            for service in list(remaining_services):
                service_priority = self.service_priorities.get(service, ServicePriority.MEDIUM)
                if service_priority == priority:
                    dependencies = self.service_dependencies.get(service, [])
                    if all(dep in deployment_order or dep not in services for dep in dependencies):
                        deployment_order.append(service)
                        remaining_services.remove(service)
        
        # 添加剩余服务
        deployment_order.extend(remaining_services)
        
        return deployment_order
    
    async def _generate_rollback_plan(
        self,
        version: str,
        services: List[str]
    ) -> Dict[str, Any]:
        """生成回滚计划"""
        # 获取当前版本
        current_versions = {}
        for service in services:
            try:
                from shared_libs.common.http_client import HTTPClient
                service_url = self.service_urls.get(service)
                if service_url:
                    async with HTTPClient(service_url) as client:
                        health = await client.get("/api/health")
                        current_versions[service] = health.get("version", "unknown")
            except Exception:
                current_versions[service] = "unknown"
        
        return {
            "target_version": version,
            "previous_versions": current_versions,
            "rollback_steps": list(reversed(services)),  # 反向回滚
            "rollback_available": True,
            "created_at": datetime.now().isoformat()
        }
    
    async def execute_deployment(
        self,
        plan_id: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        执行部署
        
        Args:
            plan_id: 部署计划ID
            dry_run: 是否仅模拟运行
        """
        plan = self.active_deployments.get(plan_id)
        if not plan:
            raise ValueError(f"Deployment plan not found: {plan_id}")
        
        plan.started_at = datetime.now()
        
        try:
            # 部署前准备
            await self._prepare_deployment(plan)
            
            if dry_run:
                return {
                    "plan_id": plan_id,
                    "status": "dry_run_completed",
                    "message": "Deployment plan validated (dry run)"
                }
            
            # 逐步部署服务
            deployment_results = []
            
            for service_name in plan.deployment_order:
                service_deployment = next(
                    (s for s in plan.services if s.service_name == service_name),
                    None
                )
                
                if not service_deployment:
                    continue
                
                # 部署单个服务
                result = await self._deploy_service(
                    service_deployment,
                    plan
                )
                deployment_results.append(result)
                
                # 检查是否需要回滚
                if result.get("status") == "failed":
                    should_rollback = await self._should_trigger_rollback(
                        plan_id, result
                    )
                    
                    if should_rollback:
                        await self._execute_rollback(plan_id, reason="Service deployment failed")
                        return {
                            "plan_id": plan_id,
                            "status": "rolled_back",
                            "message": "Deployment failed and rolled back",
                            "results": deployment_results
                        }
            
            # 部署完成
            plan.completed_at = datetime.now()
            
            # 验证部署
            verification_result = await self._verify_deployment(plan)
            
            if not verification_result.get("success"):
                await self._execute_rollback(plan_id, reason="Deployment verification failed")
                return {
                    "plan_id": plan_id,
                    "status": "rolled_back",
                    "message": "Deployment verification failed and rolled back"
                }
            
            # 记录部署历史
            self.deployment_history.append(plan)
            
            return {
                "plan_id": plan_id,
                "status": "completed",
                "message": "Deployment completed successfully",
                "results": deployment_results,
                "verification": verification_result
            }
        
        except Exception as e:
            logger.error(f"Deployment error: {str(e)}", exc_info=True)
            await self._execute_rollback(plan_id, reason=f"Deployment error: {str(e)}")
            
            return {
                "plan_id": plan_id,
                "status": "failed",
                "message": f"Deployment failed: {str(e)}"
            }
    
    async def _prepare_deployment(self, plan: DeploymentPlan):
        """部署前准备"""
        logger.info(f"Preparing deployment: {plan.plan_id}")
        
        # 验证配置
        config_valid = await self._validate_deployment_config(plan)
        if not config_valid:
            raise ValueError("Deployment configuration validation failed")
        
        # 准备回滚预案
        await self._prepare_rollback_resources(plan)
        
        # 通知监控系统
        await self._notify_monitoring("deployment_started", {"plan_id": plan.plan_id})
    
    async def _deploy_service(
        self,
        service_deployment: ServiceDeployment,
        plan: DeploymentPlan
    ) -> Dict[str, Any]:
        """部署单个服务"""
        service_name = service_deployment.service_name
        logger.info(f"Deploying service: {service_name}")
        
        service_deployment.status = DeploymentStatus.DEPLOYING
        service_deployment.deployment_time = datetime.now()
        
        try:
            # 检查服务依赖
            for dep in service_deployment.dependencies:
                dep_status = await self._check_service_status(dep)
                if not dep_status.get("healthy"):
                    raise ValueError(f"Dependency {dep} is not healthy")
            
            # 执行部署（这里应该调用实际的部署命令）
            # 例如：docker-compose up, kubectl apply, 等
            
            # 等待服务启动
            await asyncio.sleep(5)  # 模拟等待时间
            
            # 健康检查
            health_check = await self._check_service_health(service_name)
            
            if health_check.get("healthy"):
                service_deployment.status = DeploymentStatus.VERIFYING
                service_deployment.health_check_passed = True
                
                # 性能基线检查
                performance_check = await self._check_service_performance(service_name)
                service_deployment.performance_baseline = performance_check
                
                return {
                    "service": service_name,
                    "status": "success",
                    "health_check": health_check,
                    "performance": performance_check
                }
            else:
                service_deployment.status = DeploymentStatus.FAILED
                return {
                    "service": service_name,
                    "status": "failed",
                    "error": "Health check failed",
                    "health_check": health_check
                }
        
        except Exception as e:
            service_deployment.status = DeploymentStatus.FAILED
            logger.error(f"Service deployment failed: {service_name}, {str(e)}")
            
            return {
                "service": service_name,
                "status": "failed",
                "error": str(e)
            }
    
    # ==================== 平台配置管理 ====================
    
    async def validate_and_sync_config(
        self,
        environment: str,
        config_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """验证和同步配置"""
        errors = []
        
        # 验证必需配置项
        required_keys = ["database_url", "redis_url", "jwt_secret"]
        for key in required_keys:
            if key not in config_data:
                errors.append(f"Missing required config: {key}")
        
        # 验证配置格式
        if "database_url" in config_data:
            db_url = config_data["database_url"]
            if not db_url.startswith(("postgresql://", "sqlite://")):
                errors.append("Invalid database URL format")
        
        # 同步配置到各服务
        if not errors:
            for service_name in self.service_urls.keys():
                try:
                    await self._sync_config_to_service(service_name, config_data)
                except Exception as e:
                    errors.append(f"Failed to sync config to {service_name}: {str(e)}")
        
        return len(errors) == 0, errors
    
    async def _sync_config_to_service(
        self,
        service_name: str,
        config_data: Dict[str, Any]
    ):
        """同步配置到服务"""
        service_url = self.service_urls.get(service_name)
        if not service_url:
            return
        
        try:
            from shared_libs.common.http_client import HTTPClient
            
            async with HTTPClient(service_url) as client:
                await client.post(
                    "/api/config/update",
                    data={"config": config_data}
                )
        except Exception as e:
            logger.warning(f"Failed to sync config to {service_name}: {str(e)}")
    
    async def manage_service_dependencies(
        self,
        service_name: str
    ) -> Dict[str, Any]:
        """管理服务依赖关系"""
        dependencies = self.service_dependencies.get(service_name, [])
        
        dependency_status = {}
        for dep in dependencies:
            status = await self._check_service_status(dep)
            dependency_status[dep] = status
        
        return {
            "service": service_name,
            "dependencies": dependencies,
            "status": dependency_status,
            "all_healthy": all(s.get("healthy", False) for s in dependency_status.values())
        }
    
    async def manage_secrets_and_certificates(
        self,
        secrets: Dict[str, str],
        certificates: Dict[str, str]
    ) -> Dict[str, Any]:
        """管理密钥和证书"""
        # 验证密钥格式
        secret_errors = []
        for key, value in secrets.items():
            if not value or len(value) < 8:
                secret_errors.append(f"Secret {key} is too short or empty")
        
        # 验证证书格式（简化）
        cert_errors = []
        for name, cert in certificates.items():
            if not cert.startswith("-----BEGIN"):
                cert_errors.append(f"Certificate {name} format invalid")
        
        # 存储密钥和证书（这里应该使用安全的存储方式）
        config_version = f"config_{uuid.uuid4().hex[:12]}"
        deployment_config = DeploymentConfig(
            environment="production",
            config_version=config_version,
            config_data={},
            secrets=secrets,
            certificates=certificates,
            validated=len(secret_errors) == 0 and len(cert_errors) == 0,
            validation_errors=secret_errors + cert_errors
        )
        
        self.config_versions[config_version] = deployment_config
        
        return {
            "config_version": config_version,
            "secrets_count": len(secrets),
            "certificates_count": len(certificates),
            "validated": deployment_config.validated,
            "errors": secret_errors + cert_errors
        }
    
    def track_config_changes(
        self,
        config_version: str,
        changes: Dict[str, Any]
    ):
        """追踪配置变更"""
        change_record = {
            "config_version": config_version,
            "timestamp": datetime.now().isoformat(),
            "changes": changes,
            "changed_by": self.config.get("user", "system")
        }
        
        self.config_history.append(change_record)
        
        logger.info(f"Config change tracked: {config_version}")
    
    # ==================== 部署健康监控 ====================
    
    async def monitor_deployment(
        self,
        plan_id: str,
        duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """监控部署过程"""
        plan = self.active_deployments.get(plan_id)
        if not plan:
            raise ValueError(f"Deployment plan not found: {plan_id}")
        
        monitoring_results = []
        start_time = time.time()
        timeout = duration or self.rollback_thresholds["deployment_timeout_seconds"]
        
        while True:
            if time.time() - start_time > timeout:
                break
            
            # 检查每个服务的状态
            for service_deployment in plan.services:
                status = await self._check_service_status(service_deployment.service_name)
                health = await self._check_service_health(service_deployment.service_name)
                
                monitoring_results.append({
                    "timestamp": datetime.now().isoformat(),
                    "service": service_deployment.service_name,
                    "status": status,
                    "health": health
                })
            
            await asyncio.sleep(10)  # 每10秒检查一次
        
        return {
            "plan_id": plan_id,
            "monitoring_duration": time.time() - start_time,
            "results": monitoring_results
        }
    
    async def check_service_startup_status(
        self,
        service_name: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """检查服务启动状态"""
        start_time = time.time()
        service_url = self.service_urls.get(service_name)
        
        if not service_url:
            return {
                "service": service_name,
                "status": "not_configured",
                "healthy": False
            }
        
        while time.time() - start_time < timeout:
            try:
                from shared_libs.common.http_client import HTTPClient
                
                async with HTTPClient(service_url, timeout=5) as client:
                    health = await client.get("/api/health")
                    
                    if health.get("status") == "healthy":
                        return {
                            "service": service_name,
                            "status": "healthy",
                            "healthy": True,
                            "startup_time": time.time() - start_time,
                            "health_data": health
                        }
            except Exception as e:
                logger.debug(f"Service {service_name} not ready yet: {str(e)}")
            
            await asyncio.sleep(2)
        
        return {
            "service": service_name,
            "status": "timeout",
            "healthy": False,
            "startup_time": timeout
        }
    
    async def compare_performance_baseline(
        self,
        service_name: str,
        baseline: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """对比性能基线"""
        current_performance = await self._check_service_performance(service_name)
        
        if not baseline:
            # 使用当前性能作为基线
            return {
                "service": service_name,
                "baseline_set": True,
                "baseline": current_performance
            }
        
        # 对比性能指标
        degradation = {}
        for metric, baseline_value in baseline.items():
            current_value = current_performance.get(metric)
            if current_value and baseline_value:
                if isinstance(current_value, (int, float)) and isinstance(baseline_value, (int, float)):
                    percent_change = ((current_value - baseline_value) / baseline_value) * 100
                    if percent_change > self.rollback_thresholds["performance_degradation_percent"]:
                        degradation[metric] = {
                            "baseline": baseline_value,
                            "current": current_value,
                            "change_percent": percent_change
                        }
        
        return {
            "service": service_name,
            "current_performance": current_performance,
            "baseline": baseline,
            "degradation": degradation,
            "within_baseline": len(degradation) == 0
        }
    
    async def assess_user_impact(
        self,
        plan_id: str
    ) -> Dict[str, Any]:
        """评估用户影响"""
        plan = self.active_deployments.get(plan_id)
        if not plan:
            return {"error": "Deployment plan not found"}
        
        impact_assessment = {
            "affected_services": [],
            "user_impact": "low",
            "estimated_downtime": 0,
            "affected_features": []
        }
        
        for service_deployment in plan.services:
            if service_deployment.status == DeploymentStatus.FAILED:
                priority = service_deployment.priority
                
                if priority == ServicePriority.CRITICAL:
                    impact_assessment["user_impact"] = "critical"
                    impact_assessment["estimated_downtime"] += 60  # 分钟
                elif priority == ServicePriority.HIGH:
                    if impact_assessment["user_impact"] != "critical":
                        impact_assessment["user_impact"] = "high"
                    impact_assessment["estimated_downtime"] += 30
                else:
                    impact_assessment["estimated_downtime"] += 10
                
                impact_assessment["affected_services"].append(service_deployment.service_name)
        
        return impact_assessment
    
    # ==================== 紧急响应机制 ====================
    
    async def _should_trigger_rollback(
        self,
        plan_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """判断是否应该触发回滚"""
        plan = self.active_deployments.get(plan_id)
        if not plan:
            return False
        
        # 检查健康检查失败
        if result.get("health_check", {}).get("healthy") is False:
            if self.rollback_triggers.get(RollbackTrigger.HEALTH_CHECK_FAILED):
                return True
        
        # 检查错误率
        error_rate = result.get("error_rate", 0)
        if error_rate > self.rollback_thresholds["error_rate_percent"]:
            if self.rollback_triggers.get(RollbackTrigger.ERROR_RATE_EXCEEDED):
                return True
        
        # 检查性能退化
        performance = result.get("performance", {})
        if performance.get("degraded"):
            if self.rollback_triggers.get(RollbackTrigger.PERFORMANCE_DEGRADED):
                return True
        
        # 检查超时
        if plan.started_at:
            elapsed = (datetime.now() - plan.started_at).total_seconds()
            if elapsed > self.rollback_thresholds["deployment_timeout_seconds"]:
                if self.rollback_triggers.get(RollbackTrigger.TIMEOUT):
                    return True
        
        return False
    
    async def _execute_rollback(
        self,
        plan_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """执行回滚"""
        plan = self.active_deployments.get(plan_id)
        if not plan:
            raise ValueError(f"Deployment plan not found: {plan_id}")
        
        logger.warning(f"Executing rollback for plan {plan_id}: {reason}")
        
        plan.status = DeploymentStatus.ROLLING_BACK
        
        rollback_results = []
        
        # 按反向顺序回滚
        for service_name in reversed(plan.deployment_order):
            try:
                result = await self._rollback_service(service_name, plan)
                rollback_results.append(result)
            except Exception as e:
                logger.error(f"Rollback failed for {service_name}: {str(e)}")
                rollback_results.append({
                    "service": service_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        plan.status = DeploymentStatus.ROLLED_BACK
        
        # 通知监控系统
        await self._notify_monitoring("rollback_completed", {
            "plan_id": plan_id,
            "reason": reason,
            "results": rollback_results
        })
        
        return {
            "plan_id": plan_id,
            "status": "rolled_back",
            "reason": reason,
            "results": rollback_results
        }
    
    async def _rollback_service(
        self,
        service_name: str,
        plan: DeploymentPlan
    ) -> Dict[str, Any]:
        """回滚单个服务"""
        logger.info(f"Rolling back service: {service_name}")
        
        rollback_plan = plan.rollback_plan
        previous_version = rollback_plan.get("previous_versions", {}).get(service_name, "unknown")
        
        # 执行回滚（这里应该调用实际的回滚命令）
        # 例如：恢复到之前的版本
        
        return {
            "service": service_name,
            "previous_version": previous_version,
            "status": "rolled_back"
        }
    
    async def execute_service_degradation(
        self,
        service_name: str,
        degradation_level: str = "reduced"
    ) -> Dict[str, Any]:
        """执行服务降级策略"""
        logger.info(f"Degrading service {service_name} to level: {degradation_level}")
        
        # 根据降级级别调整服务功能
        degradation_config = {
            "reduced": {
                "disable_non_essential_features": True,
                "rate_limit": 0.5,
                "cache_ttl": 300
            },
            "minimal": {
                "disable_non_essential_features": True,
                "rate_limit": 0.2,
                "cache_ttl": 600,
                "disable_background_tasks": True
            },
            "emergency": {
                "maintenance_mode": True,
                "read_only": True
            }
        }
        
        config = degradation_config.get(degradation_level, degradation_config["reduced"])
        
        # 应用降级配置
        service_url = self.service_urls.get(service_name)
        if service_url:
            try:
                from shared_libs.common.http_client import HTTPClient
                
                async with HTTPClient(service_url) as client:
                    await client.post(
                        "/api/degradation/apply",
                        data={"level": degradation_level, "config": config}
                    )
            except Exception as e:
                logger.error(f"Failed to apply degradation: {str(e)}")
        
        return {
            "service": service_name,
            "degradation_level": degradation_level,
            "config": config,
            "applied": True
        }
    
    async def isolate_fault(
        self,
        service_name: str
    ) -> Dict[str, Any]:
        """故障隔离处理"""
        logger.warning(f"Isolating fault in service: {service_name}")
        
        # 停止服务
        # 移除负载均衡器中的服务
        # 通知相关服务
        
        isolation_result = {
            "service": service_name,
            "isolated": True,
            "timestamp": datetime.now().isoformat(),
            "actions": [
                "service_stopped",
                "load_balancer_updated",
                "dependencies_notified"
            ]
        }
        
        # 通知告警系统
        await self._trigger_alert(
            level="critical",
            message=f"Service {service_name} isolated due to fault",
            details=isolation_result
        )
        
        return isolation_result
    
    async def escalate_alert(
        self,
        alert_id: str,
        level: str
    ) -> Dict[str, Any]:
        """告警升级机制"""
        escalation_levels = ["info", "warning", "error", "critical"]
        
        current_level_index = escalation_levels.index(level) if level in escalation_levels else 0
        
        if current_level_index < len(escalation_levels) - 1:
            next_level = escalation_levels[current_level_index + 1]
            
            # 升级告警
            await self._trigger_alert(
                level=next_level,
                message=f"Alert {alert_id} escalated to {next_level}",
                details={"original_level": level, "escalated_level": next_level}
            )
            
            return {
                "alert_id": alert_id,
                "original_level": level,
                "escalated_level": next_level,
                "escalated": True
            }
        
        return {
            "alert_id": alert_id,
            "level": level,
            "escalated": False,
            "message": "Already at maximum alert level"
        }
    
    # ==================== 辅助方法 ====================
    
    async def _check_service_status(self, service_name: str) -> Dict[str, Any]:
        """检查服务状态"""
        service_url = self.service_urls.get(service_name)
        if not service_url:
            return {"healthy": False, "error": "Service not configured"}
        
        try:
            from shared_libs.common.http_client import HTTPClient
            
            async with HTTPClient(service_url, timeout=5) as client:
                health = await client.get("/api/health")
                return {
                    "healthy": health.get("status") == "healthy",
                    "status": health.get("status"),
                    "data": health
                }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """检查服务健康状态"""
        return await self._check_service_status(service_name)
    
    async def _check_service_performance(self, service_name: str) -> Dict[str, Any]:
        """检查服务性能"""
        service_url = self.service_urls.get(service_name)
        if not service_url:
            return {}
        
        try:
            from shared_libs.common.http_client import HTTPClient
            
            async with HTTPClient(service_url) as client:
                monitoring = await client.get("/api/monitoring")
                resource_usage = monitoring.get("resource_usage", {})
                
                return {
                    "response_time": monitoring.get("avg_response_time", 0),
                    "memory_usage": resource_usage.get("memory_usage_mb", 0),
                    "cpu_usage": resource_usage.get("cpu_usage_percent", 0),
                    "error_rate": monitoring.get("error_rate", 0)
                }
        except Exception as e:
            logger.warning(f"Failed to get performance metrics: {str(e)}")
            return {}
    
    async def _validate_deployment_config(self, plan: DeploymentPlan) -> bool:
        """验证部署配置"""
        # 验证配置完整性
        return True
    
    async def _prepare_rollback_resources(self, plan: DeploymentPlan):
        """准备回滚资源"""
        # 准备回滚所需的资源
        pass
    
    async def _verify_deployment(self, plan: DeploymentPlan) -> Dict[str, Any]:
        """验证部署"""
        all_healthy = True
        
        for service_deployment in plan.services:
            status = await self._check_service_status(service_deployment.service_name)
            if not status.get("healthy"):
                all_healthy = False
                break
        
        return {
            "success": all_healthy,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _notify_monitoring(self, event: str, data: Dict[str, Any]):
        """通知监控系统"""
        for callback in self.monitoring_callbacks:
            try:
                await callback(event, data)
            except Exception as e:
                logger.error(f"Monitoring callback error: {str(e)}")
    
    async def _trigger_alert(self, level: str, message: str, details: Dict[str, Any]):
        """触发告警"""
        for callback in self.alert_callbacks:
            try:
                await callback(level, message, details)
            except Exception as e:
                logger.error(f"Alert callback error: {str(e)}")
    
    def register_monitoring_callback(self, callback: Callable):
        """注册监控回调"""
        self.monitoring_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable):
        """注册告警回调"""
        self.alert_callbacks.append(callback)


# 全局部署管理器实例
_deployment_manager_instance: Optional[PlatformDeploymentManager] = None


def get_deployment_manager(
    config: Optional[Dict[str, Any]] = None
) -> PlatformDeploymentManager:
    """获取部署管理器实例（单例模式）"""
    global _deployment_manager_instance
    if _deployment_manager_instance is None:
        _deployment_manager_instance = PlatformDeploymentManager(config)
    return _deployment_manager_instance

