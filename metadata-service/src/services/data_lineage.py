"""
数据血缘服务
提供数据血缘关系的管理和查询
"""
import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from ..models.lineage import (
    DataLineage,
    DataLineageSchema,
    DataLineageCreate,
    LineageNode,
    LineageEdge,
    LineageGraph,
    LineageRelationType,
    LineageType,
    ImpactAnalysis,
    RootCauseAnalysis,
    DataLineageDetail
)
from ..models.data_asset import DataAsset
from ..models.ai_model import AIModel
from ..models.workflow_metadata import WorkflowMetadata

logger = logging.getLogger(__name__)


class DataLineageService:
    """数据血缘服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_lineage(self, lineage_data: DataLineageCreate) -> DataLineageSchema:
        """创建血缘关系"""
        # 准备数据，确保source_asset和target_asset字段被设置
        data = lineage_data.model_dump()
        
        # 如果未设置asset字段，从type和id构建
        if not data.get("source_asset") and data.get("source_type") and data.get("source_id"):
            data["source_asset"] = f"{data['source_type']}:{data['source_id']}"
        if not data.get("target_asset") and data.get("target_type") and data.get("target_id"):
            data["target_asset"] = f"{data['target_type']}:{data['target_id']}"
        
        lineage = DataLineage(**data)
        self.db.add(lineage)
        self.db.commit()
        self.db.refresh(lineage)
        return DataLineageSchema.model_validate(lineage)
    
    def get_lineage(self, lineage_id: int) -> Optional[DataLineageSchema]:
        """获取血缘关系"""
        lineage = self.db.query(DataLineage).filter(DataLineage.id == lineage_id).first()
        return DataLineageSchema.model_validate(lineage) if lineage else None
    
    def list_lineage(
        self,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[LineageRelationType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DataLineageSchema]:
        """列出血缘关系"""
        query = self.db.query(DataLineage)
        
        if source_type:
            query = query.filter(DataLineage.source_type == source_type)
        if source_id:
            query = query.filter(DataLineage.source_id == source_id)
        if target_type:
            query = query.filter(DataLineage.target_type == target_type)
        if target_id:
            query = query.filter(DataLineage.target_id == target_id)
        if relation_type:
            query = query.filter(DataLineage.relation_type == relation_type)
        
        lineages = query.offset(skip).limit(limit).all()
        return [DataLineageSchema.model_validate(lineage) for lineage in lineages]
    
    def get_upstream_lineage(
        self,
        entity_type: str,
        entity_id: str,
        max_depth: int = 10
    ) -> LineageGraph:
        """获取上游血缘（数据来源）"""
        nodes: Set[str] = set()
        edges: List[LineageEdge] = []
        visited: Set[tuple] = set()
        
        def traverse_upstream(current_type: str, current_id: str, depth: int):
            if depth > max_depth:
                return
            
            key = (current_type, current_id)
            if key in visited:
                return
            visited.add(key)
            
            # 获取当前实体的信息
            node_info = self._get_entity_info(current_type, current_id)
            if node_info:
                nodes.add(f"{current_type}:{current_id}")
            
            # 查找上游关系
            upstream = self.db.query(DataLineage).filter(
                and_(
                    DataLineage.target_type == current_type,
                    DataLineage.target_id == current_id
                )
            ).all()
            
            for lineage in upstream:
                source_key = f"{lineage.source_type}:{lineage.source_id}"
                target_key = f"{lineage.target_type}:{lineage.target_id}"
                
                nodes.add(source_key)
                nodes.add(target_key)
                
                edges.append(LineageEdge(
                    source=source_key,
                    target=target_key,
                    relation_type=lineage.relation_type,
                    lineage_type=lineage.lineage_type,
                    transformation_logic=lineage.transformation_logic,
                    metadata={"id": lineage.id}
                ))
                
                # 递归查找上游
                traverse_upstream(lineage.source_type, lineage.source_id, depth + 1)
        
        traverse_upstream(entity_type, entity_id, 0)
        
        # 构建节点列表
        node_list = []
        for node_key in nodes:
            entity_type, entity_id = node_key.split(":", 1)
            node_info = self._get_entity_info(entity_type, entity_id)
            if node_info:
                node_list.append(LineageNode(
                    id=node_key,
                    type=entity_type,
                    name=node_info.get("name", entity_id),
                    display_name=node_info.get("display_name"),
                    metadata=node_info
                ))
        
        return LineageGraph(nodes=node_list, edges=edges)
    
    def get_downstream_lineage(
        self,
        entity_type: str,
        entity_id: str,
        max_depth: int = 10
    ) -> LineageGraph:
        """获取下游血缘（数据去向）"""
        nodes: Set[str] = set()
        edges: List[LineageEdge] = []
        visited: Set[tuple] = set()
        
        def traverse_downstream(current_type: str, current_id: str, depth: int):
            if depth > max_depth:
                return
            
            key = (current_type, current_id)
            if key in visited:
                return
            visited.add(key)
            
            # 获取当前实体的信息
            node_info = self._get_entity_info(current_type, current_id)
            if node_info:
                nodes.add(f"{current_type}:{current_id}")
            
            # 查找下游关系
            downstream = self.db.query(DataLineage).filter(
                and_(
                    DataLineage.source_type == current_type,
                    DataLineage.source_id == current_id
                )
            ).all()
            
            for lineage in downstream:
                source_key = f"{lineage.source_type}:{lineage.source_id}"
                target_key = f"{lineage.target_type}:{lineage.target_id}"
                
                nodes.add(source_key)
                nodes.add(target_key)
                
                edges.append(LineageEdge(
                    source=source_key,
                    target=target_key,
                    relation_type=lineage.relation_type,
                    lineage_type=lineage.lineage_type,
                    transformation_logic=lineage.transformation_logic,
                    metadata={"id": lineage.id}
                ))
                
                # 递归查找下游
                traverse_downstream(lineage.target_type, lineage.target_id, depth + 1)
        
        traverse_downstream(entity_type, entity_id, 0)
        
        # 构建节点列表
        node_list = []
        for node_key in nodes:
            entity_type, entity_id = node_key.split(":", 1)
            node_info = self._get_entity_info(entity_type, entity_id)
            if node_info:
                node_list.append(LineageNode(
                    id=node_key,
                    type=entity_type,
                    name=node_info.get("name", entity_id),
                    display_name=node_info.get("display_name"),
                    metadata=node_info
                ))
        
        return LineageGraph(nodes=node_list, edges=edges)
    
    def get_full_lineage(
        self,
        entity_type: str,
        entity_id: str,
        max_depth: int = 10
    ) -> LineageGraph:
        """获取完整血缘（上游+下游）"""
        upstream = self.get_upstream_lineage(entity_type, entity_id, max_depth)
        downstream = self.get_downstream_lineage(entity_type, entity_id, max_depth)
        
        # 合并节点和边
        all_nodes = {node.id: node for node in upstream.nodes}
        for node in downstream.nodes:
            if node.id not in all_nodes:
                all_nodes[node.id] = node
        
        all_edges = upstream.edges + downstream.edges
        
        return LineageGraph(nodes=list(all_nodes.values()), edges=all_edges)
    
    def get_impact_analysis(self, asset_id: str, max_depth: int = 10) -> ImpactAnalysis:
        """影响分析 - 分析资产变更对下游的影响"""
        # 解析asset_id（格式：type:id 或直接是id）
        if ":" in asset_id:
            entity_type, entity_id = asset_id.split(":", 1)
        else:
            # 默认假设是data_asset
            entity_type = "data_asset"
            entity_id = asset_id
        
        # 获取下游血缘
        downstream_graph = self.get_downstream_lineage(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth
        )
        
        # 获取资产信息
        entity_info = self._get_entity_info(entity_type, entity_id)
        asset_name = entity_info.get("name", entity_id) if entity_info else entity_id
        
        # 统计影响
        all_impacted = set()
        direct_impacted = set()
        indirect_impacted = set()
        impact_paths = []
        
        for edge in downstream_graph.edges:
            target_key = edge.target
            if target_key not in all_impacted:
                all_impacted.add(target_key)
                direct_impacted.add(target_key)
            
            # 构建影响路径
            path = {
                "source": edge.source,
                "target": edge.target,
                "relation_type": edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type),
                "transformation": edge.transformation_logic,
                "depth": 1  # 简化处理，实际应该计算深度
            }
            impact_paths.append(path)
        
        # 计算间接影响（通过多跳关系）
        for node in downstream_graph.nodes:
            if node.id not in direct_impacted:
                indirect_impacted.add(node.id)
        
        # 构建受影响资产列表
        impacted_assets = []
        for node in downstream_graph.nodes:
            if node.id != f"{entity_type}:{entity_id}":
                impacted_assets.append({
                    "id": node.id,
                    "type": node.type,
                    "name": node.name,
                    "display_name": node.display_name,
                    "metadata": node.extra_metadata
                })
        
        # 评估风险等级
        total_impacted = len(all_impacted)
        if total_impacted == 0:
            risk_level = "low"
        elif total_impacted <= 5:
            risk_level = "medium"
        elif total_impacted <= 20:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # 生成建议
        recommendations = []
        if total_impacted > 0:
            recommendations.append(f"该资产变更将影响 {total_impacted} 个下游资产")
            if total_impacted > 10:
                recommendations.append("建议在变更前通知所有受影响方")
                recommendations.append("建议进行灰度发布，逐步验证影响")
            if len(indirect_impacted) > 0:
                recommendations.append(f"存在 {len(indirect_impacted)} 个间接影响，需要特别关注")
        
        return ImpactAnalysis(
            asset_id=asset_id,
            asset_type=entity_type,
            asset_name=asset_name,
            total_impacted=total_impacted,
            direct_impacted=len(direct_impacted),
            indirect_impacted=len(indirect_impacted),
            impacted_assets=impacted_assets,
            impact_paths=impact_paths,
            risk_level=risk_level,
            recommendations=recommendations,
            metadata={
                "max_depth": max_depth,
                "analysis_time": datetime.now().isoformat()
            }
        )
    
    def get_root_cause_analysis(self, asset_id: str, max_depth: int = 10) -> RootCauseAnalysis:
        """根因分析 - 分析资产问题的上游根因"""
        # 解析asset_id
        if ":" in asset_id:
            entity_type, entity_id = asset_id.split(":", 1)
        else:
            entity_type = "data_asset"
            entity_id = asset_id
        
        # 获取上游血缘
        upstream_graph = self.get_upstream_lineage(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth
        )
        
        # 获取资产信息
        entity_info = self._get_entity_info(entity_type, entity_id)
        asset_name = entity_info.get("name", entity_id) if entity_info else entity_id
        
        # 统计来源
        all_sources = set()
        direct_sources = set()
        indirect_sources = set()
        source_paths = []
        critical_paths = []
        
        for edge in upstream_graph.edges:
            source_key = edge.source
            if source_key not in all_sources:
                all_sources.add(source_key)
                direct_sources.add(source_key)
            
            # 构建来源路径
            path = {
                "source": edge.source,
                "target": edge.target,
                "relation_type": edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type),
                "transformation": edge.transformation_logic,
                "lineage_type": edge.lineage_type.value if hasattr(edge.lineage_type, 'value') else str(edge.lineage_type),
                "depth": 1
            }
            source_paths.append(path)
            
            # 识别关键路径（数据流或转换关系）
            if edge.lineage_type == LineageType.DATA_FLOW or edge.lineage_type == LineageType.TRANSFORMATION:
                critical_paths.append(path)
        
        # 计算间接来源
        for node in upstream_graph.nodes:
            if node.id not in direct_sources and node.id != f"{entity_type}:{entity_id}":
                indirect_sources.add(node.id)
        
        # 构建来源资产列表
        source_assets = []
        for node in upstream_graph.nodes:
            if node.id != f"{entity_type}:{entity_id}":
                source_assets.append({
                    "id": node.id,
                    "type": node.type,
                    "name": node.name,
                    "display_name": node.display_name,
                    "metadata": node.extra_metadata
                })
        
        # 检查数据质量问题（从血缘关系中提取）
        data_quality_issues = []
        for edge in upstream_graph.edges:
            if edge.extra_metadata and edge.extra_metadata.get("data_quality_impact"):
                issue = {
                    "source": edge.source,
                    "issue_type": edge.extra_metadata.get("data_quality_impact", {}).get("issue_type"),
                    "severity": edge.extra_metadata.get("data_quality_impact", {}).get("severity", "medium"),
                    "description": edge.extra_metadata.get("data_quality_impact", {}).get("description")
                }
                data_quality_issues.append(issue)
        
        # 生成建议
        recommendations = []
        if len(all_sources) > 0:
            recommendations.append(f"该资产依赖 {len(all_sources)} 个上游资产")
            if len(critical_paths) > 0:
                recommendations.append(f"存在 {len(critical_paths)} 条关键数据流路径，需要重点监控")
            if len(data_quality_issues) > 0:
                recommendations.append(f"发现 {len(data_quality_issues)} 个数据质量问题，建议优先处理")
            if len(indirect_sources) > 0:
                recommendations.append(f"存在 {len(indirect_sources)} 个间接来源，需要追踪完整链路")
        
        return RootCauseAnalysis(
            asset_id=asset_id,
            asset_type=entity_type,
            asset_name=asset_name,
            total_sources=len(all_sources),
            direct_sources=len(direct_sources),
            indirect_sources=len(indirect_sources),
            source_assets=source_assets,
            source_paths=source_paths,
            critical_paths=critical_paths,
            data_quality_issues=data_quality_issues,
            recommendations=recommendations,
            metadata={
                "max_depth": max_depth,
                "analysis_time": datetime.now().isoformat()
            }
        )
    
    def get_data_lineage_detail(self, asset_id: str, max_depth: int = 10) -> DataLineageDetail:
        """获取数据血缘详情（包含完整图谱和分析）"""
        # 解析asset_id
        if ":" in asset_id:
            entity_type, entity_id = asset_id.split(":", 1)
        else:
            entity_type = "data_asset"
            entity_id = asset_id
        
        # 获取完整血缘
        full_lineage = self.get_full_lineage(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth
        )
        
        # 获取上游和下游
        upstream_graph = self.get_upstream_lineage(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth
        )
        downstream_graph = self.get_downstream_lineage(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth
        )
        
        # 获取资产信息
        entity_info = self._get_entity_info(entity_type, entity_id)
        asset_name = entity_info.get("name", entity_id) if entity_info else entity_id
        
        # 执行分析
        impact_analysis = self.get_impact_analysis(asset_id, max_depth)
        root_cause_analysis = self.get_root_cause_analysis(asset_id, max_depth)
        
        return DataLineageDetail(
            asset_id=asset_id,
            asset_type=entity_type,
            asset_name=asset_name,
            lineage_graph=full_lineage,
            upstream_count=len(upstream_graph.nodes),
            downstream_count=len(downstream_graph.nodes),
            total_relations=len(full_lineage.edges),
            impact_analysis=impact_analysis,
            root_cause_analysis=root_cause_analysis,
            metadata={
                "max_depth": max_depth,
                "analysis_time": datetime.now().isoformat()
            }
        )
    
    def _get_entity_info(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """获取实体信息"""
        try:
            if entity_type == "data_asset":
                asset = self.db.query(DataAsset).filter(DataAsset.id == int(entity_id)).first()
                if asset:
                    return {
                        "name": asset.name,
                        "display_name": asset.display_name,
                        "type": asset.asset_type.value if asset.asset_type else None
                    }
            elif entity_type == "ai_model":
                model = self.db.query(AIModel).filter(AIModel.id == int(entity_id)).first()
                if model:
                    return {
                        "name": model.name,
                        "display_name": model.display_name,
                        "type": model.model_type.value if model.model_type else None
                    }
            elif entity_type == "workflow":
                workflow = self.db.query(WorkflowMetadata).filter(
                    WorkflowMetadata.workflow_id == entity_id
                ).first()
                if workflow:
                    return {
                        "name": workflow.name,
                        "display_name": workflow.display_name,
                        "type": workflow.workflow_type
                    }
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to get entity info for {entity_type}:{entity_id}: {str(e)}")
        
        return None
    
    def delete_lineage(self, lineage_id: int) -> bool:
        """删除血缘关系"""
        lineage = self.db.query(DataLineage).filter(DataLineage.id == lineage_id).first()
        if not lineage:
            return False
        
        self.db.delete(lineage)
        self.db.commit()
        return True

