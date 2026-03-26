"""
元数据目录服务
提供元数据的CRUD操作和目录管理
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, cast, String

from ..models.data_asset import DataAsset, DataAssetSchema, DataAssetCreate, DataAssetUpdate
from ..models.ai_model import AIModel, AIModelSchema, AIModelCreate, AIModelUpdate
from ..models.business_entity import BusinessEntity, BusinessEntitySchema, BusinessEntityCreate, BusinessEntityUpdate
from ..models.workflow_metadata import WorkflowMetadata, WorkflowMetadataSchema, WorkflowMetadataCreate, WorkflowMetadataUpdate

logger = logging.getLogger(__name__)


class MetadataCatalogService:
    """元数据目录服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== 数据资产操作 ==========
    
    def create_data_asset(self, asset_data: DataAssetCreate) -> DataAssetSchema:
        """创建数据资产"""
        asset = DataAsset(**asset_data.model_dump())
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return DataAssetSchema.model_validate(asset)
    
    def get_data_asset(self, asset_id: int) -> Optional[DataAssetSchema]:
        """获取数据资产"""
        asset = self.db.query(DataAsset).filter(DataAsset.id == asset_id).first()
        return DataAssetSchema.model_validate(asset) if asset else None
    
    def list_data_assets(
        self,
        skip: int = 0,
        limit: int = 20,
        asset_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        classification: Optional[str] = None,
        business_domain: Optional[str] = None,
        technical_source: Optional[str] = None,
        lifecycle_stage: Optional[str] = None,
        standardized_tag: Optional[str] = None,
        quality_score: Optional[float] = None
    ) -> List[DataAssetSchema]:
        """列出数据资产"""
        from sqlalchemy import func, cast, String
        
        query = self.db.query(DataAsset)
        
        if asset_type:
            # 验证 asset_type 是否为有效的枚举值
            # 如果传入的是中文值（如"组织架构数据"），则忽略该过滤条件
            try:
                # 尝试将字符串转换为枚举值
                from ..models.data_asset import DataAssetType
                # 检查是否是有效的枚举值
                valid_types = [e.value for e in DataAssetType]
                if asset_type in valid_types:
                    query = query.filter(DataAsset.asset_type == asset_type)
                else:
                    # 如果不是有效的枚举值（可能是中文值），记录警告并忽略该过滤条件
                    logger.warning(f"Invalid asset_type value '{asset_type}', ignoring filter. Valid values: {valid_types}")
            except Exception as e:
                logger.warning(f"Error validating asset_type '{asset_type}': {e}, ignoring filter")
        if status:
            query = query.filter(DataAsset.status == status)
        if search:
            query = query.filter(
                or_(
                    DataAsset.name.ilike(f"%{search}%"),
                    DataAsset.display_name.ilike(f"%{search}%"),
                    DataAsset.description.ilike(f"%{search}%")
                )
            )
        if category:
            # category存储在metadata JSON字段中
            query = query.filter(
                func.cast(DataAsset.extra_metadata, String).ilike(f'%"category": "{category}"%')
            )
        if domain:
            # domain存储在metadata JSON字段中
            query = query.filter(
                func.cast(DataAsset.extra_metadata, String).ilike(f'%"domain": "{domain}"%')
            )
        if classification:
            # classification存储在classification字段中
            query = query.filter(DataAsset.classification == classification)
        if quality_score is not None:
            # quality_score存储在data_quality_metrics JSON字段中
            # 使用JSON路径查询（PostgreSQL支持）
            query = query.filter(
                func.cast(DataAsset.data_quality_metrics, String).ilike(f'%"quality_score": {quality_score}%')
            )
            # 或者使用更精确的JSON查询（如果数据库支持）
            # query = query.filter(DataAsset.data_quality_metrics['quality_score'].astext.cast(float) >= quality_score)
        
        assets = query.offset(skip).limit(limit).all()
        return [DataAssetSchema.model_validate(asset) for asset in assets]
    
    def count_data_assets(
        self,
        asset_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        classification: Optional[str] = None,
        business_domain: Optional[str] = None,
        technical_source: Optional[str] = None,
        lifecycle_stage: Optional[str] = None,
        standardized_tag: Optional[str] = None,
        quality_score: Optional[float] = None
    ) -> int:
        """统计数据资产总数"""
        from sqlalchemy import func, cast, String, or_
        
        query = self.db.query(func.count(DataAsset.id))
        
        if asset_type:
            # 验证 asset_type 是否为有效的枚举值
            # 如果传入的是中文值（如"组织架构数据"），则忽略该过滤条件
            try:
                # 尝试将字符串转换为枚举值
                from ..models.data_asset import DataAssetType
                # 检查是否是有效的枚举值
                valid_types = [e.value for e in DataAssetType]
                if asset_type in valid_types:
                    query = query.filter(DataAsset.asset_type == asset_type)
                else:
                    # 如果不是有效的枚举值（可能是中文值），记录警告并忽略该过滤条件
                    logger.warning(f"Invalid asset_type value '{asset_type}' in count_data_assets, ignoring filter. Valid values: {valid_types}")
            except Exception as e:
                logger.warning(f"Error validating asset_type '{asset_type}' in count_data_assets: {e}, ignoring filter")
        if status:
            query = query.filter(DataAsset.status == status)
        if search:
            query = query.filter(
                or_(
                    DataAsset.name.ilike(f"%{search}%"),
                    DataAsset.display_name.ilike(f"%{search}%"),
                    DataAsset.description.ilike(f"%{search}%")
                )
            )
        if category:
            query = query.filter(
                func.cast(DataAsset.extra_metadata, String).ilike(f'%"category": "{category}"%')
            )
        if domain:
            query = query.filter(
                func.cast(DataAsset.extra_metadata, String).ilike(f'%"domain": "{domain}"%')
            )
        if classification:
            query = query.filter(DataAsset.classification == classification)
        if business_domain:
            query = query.filter(
                func.cast(DataAsset.classification_dimensions, String).ilike(f'%"business": {{%"domain": "{business_domain}"%')
            )
        if technical_source:
            query = query.filter(
                func.cast(DataAsset.classification_dimensions, String).ilike(f'%"technical": {{%"source": "{technical_source}"%')
            )
        if lifecycle_stage:
            query = query.filter(
                func.cast(DataAsset.classification_dimensions, String).ilike(f'%"lifecycle": {{%"stage": "{lifecycle_stage}"%')
            )
        if standardized_tag:
            query = query.filter(
                func.cast(DataAsset.standardized_tags, String).ilike(f'%"{standardized_tag}"%')
            )
        if quality_score is not None:
            query = query.filter(
                func.cast(DataAsset.data_quality_metrics, String).ilike(f'%"quality_score": {quality_score}%')
            )
        
        return query.scalar() or 0
    
    def update_data_asset(self, asset_id: int, asset_data: DataAssetUpdate) -> Optional[DataAssetSchema]:
        """更新数据资产"""
        asset = self.db.query(DataAsset).filter(DataAsset.id == asset_id).first()
        if not asset:
            return None
        
        update_data = asset_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(asset, key, value)
        
        self.db.commit()
        self.db.refresh(asset)
        return DataAssetSchema.model_validate(asset)
    
    def delete_data_asset(self, asset_id: int) -> bool:
        """删除数据资产"""
        asset = self.db.query(DataAsset).filter(DataAsset.id == asset_id).first()
        if not asset:
            return False
        
        self.db.delete(asset)
        self.db.commit()
        return True
    
    # ========== AI模型操作 ==========
    
    def create_ai_model(self, model_data: AIModelCreate) -> AIModelSchema:
        """创建AI模型"""
        # 确保枚举值转换为小写字符串（数据库枚举类型使用小写）
        dump_data = model_data.model_dump()
        
        # 处理model_type：转换为小写字符串
        if 'model_type' in dump_data:
            mt = dump_data['model_type']
            if isinstance(mt, str):
                dump_data['model_type'] = mt.lower()
            elif hasattr(mt, 'value'):
                dump_data['model_type'] = mt.value.lower()
            elif hasattr(mt, 'name'):
                # 如果是枚举对象，获取值
                dump_data['model_type'] = mt.value.lower() if hasattr(mt, 'value') else str(mt).lower()
        
        # 处理status：转换为小写字符串
        if 'status' in dump_data:
            st = dump_data['status']
            if isinstance(st, str):
                dump_data['status'] = st.lower()
            elif hasattr(st, 'value'):
                dump_data['status'] = st.value.lower()
            elif hasattr(st, 'name'):
                dump_data['status'] = st.value.lower() if hasattr(st, 'value') else str(st).lower()
        
        # 手动创建模型对象，确保枚举值正确
        from ..models.ai_model import ModelType, ModelStatus
        model = AIModel(
            name=dump_data['name'],
            display_name=dump_data.get('display_name'),
            description=dump_data.get('description'),
            model_type=ModelType(dump_data['model_type']),  # 使用枚举构造函数
            status=ModelStatus(dump_data.get('status', 'active')),
            model_version=dump_data.get('model_version'),
            framework=dump_data.get('framework'),
            model_path=dump_data.get('model_path'),
            model_size=dump_data.get('model_size'),
            training_dataset=dump_data.get('training_dataset'),
            training_config=dump_data.get('training_config'),
            hyperparameters=dump_data.get('hyperparameters'),
            training_metrics=dump_data.get('training_metrics'),
            accuracy=dump_data.get('accuracy'),
            precision=dump_data.get('precision'),
            recall=dump_data.get('recall'),
            f1_score=dump_data.get('f1_score'),
            performance_metrics=dump_data.get('performance_metrics'),
            deployment_endpoint=dump_data.get('deployment_endpoint'),
            deployment_config=dump_data.get('deployment_config'),
            inference_latency=dump_data.get('inference_latency'),
            business_owner=dump_data.get('business_owner'),
            technical_owner=dump_data.get('technical_owner'),
            tags=dump_data.get('tags'),
            use_cases=dump_data.get('use_cases'),
            extra_metadata=dump_data.get('metadata')
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return AIModelSchema.model_validate(model)
    
    def get_ai_model(self, model_id: int) -> Optional[AIModelSchema]:
        """获取AI模型"""
        model = self.db.query(AIModel).filter(AIModel.id == model_id).first()
        return AIModelSchema.model_validate(model) if model else None
    
    def list_ai_models(
        self,
        skip: int = 0,
        limit: int = 20,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[AIModelSchema]:
        """列出AI模型"""
        query = self.db.query(AIModel)
        
        if model_type:
            query = query.filter(AIModel.model_type == model_type)
        if status:
            query = query.filter(AIModel.status == status)
        if search:
            query = query.filter(
                or_(
                    AIModel.name.ilike(f"%{search}%"),
                    AIModel.display_name.ilike(f"%{search}%"),
                    AIModel.description.ilike(f"%{search}%")
                )
            )
        if business_domain:
            query = query.filter(
                func.cast(AIModel.classification_dimensions, String).ilike(f'%"business": {{%"domain": "{business_domain}"%')
            )
        if lifecycle_status:
            query = query.filter(
                func.cast(AIModel.classification_dimensions, String).ilike(f'%"lifecycle": {{%"status": "{lifecycle_status}"%')
            )
        if standardized_tag:
            query = query.filter(
                func.cast(AIModel.standardized_tags, String).ilike(f'%"{standardized_tag}"%')
            )
        
        models = query.offset(skip).limit(limit).all()
        return [AIModelSchema.model_validate(model) for model in models]
    
    def update_ai_model(self, model_id: int, model_data: AIModelUpdate) -> Optional[AIModelSchema]:
        """更新AI模型"""
        model = self.db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            return None
        
        update_data = model_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
        
        self.db.commit()
        self.db.refresh(model)
        return AIModelSchema.model_validate(model)
    
    def delete_ai_model(self, model_id: int) -> bool:
        """删除AI模型"""
        model = self.db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            return False
        
        self.db.delete(model)
        self.db.commit()
        return True
    
    # ========== 业务实体操作 ==========
    
    def create_business_entity(self, entity_data: BusinessEntityCreate) -> BusinessEntitySchema:
        """创建业务实体"""
        # 确保枚举值转换为小写字符串（数据库枚举类型使用小写）
        dump_data = entity_data.model_dump()
        
        # 处理entity_type：转换为小写字符串
        if 'entity_type' in dump_data:
            et = dump_data['entity_type']
            if isinstance(et, str):
                dump_data['entity_type'] = et.lower()
            elif hasattr(et, 'value'):
                dump_data['entity_type'] = et.value.lower()
            elif hasattr(et, 'name'):
                dump_data['entity_type'] = et.value.lower() if hasattr(et, 'value') else str(et).lower()
        
        # 手动创建实体对象，确保枚举值正确
        from ..models.business_entity import EntityType
        entity = BusinessEntity(
            name=dump_data['name'],
            display_name=dump_data.get('display_name'),
            description=dump_data.get('description'),
            entity_type=EntityType(dump_data['entity_type']),  # 使用枚举构造函数
            parent_id=dump_data.get('parent_id'),
            business_definition=dump_data.get('business_definition'),
            business_rules=dump_data.get('business_rules'),
            data_dictionary=dump_data.get('data_dictionary'),
            related_entities=dump_data.get('related_entities'),
            related_data_assets=dump_data.get('related_data_assets'),
            related_models=dump_data.get('related_models'),
            data_steward=dump_data.get('data_steward'),
            business_owner=dump_data.get('business_owner'),
            classification=dump_data.get('classification'),
            tags=dump_data.get('tags'),
            extra_metadata=dump_data.get('metadata')
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return BusinessEntitySchema.model_validate(entity)
    
    def create_business_entities_batch(
        self,
        entities_data: List[BusinessEntityCreate],
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        批量创建业务实体
        
        Args:
            entities_data: 业务实体数据列表
            skip_duplicates: 是否跳过重复的实体（基于name）
            
        Returns:
            创建结果，包含created、skipped、errors
        """
        result = {
            "created": 0,
            "skipped": 0,
            "errors": []
        }
        
        # 如果启用跳过重复，先检查已存在的实体
        existing_names = set()
        if skip_duplicates:
            entity_names = [e.name for e in entities_data]
            existing_entities = self.db.query(BusinessEntity).filter(
                BusinessEntity.name.in_(entity_names)
            ).all()
            existing_names = {e.name for e in existing_entities}
        
        from ..models.business_entity import EntityType
        
        for entity_data in entities_data:
            try:
                # 检查是否已存在
                if skip_duplicates and entity_data.name in existing_names:
                    result["skipped"] += 1
                    continue
                
                # 创建实体（复用create_business_entity的逻辑）
                dump_data = entity_data.model_dump()
                
                # 处理entity_type
                if 'entity_type' in dump_data:
                    et = dump_data['entity_type']
                    if isinstance(et, str):
                        dump_data['entity_type'] = et.lower()
                    elif hasattr(et, 'value'):
                        dump_data['entity_type'] = et.value.lower()
                    elif hasattr(et, 'name'):
                        dump_data['entity_type'] = et.value.lower() if hasattr(et, 'value') else str(et).lower()
                
                entity = BusinessEntity(
                    name=dump_data['name'],
                    display_name=dump_data.get('display_name'),
                    description=dump_data.get('description'),
                    entity_type=EntityType(dump_data['entity_type']),
                    parent_id=dump_data.get('parent_id'),
                    business_definition=dump_data.get('business_definition'),
                    business_rules=dump_data.get('business_rules'),
                    data_dictionary=dump_data.get('data_dictionary'),
                    related_entities=dump_data.get('related_entities'),
                    related_data_assets=dump_data.get('related_data_assets'),
                    related_models=dump_data.get('related_models'),
                    data_steward=dump_data.get('data_steward'),
                    business_owner=dump_data.get('business_owner'),
                    classification=dump_data.get('classification'),
                    tags=dump_data.get('tags'),
                    extra_metadata=dump_data.get('metadata')
                )
                self.db.add(entity)
                result["created"] += 1
                
            except Exception as e:
                error_msg = f"Failed to create entity '{entity_data.name}': {str(e)}"
                logger.error(error_msg, exc_info=True)
                result["errors"].append(error_msg)
        
        # 批量提交
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            error_msg = f"Failed to commit batch: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["errors"].append(error_msg)
            result["created"] = 0  # 回滚后，创建数归零
        
        return result
    
    def get_business_entity(self, entity_id: int) -> Optional[BusinessEntitySchema]:
        """获取业务实体"""
        entity = self.db.query(BusinessEntity).filter(BusinessEntity.id == entity_id).first()
        return BusinessEntitySchema.model_validate(entity) if entity else None
    
    def list_business_entities(
        self,
        skip: int = 0,
        limit: int = 20,
        entity_type: Optional[str] = None,
        parent_id: Optional[int] = None,
        search: Optional[str] = None,
        business_domain: Optional[str] = None,
        standardized_tag: Optional[str] = None
    ) -> List[BusinessEntitySchema]:
        """列出业务实体"""
        query = self.db.query(BusinessEntity)
        
        if entity_type:
            query = query.filter(BusinessEntity.entity_type == entity_type)
        if parent_id is not None:
            query = query.filter(BusinessEntity.parent_id == parent_id)
        if search:
            query = query.filter(
                or_(
                    BusinessEntity.name.ilike(f"%{search}%"),
                    BusinessEntity.display_name.ilike(f"%{search}%"),
                    BusinessEntity.description.ilike(f"%{search}%")
                )
            )
        if business_domain:
            query = query.filter(
                func.cast(BusinessEntity.classification_dimensions, String).ilike(f'%"business": {{%"domain": "{business_domain}"%')
            )
        if standardized_tag:
            query = query.filter(
                func.cast(BusinessEntity.standardized_tags, String).ilike(f'%"{standardized_tag}"%')
            )
        
        entities = query.offset(skip).limit(limit).all()
        return [BusinessEntitySchema.model_validate(entity) for entity in entities]
    
    def update_business_entity(self, entity_id: int, entity_data: BusinessEntityUpdate) -> Optional[BusinessEntitySchema]:
        """更新业务实体"""
        entity = self.db.query(BusinessEntity).filter(BusinessEntity.id == entity_id).first()
        if not entity:
            return None
        
        update_data = entity_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entity, key, value)
        
        self.db.commit()
        self.db.refresh(entity)
        return BusinessEntitySchema.model_validate(entity)
    
    def delete_business_entity(self, entity_id: int) -> bool:
        """删除业务实体"""
        entity = self.db.query(BusinessEntity).filter(BusinessEntity.id == entity_id).first()
        if not entity:
            return False
        
        self.db.delete(entity)
        self.db.commit()
        return True
    
    # ========== 工作流元数据操作 ==========
    
    def create_workflow_metadata(self, workflow_data: WorkflowMetadataCreate) -> WorkflowMetadataSchema:
        """创建工作流元数据"""
        data = workflow_data.model_dump()
        existing = self.db.query(WorkflowMetadata).filter(
            WorkflowMetadata.workflow_id == data.get("workflow_id")
        ).first()
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return WorkflowMetadataSchema.model_validate(existing)

        workflow = WorkflowMetadata(**data)
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return WorkflowMetadataSchema.model_validate(workflow)
    
    def get_workflow_metadata(self, workflow_id: str) -> Optional[WorkflowMetadataSchema]:
        """获取工作流元数据（通过workflow_id）"""
        workflow = self.db.query(WorkflowMetadata).filter(WorkflowMetadata.workflow_id == workflow_id).first()
        return WorkflowMetadataSchema.model_validate(workflow) if workflow else None
    
    def get_workflow_metadata_by_id(self, id: int) -> Optional[WorkflowMetadataSchema]:
        """获取工作流元数据（通过id）"""
        workflow = self.db.query(WorkflowMetadata).filter(WorkflowMetadata.id == id).first()
        return WorkflowMetadataSchema.model_validate(workflow) if workflow else None
    
    def list_workflow_metadata(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        business_domain: Optional[str] = None,
        standardized_tag: Optional[str] = None
    ) -> List[WorkflowMetadataSchema]:
        """列出工作流元数据"""
        query = self.db.query(WorkflowMetadata)
        
        if status:
            query = query.filter(WorkflowMetadata.status == status)
        if category:
            query = query.filter(WorkflowMetadata.category == category)
        if search:
            query = query.filter(
                or_(
                    WorkflowMetadata.name.ilike(f"%{search}%"),
                    WorkflowMetadata.display_name.ilike(f"%{search}%"),
                    WorkflowMetadata.description.ilike(f"%{search}%")
                )
            )
        if business_domain:
            query = query.filter(
                func.cast(WorkflowMetadata.classification_dimensions, String).ilike(f'%"business": {{%"domain": "{business_domain}"%')
            )
        if standardized_tag:
            query = query.filter(
                func.cast(WorkflowMetadata.standardized_tags, String).ilike(f'%"{standardized_tag}"%')
            )
        
        workflows = query.offset(skip).limit(limit).all()
        return [WorkflowMetadataSchema.model_validate(workflow) for workflow in workflows]
    
    def update_workflow_metadata(self, workflow_id: str, workflow_data: WorkflowMetadataUpdate) -> Optional[WorkflowMetadataSchema]:
        """更新工作流元数据"""
        workflow = self.db.query(WorkflowMetadata).filter(WorkflowMetadata.workflow_id == workflow_id).first()
        if not workflow:
            return None
        
        update_data = workflow_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(workflow, key, value)
        
        self.db.commit()
        self.db.refresh(workflow)
        return WorkflowMetadataSchema.model_validate(workflow)
    
    def delete_workflow_metadata(self, workflow_id: str) -> bool:
        """删除工作流元数据"""
        workflow = self.db.query(WorkflowMetadata).filter(WorkflowMetadata.workflow_id == workflow_id).first()
        if not workflow:
            return False
        
        self.db.delete(workflow)
        self.db.commit()
        return True
