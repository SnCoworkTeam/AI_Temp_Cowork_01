"""
组织架构服务
提供组织架构的CRUD操作和查询
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.enterprise_architecture_models import (
    OrganizationUnit, BusinessRole, OrganizationBusinessRelationship,
    BusinessProcess, BusinessCapability, ApplicationSystem, TechnologyInstance
)
from database.src.core.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class OrganizationArchitectureService:
    """组织架构服务"""
    
    def __init__(self, db: Session, neo4j_client: Optional[Neo4jClient] = None):
        self.db = db
        self.neo4j = neo4j_client
    
    # ========== 组织单元CRUD ==========
    
    async def create_organization_unit(
        self, 
        name: str,
        code: Optional[str] = None,
        description: Optional[str] = None,
        organization_type: Optional[str] = None,
        level: int = 1,
        parent_id: Optional[UUID] = None,
        manager_id: Optional[UUID] = None,
        location: Optional[str] = None,
        meta_data: Optional[Dict] = None
    ) -> OrganizationUnit:
        """创建组织单元"""
        try:
            org_unit = OrganizationUnit(
                name=name,
                code=code,
                description=description,
                organization_type=organization_type,
                level=level,
                parent_id=parent_id,
                manager_id=manager_id,
                location=location,
                meta_data=meta_data or {}
            )
            self.db.add(org_unit)
            self.db.commit()
            self.db.refresh(org_unit)
            
            # 创建Neo4j节点
            if self.neo4j:
                await self._create_neo4j_node(org_unit)
            
            return org_unit
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating organization unit: {str(e)}", exc_info=True)
            raise
    
    async def get_organization_unit(self, org_id: UUID) -> Optional[OrganizationUnit]:
        """获取组织单元"""
        return self.db.query(OrganizationUnit).filter(OrganizationUnit.id == org_id).first()
    
    async def get_all_organizations(self) -> List[OrganizationUnit]:
        """获取所有组织单元"""
        return self.db.query(OrganizationUnit).order_by(OrganizationUnit.level, OrganizationUnit.name).all()
    
    async def get_root_organizations(self) -> List[OrganizationUnit]:
        """获取所有根组织（没有父组织的组织）"""
        return self.db.query(OrganizationUnit).filter(
            OrganizationUnit.parent_id.is_(None)
        ).order_by(OrganizationUnit.name).all()
    
    async def get_organization_hierarchy(self, org_id: UUID) -> Dict[str, Any]:
        """获取组织层级结构"""
        org = await self.get_organization_unit(org_id)
        if not org:
            return {}
        
        # 获取子组织
        children = self.db.query(OrganizationUnit).filter(
            OrganizationUnit.parent_id == org_id
        ).all()
        
        # 递归获取子组织的子组织
        children_data = []
        for child in children:
            child_data = await self.get_organization_hierarchy(child.id)
            children_data.append(child_data)
        
        return {
            "id": str(org.id),
            "name": org.name,
            "code": org.code,
            "description": org.description,
            "organization_type": org.organization_type,
            "level": org.level,
            "status": org.status,
            "children": children_data if children_data else []
        }
    
    # ========== 组织责任查询 ==========
    
    async def get_organization_responsibilities(self, org_id: UUID) -> Dict[str, Any]:
        """获取组织的责任范围"""
        org = await self.get_organization_unit(org_id)
        if not org:
            raise ValueError(f"组织不存在: {org_id}")
        
        # 查询拥有的业务能力
        capabilities = self.db.query(BusinessCapability).filter(
            BusinessCapability.owner_organization_id == org_id
        ).all()
        
        # 查询执行的业务流程
        processes = self.db.query(BusinessProcess).filter(
            BusinessProcess.organization_id == org_id
        ).all()
        
        # 查询管理的应用系统
        systems = self.db.query(ApplicationSystem).filter(
            ApplicationSystem.business_owner_org_id == org_id
        ).all()
        
        # 查询使用的技术实例
        tech_instances = self.db.query(TechnologyInstance).join(
            ApplicationSystem
        ).filter(
            ApplicationSystem.business_owner_org_id == org_id
        ).all()
        
        return {
            "organization": {
                "id": str(org.id),
                "name": org.name,
                "code": org.code
            },
            "capabilities": [self._capability_to_dict(c) for c in capabilities],
            "processes": [self._process_to_dict(p) for p in processes],
            "systems": [self._system_to_dict(s) for s in systems],
            "technologies": [self._tech_instance_to_dict(t) for t in tech_instances]
        }
    
    async def get_organization_resources(self, org_id: UUID) -> Dict[str, Any]:
        """获取组织的IT资源统计"""
        org = await self.get_organization_unit(org_id)
        if not org:
            raise ValueError(f"组织不存在: {org_id}")
        
        # 降级到PostgreSQL查询
        systems = self.db.query(ApplicationSystem).filter(
            ApplicationSystem.business_owner_org_id == org_id
        ).all()
        
        tech_instances = self.db.query(TechnologyInstance).join(
            ApplicationSystem
        ).filter(
            ApplicationSystem.business_owner_org_id == org_id
        ).all()
        
        return {
            "organization": org.name,
            "system_count": len(systems),
            "technology_count": len(tech_instances),
            "systems": [s.name for s in systems],
            "technologies": [t.name for t in tech_instances]
        }
    
    # ========== Neo4j节点创建 ==========
    
    async def _create_neo4j_node(self, org_unit: OrganizationUnit):
        """创建Neo4j组织节点"""
        if not self.neo4j:
            return
        
        try:
            # 使用Neo4j客户端创建节点
            query = """
            CREATE (org:OrganizationUnit {
                uuid: $uuid,
                name: $name,
                code: $code,
                description: $description,
                organization_type: $organization_type,
                level: $level,
                location: $location,
                status: $status
            })
            RETURN id(org) as node_id
            """
            result = await self.neo4j.execute_query(
                query,
                {
                    "uuid": str(org_unit.id),
                    "name": org_unit.name,
                    "code": org_unit.code,
                    "description": org_unit.description,
                    "organization_type": org_unit.organization_type,
                    "level": org_unit.level,
                    "location": org_unit.location,
                    "status": org_unit.status
                }
            )
            
            if result and len(result) > 0:
                org_unit.neo4j_node_id = str(result[0].get("node_id", ""))
                self.db.commit()
            
            # 创建组织层级关系
            if org_unit.parent_id:
                await self._create_parent_relationship(org_unit)
        except Exception as e:
            logger.error(f"Error creating Neo4j node for organization: {str(e)}", exc_info=True)
    
    async def _create_parent_relationship(self, org_unit: OrganizationUnit):
        """创建组织层级关系"""
        parent = self.db.query(OrganizationUnit).filter(
            OrganizationUnit.id == org_unit.parent_id
        ).first()
        
        if parent and parent.neo4j_node_id and org_unit.neo4j_node_id and self.neo4j:
            query = """
            MATCH (parent:OrganizationUnit {uuid: $parent_uuid})
            MATCH (child:OrganizationUnit {uuid: $child_uuid})
            MERGE (parent)-[:PARENT_OF]->(child)
            """
            await self.neo4j.execute_query(
                query,
                {
                    "parent_uuid": str(parent.id),
                    "child_uuid": str(org_unit.id)
                }
            )
    
    # ========== 辅助方法 ==========
    
    def _capability_to_dict(self, cap: BusinessCapability) -> Dict[str, Any]:
        return {
            "id": str(cap.id),
            "name": cap.name,
            "description": cap.description,
            "level": cap.level
        }
    
    def _process_to_dict(self, proc: BusinessProcess) -> Dict[str, Any]:
        return {
            "id": str(proc.id),
            "name": proc.name,
            "description": proc.description,
            "criticality": proc.meta_data.get("criticality") if proc.meta_data else None,
            "pain_points": proc.meta_data.get("pain_points", []) if proc.meta_data else []
        }
    
    def _system_to_dict(self, sys: ApplicationSystem) -> Dict[str, Any]:
        return {
            "id": str(sys.id),
            "name": sys.name,
            "system_type": sys.system_type,
            "system_category": sys.system_category,
            "vendor": sys.vendor,
            "version": sys.version
        }
    
    def _tech_instance_to_dict(self, ti: TechnologyInstance) -> Dict[str, Any]:
        return {
            "id": str(ti.id),
            "name": ti.name,
            "technology_name": ti.technology_name,
            "version": ti.version,
            "deployment_type": ti.deployment_type
        }

