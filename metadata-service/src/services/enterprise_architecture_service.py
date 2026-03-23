"""
企业架构服务
提供企业架构数据的CRUD操作和查询
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

# 导入数据库模型
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.enterprise_architecture_models import (
    BusinessProcess, BusinessCapability, BusinessService,
    ApplicationSystem, ApplicationService, APIInterface,
    DataEntity, DataModel, DataFlow,
    TechnologyComponent, TechnologyStack, InfrastructureComponent,
    ArchitectureRelationship, OrganizationUnit, BusinessRole
)

logger = logging.getLogger(__name__)


class EnterpriseArchitectureService:
    """企业架构服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== 总览统计 ==========
    
    async def get_overview(self) -> Dict[str, Any]:
        """获取企业架构总览"""
        try:
            return {
                "organization_architecture": {
                    "organizations_count": self._count_organization_units(),
                    "departments_count": self._count_organization_units_by_type("Department"),
                    "teams_count": self._count_organization_units_by_type("Team"),
                    "roles_count": self._count_business_roles()
                },
                "business_architecture": {
                    "processes_count": self._count_business_processes(),
                    "capabilities_count": self._count_business_capabilities(),
                    "services_count": self._count_business_services()
                },
                "application_architecture": {
                    "systems_count": self._count_application_systems(),
                    "services_count": self._count_application_services(),
                    "apis_count": self._count_api_interfaces()
                },
                "data_architecture": {
                    "entities_count": self._count_data_entities(),
                    "models_count": self._count_data_models(),
                    "flows_count": self._count_data_flows()
                },
                "technology_architecture": {
                    "components_count": self._count_technology_components(),
                    "stacks_count": self._count_technology_stacks(),
                    "infrastructure_count": self._count_infrastructure_components()
                }
            }
        except Exception as e:
            logger.error(f"Error getting EA overview: {str(e)}", exc_info=True)
            raise
    
    # ========== 业务架构 ==========
    
    async def get_business_architecture(self) -> Dict[str, Any]:
        """获取业务架构"""
        try:
            processes = self.db.query(BusinessProcess).all()
            capabilities = self.db.query(BusinessCapability).all()
            services = self.db.query(BusinessService).all()
            
            return {
                "processes": [self._process_to_dict(p) for p in processes],
                "capabilities": [self._capability_to_dict(c) for c in capabilities],
                "services": [self._business_service_to_dict(s) for s in services]
            }
        except Exception as e:
            logger.error(f"Error getting business architecture: {str(e)}", exc_info=True)
            raise
    
    def _count_business_processes(self) -> int:
        """统计业务流程数量"""
        return self.db.query(func.count(BusinessProcess.id)).scalar() or 0
    
    def _count_business_capabilities(self) -> int:
        """统计业务能力数量"""
        return self.db.query(func.count(BusinessCapability.id)).scalar() or 0
    
    def _count_business_services(self) -> int:
        """统计业务服务数量"""
        return self.db.query(func.count(BusinessService.id)).scalar() or 0
    
    # ========== 应用架构 ==========
    
    async def get_application_architecture(self) -> Dict[str, Any]:
        """获取应用架构"""
        try:
            systems = self.db.query(ApplicationSystem).all()
            services = self.db.query(ApplicationService).all()
            apis = self.db.query(APIInterface).all()
            
            return {
                "systems": [self._application_system_to_dict(s) for s in systems],
                "services": [self._application_service_to_dict(s) for s in services],
                "apis": [self._api_interface_to_dict(a) for a in apis]
            }
        except Exception as e:
            logger.error(f"Error getting application architecture: {str(e)}", exc_info=True)
            raise
    
    def _count_application_systems(self) -> int:
        """统计应用系统数量"""
        return self.db.query(func.count(ApplicationSystem.id)).scalar() or 0
    
    def _count_application_services(self) -> int:
        """统计应用服务数量"""
        return self.db.query(func.count(ApplicationService.id)).scalar() or 0
    
    def _count_api_interfaces(self) -> int:
        """统计API接口数量"""
        return self.db.query(func.count(APIInterface.id)).scalar() or 0
    
    # ========== 数据架构 ==========
    
    async def get_data_architecture(self) -> Dict[str, Any]:
        """获取数据架构"""
        try:
            entities = self.db.query(DataEntity).all()
            models = self.db.query(DataModel).all()
            flows = self.db.query(DataFlow).all()
            
            return {
                "entities": [self._data_entity_to_dict(e) for e in entities],
                "models": [self._data_model_to_dict(m) for m in models],
                "flows": [self._data_flow_to_dict(f) for f in flows]
            }
        except Exception as e:
            logger.error(f"Error getting data architecture: {str(e)}", exc_info=True)
            raise
    
    def _count_data_entities(self) -> int:
        """统计数据实体数量"""
        return self.db.query(func.count(DataEntity.id)).scalar() or 0
    
    def _count_data_models(self) -> int:
        """统计数据模型数量"""
        return self.db.query(func.count(DataModel.id)).scalar() or 0
    
    def _count_data_flows(self) -> int:
        """统计数据流数量"""
        return self.db.query(func.count(DataFlow.id)).scalar() or 0
    
    # ========== 组织架构统计 ==========
    
    def _count_organization_units(self) -> int:
        """统计组织单元数量"""
        return self.db.query(func.count(OrganizationUnit.id)).scalar() or 0
    
    def _count_organization_units_by_type(self, org_type: str) -> int:
        """按类型统计组织单元数量"""
        return self.db.query(func.count(OrganizationUnit.id)).filter(
            OrganizationUnit.organization_type == org_type
        ).scalar() or 0
    
    def _count_business_roles(self) -> int:
        """统计业务角色数量"""
        return self.db.query(func.count(BusinessRole.id)).scalar() or 0
    
    # ========== 技术架构 ==========
    
    async def get_technology_architecture(self) -> Dict[str, Any]:
        """获取技术架构"""
        try:
            components = self.db.query(TechnologyComponent).all()
            stacks = self.db.query(TechnologyStack).all()
            infrastructure = self.db.query(InfrastructureComponent).all()
            
            return {
                "components": [self._technology_component_to_dict(c) for c in components],
                "stacks": [self._technology_stack_to_dict(s) for s in stacks],
                "infrastructure": [self._infrastructure_component_to_dict(i) for i in infrastructure]
            }
        except Exception as e:
            logger.error(f"Error getting technology architecture: {str(e)}", exc_info=True)
            raise
    
    def _count_technology_components(self) -> int:
        """统计技术组件数量"""
        return self.db.query(func.count(TechnologyComponent.id)).scalar() or 0
    
    def _count_technology_stacks(self) -> int:
        """统计技术栈数量"""
        return self.db.query(func.count(TechnologyStack.id)).scalar() or 0
    
    def _count_infrastructure_components(self) -> int:
        """统计基础设施组件数量"""
        return self.db.query(func.count(InfrastructureComponent.id)).scalar() or 0
    
    # ========== 架构关系图 ==========
    
    async def get_architecture_graph(self) -> Dict[str, Any]:
        """获取架构关系图"""
        try:
            nodes = []
            links = []
            
            # 添加业务架构节点
            processes = self.db.query(BusinessProcess).all()
            for process in processes:
                nodes.append({
                    "id": str(process.id),
                    "name": process.name,
                    "type": "business_process",
                    "group": "business"
                })
            
            capabilities = self.db.query(BusinessCapability).all()
            for capability in capabilities:
                nodes.append({
                    "id": str(capability.id),
                    "name": capability.name,
                    "type": "business_capability",
                    "group": "business"
                })
            
            # 添加应用架构节点
            systems = self.db.query(ApplicationSystem).all()
            for system in systems:
                nodes.append({
                    "id": str(system.id),
                    "name": system.name,
                    "type": "application_system",
                    "group": "application"
                })
            
            # 添加数据架构节点
            entities = self.db.query(DataEntity).all()
            for entity in entities:
                nodes.append({
                    "id": str(entity.id),
                    "name": entity.name,
                    "type": "data_entity",
                    "group": "data"
                })
            
            # 添加技术架构节点
            components = self.db.query(TechnologyComponent).all()
            for component in components:
                nodes.append({
                    "id": str(component.id),
                    "name": component.name,
                    "type": "technology_component",
                    "group": "technology"
                })
            
            # 添加关系边
            relationships = self.db.query(ArchitectureRelationship).all()
            node_ids = {n["id"] for n in nodes}
            
            for rel in relationships:
                source_id = str(rel.source_id)
                target_id = str(rel.target_id)
                
                if source_id in node_ids and target_id in node_ids:
                    links.append({
                        "source": source_id,
                        "target": target_id,
                        "type": rel.relationship_type,
                        "description": rel.description
                    })
            
            return {"nodes": nodes, "links": links}
        except Exception as e:
            logger.error(f"Error getting architecture graph: {str(e)}", exc_info=True)
            raise
    
    # ========== 影响分析 ==========
    
    async def analyze_impact(self, entity_id: str, entity_type: str) -> Dict[str, Any]:
        """分析架构影响"""
        try:
            # 查找依赖（上游）
            dependencies = self.db.query(ArchitectureRelationship).filter(
                and_(
                    ArchitectureRelationship.target_id == entity_id,
                    ArchitectureRelationship.target_type == entity_type
                )
            ).all()
            
            # 查找影响（下游）
            impacts = self.db.query(ArchitectureRelationship).filter(
                and_(
                    ArchitectureRelationship.source_id == entity_id,
                    ArchitectureRelationship.source_type == entity_type
                )
            ).all()
            
            # 计算风险等级
            risk_level = self._calculate_risk_level(len(dependencies), len(impacts))
            
            return {
                "dependencies": [self._relationship_to_dict(r) for r in dependencies],
                "impacts": [self._relationship_to_dict(r) for r in impacts],
                "risk_level": risk_level,
                "dependency_count": len(dependencies),
                "impact_count": len(impacts)
            }
        except Exception as e:
            logger.error(f"Error analyzing impact: {str(e)}", exc_info=True)
            raise
    
    def _calculate_risk_level(self, dependency_count: int, impact_count: int) -> str:
        """计算风险等级"""
        total = dependency_count + impact_count
        if total == 0:
            return "low"
        elif total < 5:
            return "medium"
        else:
            return "high"
    
    # ========== 数据转换方法 ==========
    
    def _process_to_dict(self, process: BusinessProcess) -> Dict[str, Any]:
        """转换业务流程为字典"""
        return {
            "id": str(process.id),
            "name": process.name,
            "description": process.description,
            "owner": process.owner,
            "status": process.status,
            "classification": process.classification,
            "level": process.level,
            "parent_id": str(process.parent_id) if process.parent_id else None,
            "metadata": process.meta_data or {}
        }
    
    def _capability_to_dict(self, capability: BusinessCapability) -> Dict[str, Any]:
        """转换业务能力为字典"""
        return {
            "id": str(capability.id),
            "name": capability.name,
            "description": capability.description,
            "level": capability.level,
            "parent_id": str(capability.parent_id) if capability.parent_id else None,
            "metadata": capability.meta_data or {}
        }
    
    def _business_service_to_dict(self, service: BusinessService) -> Dict[str, Any]:
        """转换业务服务为字典"""
        return {
            "id": str(service.id),
            "name": service.name,
            "description": service.description,
            "service_type": service.service_type,
            "endpoint": service.endpoint,
            "status": service.status,
            "metadata": service.meta_data or {}
        }
    
    def _application_system_to_dict(self, system: ApplicationSystem) -> Dict[str, Any]:
        """转换应用系统为字典"""
        return {
            "id": str(system.id),
            "name": system.name,
            "description": system.description,
            "system_type": system.system_type,
            "vendor": system.vendor,
            "version": system.version,
            "status": system.status,
            "owner": system.owner,
            "metadata": system.meta_data or {}
        }
    
    def _application_service_to_dict(self, service: ApplicationService) -> Dict[str, Any]:
        """转换应用服务为字典"""
        return {
            "id": str(service.id),
            "application_id": str(service.application_id) if service.application_id else None,
            "name": service.name,
            "description": service.description,
            "service_type": service.service_type,
            "protocol": service.protocol,
            "endpoint": service.endpoint,
            "metadata": service.meta_data or {}
        }
    
    def _api_interface_to_dict(self, api: APIInterface) -> Dict[str, Any]:
        """转换API接口为字典"""
        return {
            "id": str(api.id),
            "service_id": str(api.service_id) if api.service_id else None,
            "path": api.path,
            "method": api.method,
            "description": api.description,
            "metadata": api.meta_data or {}
        }
    
    def _data_entity_to_dict(self, entity: DataEntity) -> Dict[str, Any]:
        """转换数据实体为字典"""
        return {
            "id": str(entity.id),
            "name": entity.name,
            "description": entity.description,
            "schema": entity.schema or {},
            "entity_type": entity.entity_type,
            "metadata": entity.meta_data or {}
        }
    
    def _data_model_to_dict(self, model: DataModel) -> Dict[str, Any]:
        """转换数据模型为字典"""
        return {
            "id": str(model.id),
            "name": model.name,
            "description": model.description,
            "version": model.version,
            "definition": model.definition or {},
            "metadata": model.meta_data or {}
        }
    
    def _data_flow_to_dict(self, flow: DataFlow) -> Dict[str, Any]:
        """转换数据流为字典"""
        return {
            "id": str(flow.id),
            "name": flow.name,
            "description": flow.description,
            "source_entity_id": str(flow.source_entity_id) if flow.source_entity_id else None,
            "target_entity_id": str(flow.target_entity_id) if flow.target_entity_id else None,
            "transformation": flow.transformation,
            "metadata": flow.meta_data or {}
        }
    
    def _technology_component_to_dict(self, component: TechnologyComponent) -> Dict[str, Any]:
        """转换技术组件为字典"""
        return {
            "id": str(component.id),
            "name": component.name,
            "description": component.description,
            "component_type": component.component_type,
            "version": component.version,
            "metadata": component.meta_data or {}
        }
    
    def _technology_stack_to_dict(self, stack: TechnologyStack) -> Dict[str, Any]:
        """转换技术栈为字典"""
        return {
            "id": str(stack.id),
            "name": stack.name,
            "description": stack.description,
            "category": stack.category,
            "components": stack.components or [],
            "metadata": stack.meta_data or {}
        }
    
    def _infrastructure_component_to_dict(self, component: InfrastructureComponent) -> Dict[str, Any]:
        """转换基础设施组件为字典"""
        return {
            "id": str(component.id),
            "name": component.name,
            "description": component.description,
            "component_type": component.component_type,
            "specifications": component.specifications or {},
            "metadata": component.meta_data or {}
        }
    
    def _relationship_to_dict(self, rel: ArchitectureRelationship) -> Dict[str, Any]:
        """转换架构关系为字典"""
        return {
            "id": str(rel.id),
            "source_id": str(rel.source_id),
            "source_type": rel.source_type,
            "target_id": str(rel.target_id),
            "target_type": rel.target_type,
            "relationship_type": rel.relationship_type,
            "description": rel.description,
            "properties": rel.properties or {}
        }

