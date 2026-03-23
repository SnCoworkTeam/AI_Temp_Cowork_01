"""
技术实例服务
提供技术实例的CRUD操作和查询
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from uuid import UUID

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.enterprise_architecture_models import (
    TechnologyInstance, TechnologyType, ApplicationSystem
)
from database.src.core.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class TechnologyInstanceService:
    """技术实例服务"""
    
    def __init__(self, db: Session, neo4j_client: Optional[Neo4jClient] = None):
        self.db = db
        self.neo4j = neo4j_client
    
    # ========== 技术实例CRUD ==========
    
    async def create_technology_instance(
        self,
        name: str,
        application_system_id: UUID,
        technology_type: str,
        technology_name: str,
        version: Optional[str] = None,
        vendor: Optional[str] = None,
        deployment_type: str = "independent",
        instance_id: Optional[str] = None,
        owner_department: Optional[str] = None,
        owner_team: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        location: Optional[str] = None,
        capacity: Optional[str] = None,
        resource_allocation: str = "dedicated",
        status: str = "active",
        lifecycle_status: Optional[str] = None,
        meta_data: Optional[Dict] = None
    ) -> TechnologyInstance:
        """创建技术实例"""
        try:
            # 查找或创建技术类型
            tech_type = await self._get_or_create_technology_type(
                name=technology_name,
                category=technology_type
            )
            
            instance = TechnologyInstance(
                name=name,
                instance_id=instance_id,
                application_system_id=application_system_id,
                owner_department=owner_department,
                owner_team=owner_team,
                technology_type=technology_type,
                technology_name=technology_name,
                technology_type_id=tech_type.id if tech_type else None,
                vendor=vendor,
                version=version,
                deployment_type=deployment_type,
                host=host,
                port=port,
                location=location,
                capacity=capacity,
                resource_allocation=resource_allocation,
                status=status,
                lifecycle_status=lifecycle_status,
                meta_data=meta_data or {}
            )
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            
            # 创建Neo4j节点
            if self.neo4j:
                await self._create_neo4j_node(instance)
            
            # 更新技术类型的实例计数
            if tech_type:
                await self._update_technology_type_count(tech_type.id)
            
            return instance
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating technology instance: {str(e)}", exc_info=True)
            raise
    
    async def get_technology_instance(self, instance_id: UUID) -> Optional[TechnologyInstance]:
        """获取技术实例"""
        return self.db.query(TechnologyInstance).filter(
            TechnologyInstance.id == instance_id
        ).first()
    
    async def get_instances_by_system(self, system_id: UUID) -> List[TechnologyInstance]:
        """按系统查询技术实例"""
        return self.db.query(TechnologyInstance).filter(
            TechnologyInstance.application_system_id == system_id
        ).all()
    
    async def get_instances_by_technology(self, technology_name: str) -> List[TechnologyInstance]:
        """按技术名称查询技术实例"""
        return self.db.query(TechnologyInstance).filter(
            TechnologyInstance.technology_name == technology_name
        ).all()
    
    async def get_instances_by_type(self, technology_type: str) -> List[TechnologyInstance]:
        """按技术类型查询技术实例"""
        return self.db.query(TechnologyInstance).filter(
            TechnologyInstance.technology_type == technology_type
        ).all()
    
    async def get_instances_by_deployment_type(
        self, 
        deployment_type: str
    ) -> List[TechnologyInstance]:
        """按部署类型查询技术实例"""
        return self.db.query(TechnologyInstance).filter(
            TechnologyInstance.deployment_type == deployment_type
        ).all()
    
    async def update_technology_instance(
        self,
        instance_id: UUID,
        **kwargs
    ) -> Optional[TechnologyInstance]:
        """更新技术实例"""
        try:
            instance = await self.get_technology_instance(instance_id)
            if not instance:
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(instance, key) and value is not None:
                    setattr(instance, key, value)
            
            self.db.commit()
            self.db.refresh(instance)
            
            # 更新Neo4j节点
            if self.neo4j and instance.neo4j_node_id:
                await self._update_neo4j_node(instance)
            
            return instance
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating technology instance: {str(e)}", exc_info=True)
            raise
    
    async def delete_technology_instance(self, instance_id: UUID) -> bool:
        """删除技术实例"""
        try:
            instance = await self.get_technology_instance(instance_id)
            if not instance:
                return False
            
            tech_type_id = instance.technology_type_id
            
            # 删除Neo4j节点
            if self.neo4j and instance.neo4j_node_id:
                await self.neo4j.delete_node(instance.neo4j_node_id)
            
            self.db.delete(instance)
            self.db.commit()
            
            # 更新技术类型的实例计数
            if tech_type_id:
                await self._update_technology_type_count(tech_type_id)
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting technology instance: {str(e)}", exc_info=True)
            raise
    
    # ========== 查询方法 ==========
    
    async def search_instances(
        self,
        keyword: Optional[str] = None,
        technology_type: Optional[str] = None,
        technology_name: Optional[str] = None,
        deployment_type: Optional[str] = None,
        status: Optional[str] = None,
        system_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """搜索技术实例"""
        query = self.db.query(TechnologyInstance)
        
        # 应用过滤条件
        if keyword:
            query = query.filter(
                or_(
                    TechnologyInstance.name.ilike(f"%{keyword}%"),
                    TechnologyInstance.instance_id.ilike(f"%{keyword}%"),
                    TechnologyInstance.technology_name.ilike(f"%{keyword}%")
                )
            )
        
        if technology_type:
            query = query.filter(TechnologyInstance.technology_type == technology_type)
        
        if technology_name:
            query = query.filter(TechnologyInstance.technology_name == technology_name)
        
        if deployment_type:
            query = query.filter(TechnologyInstance.deployment_type == deployment_type)
        
        if status:
            query = query.filter(TechnologyInstance.status == status)
        
        if system_id:
            query = query.filter(TechnologyInstance.application_system_id == system_id)
        
        # 获取总数
        total = query.count()
        
        # 分页
        instances = query.offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "items": instances,
            "offset": offset,
            "limit": limit
        }
    
    async def get_technology_statistics(self) -> Dict[str, Any]:
        """获取技术统计信息"""
        # 按技术类型统计
        type_stats = self.db.query(
            TechnologyInstance.technology_type,
            func.count(TechnologyInstance.id).label('count')
        ).group_by(TechnologyInstance.technology_type).all()
        
        # 按技术名称统计
        name_stats = self.db.query(
            TechnologyInstance.technology_name,
            func.count(TechnologyInstance.id).label('count')
        ).group_by(TechnologyInstance.technology_name).all()
        
        # 按部署类型统计
        deployment_stats = self.db.query(
            TechnologyInstance.deployment_type,
            func.count(TechnologyInstance.id).label('count')
        ).group_by(TechnologyInstance.deployment_type).all()
        
        # 按状态统计
        status_stats = self.db.query(
            TechnologyInstance.status,
            func.count(TechnologyInstance.id).label('count')
        ).group_by(TechnologyInstance.status).all()
        
        return {
            "by_type": {stat[0]: stat[1] for stat in type_stats},
            "by_name": {stat[0]: stat[1] for stat in name_stats},
            "by_deployment": {stat[0]: stat[1] for stat in deployment_stats},
            "by_status": {stat[0]: stat[1] for stat in status_stats},
            "total": self.db.query(func.count(TechnologyInstance.id)).scalar() or 0
        }
    
    async def get_system_technology_stack(self, system_id: UUID) -> Dict[str, Any]:
        """获取系统的技术栈"""
        instances = await self.get_instances_by_system(system_id)
        
        # 按技术类型分组
        stack = {}
        for instance in instances:
            tech_type = instance.technology_type
            if tech_type not in stack:
                stack[tech_type] = []
            stack[tech_type].append({
                "id": str(instance.id),
                "name": instance.name,
                "technology_name": instance.technology_name,
                "version": instance.version,
                "vendor": instance.vendor,
                "deployment_type": instance.deployment_type,
                "status": instance.status
            })
        
        return {
            "system_id": str(system_id),
            "technology_stack": stack,
            "total_instances": len(instances)
        }
    
    # ========== 辅助方法 ==========
    
    async def _get_or_create_technology_type(
        self, name: str, category: str
    ) -> Optional[TechnologyType]:
        """获取或创建技术类型"""
        tech_type = self.db.query(TechnologyType).filter(
            TechnologyType.name == name,
            TechnologyType.category == category
        ).first()
        
        if not tech_type:
            tech_type = TechnologyType(
                name=name,
                category=category,
                lifecycle_status="strategic"
            )
            self.db.add(tech_type)
            self.db.commit()
            self.db.refresh(tech_type)
        
        return tech_type
    
    async def _update_technology_type_count(self, tech_type_id: UUID):
        """更新技术类型的实例计数"""
        count = self.db.query(func.count(TechnologyInstance.id)).filter(
            TechnologyInstance.technology_type_id == tech_type_id
        ).scalar() or 0
        
        tech_type = self.db.query(TechnologyType).filter(
            TechnologyType.id == tech_type_id
        ).first()
        
        if tech_type:
            tech_type.instance_count = count
            self.db.commit()
    
    async def _create_neo4j_node(self, instance: TechnologyInstance):
        """创建Neo4j技术实例节点"""
        if not self.neo4j:
            return
        
        try:
            node_id = await self.neo4j.create_node(
                labels=["TechnologyInstance", instance.technology_type],
                properties={
                    "uuid": str(instance.id),
                    "name": instance.name,
                    "instance_id": instance.instance_id,
                    "technology_type": instance.technology_type,
                    "technology_name": instance.technology_name,
                    "version": instance.version,
                    "vendor": instance.vendor,
                    "deployment_type": instance.deployment_type,
                    "host": instance.host,
                    "port": instance.port,
                    "location": instance.location,
                    "capacity": instance.capacity,
                    "status": instance.status
                }
            )
            
            instance.neo4j_node_id = node_id
            self.db.commit()
            
            # 创建与应用系统的关系
            if instance.application_system_id and instance.application_system:
                await self._create_application_relationship(instance)
            
            # 创建与技术类型的关系
            if instance.technology_type_id:
                await self._create_technology_type_relationship(instance)
        except Exception as e:
            logger.error(f"Error creating Neo4j node for technology instance: {str(e)}", exc_info=True)
    
    async def _update_neo4j_node(self, instance: TechnologyInstance):
        """更新Neo4j节点"""
        if not self.neo4j or not instance.neo4j_node_id:
            return
        
        try:
            await self.neo4j.update_node(
                node_id=instance.neo4j_node_id,
                properties={
                    "name": instance.name,
                    "instance_id": instance.instance_id,
                    "version": instance.version,
                    "status": instance.status,
                    "host": instance.host,
                    "port": instance.port
                }
            )
        except Exception as e:
            logger.error(f"Error updating Neo4j node: {str(e)}", exc_info=True)
    
    async def _create_application_relationship(self, instance: TechnologyInstance):
        """创建技术实例与应用系统的关系"""
        system = instance.application_system
        if system and system.neo4j_node_id and instance.neo4j_node_id:
            await self.neo4j.create_relationship(
                source_id=system.neo4j_node_id,
                target_id=instance.neo4j_node_id,
                rel_type="USES",
                properties={
                    "usage_type": "primary" if instance.technology_type == "Database" else "supporting",
                    "deployment_type": instance.deployment_type,
                    "created_at": instance.created_at.isoformat() if instance.created_at else None
                }
            )
    
    async def _create_technology_type_relationship(self, instance: TechnologyInstance):
        """创建技术实例与技术类型的关系"""
        tech_type = self.db.query(TechnologyType).filter(
            TechnologyType.id == instance.technology_type_id
        ).first()
        
        if tech_type and tech_type.neo4j_node_id and instance.neo4j_node_id:
            await self.neo4j.create_relationship(
                source_id=instance.neo4j_node_id,
                target_id=tech_type.neo4j_node_id,
                rel_type="INSTANCE_OF",
                properties={
                    "created_at": instance.created_at.isoformat() if instance.created_at else None
                }
            )

