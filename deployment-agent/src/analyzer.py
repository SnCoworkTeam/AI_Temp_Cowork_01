"""
服务分析器 - 分析代码变更影响的服务
"""
import json
import logging
from pathlib import Path
from typing import List, Set, Dict, Optional

logger = logging.getLogger(__name__)


class ServiceAnalyzer:
    """服务分析器 - 分析代码变更影响的服务"""
    
    def __init__(self, service_map_path: Optional[str] = None):
        """
        初始化服务分析器
        
        Args:
            service_map_path: 服务映射配置文件路径
        """
        self.service_map = self._load_service_map(service_map_path)
        self.dependency_graph = self._build_dependency_graph()
    
    def _load_service_map(self, config_path: Optional[str]) -> Dict[str, List[str]]:
        """加载服务映射配置"""
        # 默认服务映射（基于实际项目结构）
        default_map = {
            # 服务目录映射
            "agent-service/": ["agent-service"],
            "api-gateway/": ["api-gateway"],
            "auth-service/": ["auth-service"],
            "workflow-engine/": ["workflow-engine"],
            "knowledge-base/": ["knowledge-base"],
            "metadata-service/": ["metadata-service"],
            "chat-service/": ["chat-service"],
            "mcp-gateway/": ["mcp-gateway"],
            "web-ui/": ["web-ui"],
            "registry-service/": ["registry-service"],
            "config-center/": ["config-center"],
            "dag-orchestrator/": ["dag-orchestrator"],
            "agent-orchestrator/": ["agent-orchestrator"],
            "agent-registry/": ["agent-registry"],
            "memory-service/": ["memory-service"],
            "vector-coordinator-service/": ["vector-coordinator-service"],
            "sap-metadata-agent/": ["sap-metadata-agent"],
            
            # 共享资源映射（影响所有服务）
            "shared_libs/": ["all"],
            "shared-libs/": ["all"],
            "docker-compose.yml": ["all"],
            "docker-compose.prod.yml": ["all"],
            "config/": ["all"],
            "database/": ["all"],  # 数据库迁移影响所有服务
        }
        
        # 如果提供了配置文件，尝试加载
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_map = json.load(f)
                    default_map.update(custom_map)
                    logger.info(f"已加载服务映射配置: {config_path}")
            except Exception as e:
                logger.warning(f"加载服务映射配置失败: {e}, 使用默认配置")
        
        return default_map
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """构建服务依赖关系图"""
        return {
            # 基础服务（无依赖）
            "postgres": [],
            "redis": [],
            "qdrant": [],
            "neo4j": [],
            
            # 基础设施服务
            "registry-service": ["redis"],
            "config-center": ["redis", "registry-service"],
            
            # 核心服务
            "workflow-engine": ["postgres", "redis"],
            "mcp-gateway": ["postgres", "redis", "workflow-engine"],
            "auth-service": ["postgres", "redis"],
            "knowledge-base": ["postgres", "redis", "neo4j"],
            "metadata-service": ["postgres", "redis", "neo4j"],
            
            # 业务服务
            "chat-service": ["postgres", "redis", "knowledge-base", "metadata-service"],
            "memory-service": ["redis"],
            "agent-service": ["postgres", "redis", "workflow-engine", "metadata-service"],
            "agent-orchestrator": ["agent-service", "workflow-engine"],
            "agent-registry": ["registry-service"],
            "dag-orchestrator": ["workflow-engine"],
            "sap-metadata-agent": ["metadata-service"],
            "vector-coordinator-service": ["qdrant"],
            
            # 网关和前端
            "api-gateway": ["registry-service", "config-center"],  # 依赖所有业务服务
            "web-ui": ["api-gateway"],
        }
    
    def analyze_changes(self, changed_files: List[str]) -> List[str]:
        """
        分析变更影响的服务
        
        Args:
            changed_files: 变更的文件路径列表
        
        Returns:
            受影响的服务列表，如果返回["all"]则表示需要全量部署
        """
        affected_services: Set[str] = set()
        
        for file_path in changed_files:
            # 标准化路径（使用正斜杠）
            normalized_path = file_path.replace("\\", "/")
            
            # 检查服务映射
            for pattern, services in self.service_map.items():
                if pattern in normalized_path:
                    if services == ["all"]:
                        logger.info(f"检测到全量部署触发文件: {file_path}")
                        return ["all"]  # 全量部署
                    affected_services.update(services)
                    logger.debug(f"文件 {file_path} 影响服务: {services}")
        
        return list(affected_services)
    
    def get_dependencies(self, service: str) -> Set[str]:
        """
        获取服务的所有依赖（递归）
        
        Args:
            service: 服务名称
        
        Returns:
            依赖服务集合
        """
        dependencies: Set[str] = set()
        queue = [service]
        visited = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            deps = self.dependency_graph.get(current, [])
            for dep in deps:
                if dep not in visited:
                    dependencies.add(dep)
                    queue.append(dep)
        
        return dependencies
    
    def get_all_dependencies(self, services: List[str]) -> List[str]:
        """
        获取所有服务的依赖（包括依赖的依赖）
        
        Args:
            services: 服务列表
        
        Returns:
            包含所有依赖的完整服务列表
        """
        if "all" in services:
            return ["all"]
        
        all_services: Set[str] = set(services)
        
        for service in services:
            # 添加直接依赖
            deps = self.dependency_graph.get(service, [])
            all_services.update(deps)
            
            # 递归添加依赖的依赖
            for dep in deps:
                all_services.update(self.get_dependencies(dep))
        
        return sorted(list(all_services))
    
    def generate_deployment_plan(self, services: List[str]) -> Dict:
        """
        生成部署计划
        
        Args:
            services: 需要部署的服务列表
        
        Returns:
            部署计划字典
        """
        if "all" in services:
            return {
                "type": "full",
                "services": ["all"],
                "description": "全量部署所有服务"
            }
        
        # 按依赖关系排序
        sorted_services = self._topological_sort(services)
        
        return {
            "type": "incremental",
            "services": sorted_services,
            "description": f"增量部署 {len(sorted_services)} 个服务"
        }
    
    def _topological_sort(self, services: List[str]) -> List[str]:
        """拓扑排序服务（确保依赖的服务先部署）"""
        # 简化实现：先部署基础服务，再部署业务服务
        base_services = ["postgres", "redis", "qdrant", "neo4j"]
        infra_services = ["registry-service", "config-center"]
        core_services = ["workflow-engine", "mcp-gateway", "auth-service", 
                        "knowledge-base", "metadata-service"]
        business_services = ["chat-service", "memory-service", "agent-service",
                            "agent-orchestrator", "agent-registry", "dag-orchestrator",
                            "sap-metadata-agent", "vector-coordinator-service"]
        gateway_services = ["api-gateway", "web-ui"]
        
        service_order = base_services + infra_services + core_services + business_services + gateway_services
        
        # 按顺序过滤出需要部署的服务
        result = []
        for service in service_order:
            if service in services:
                result.append(service)
        
        # 添加不在预定义顺序中的服务
        for service in services:
            if service not in result:
                result.append(service)
        
        return result




