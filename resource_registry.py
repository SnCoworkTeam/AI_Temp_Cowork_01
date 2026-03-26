"""
资源注册表
企业资源注册表（类似OS的设备注册表）
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging

try:
    from .resource_model import Resource, ResourceType
except ImportError:
    from resource_model import Resource, ResourceType

logger = logging.getLogger(__name__)


class ResourceRegistry:
    """企业资源注册表"""
    
    def __init__(self):
        """初始化资源注册表"""
        # 按ID索引
        self._resources_by_id: Dict[str, Resource] = {}
        # 按类型索引
        self._resources_by_type: Dict[ResourceType, List[Resource]] = defaultdict(list)
        # 按URI索引
        self._resources_by_uri: Dict[str, Resource] = {}
        # 语义索引（用于发现）
        self._semantic_index: Dict[str, List[str]] = defaultdict(list)  # {keyword: [resource_ids]}
    
    def register(self, resource: Resource) -> bool:
        """
        注册资源
        
        Args:
            resource: 要注册的资源对象
            
        Returns:
            bool: 注册是否成功
        """
        try:
            # 检查是否已存在
            if resource.id in self._resources_by_id:
                logger.warning(f"资源 {resource.id} 已存在，将更新")
            
            # 注册到各个索引
            self._resources_by_id[resource.id] = resource
            self._resources_by_type[resource.type].append(resource)
            self._resources_by_uri[resource.uri] = resource
            
            # 更新语义索引（简单实现，基于名称和描述）
            keywords = self._extract_keywords(resource)
            for keyword in keywords:
                self._semantic_index[keyword].append(resource.id)
            
            logger.info(f"资源注册成功: {resource.id} ({resource.type.value})")
            return True
            
        except Exception as e:
            logger.error(f"资源注册失败: {resource.id}, 错误: {e}")
            return False
    
    def unregister(self, resource_id: str) -> bool:
        """
        注销资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            bool: 注销是否成功
        """
        if resource_id not in self._resources_by_id:
            logger.warning(f"资源 {resource_id} 不存在")
            return False
        
        resource = self._resources_by_id[resource_id]
        
        # 从各个索引中移除
        del self._resources_by_id[resource_id]
        if resource in self._resources_by_type[resource.type]:
            self._resources_by_type[resource.type].remove(resource)
        if resource.uri in self._resources_by_uri:
            del self._resources_by_uri[resource.uri]
        
        # 更新语义索引
        keywords = self._extract_keywords(resource)
        for keyword in keywords:
            if resource_id in self._semantic_index[keyword]:
                self._semantic_index[keyword].remove(resource_id)
        
        logger.info(f"资源注销成功: {resource_id}")
        return True
    
    def resolve(self, uri: str) -> Optional[Resource]:
        """
        解析URI到资源对象
        
        Args:
            uri: 统一资源标识符
            
        Returns:
            Resource对象，如果不存在则返回None
        """
        return self._resources_by_uri.get(uri)
    
    def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """
        根据ID获取资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            Resource对象，如果不存在则返回None
        """
        return self._resources_by_id.get(resource_id)
    
    def get_by_type(self, resource_type: ResourceType) -> List[Resource]:
        """
        根据类型获取资源列表
        
        Args:
            resource_type: 资源类型
            
        Returns:
            资源列表
        """
        return self._resources_by_type.get(resource_type, []).copy()
    
    def discover(
        self, 
        query: str, 
        resource_type: Optional[ResourceType] = None,
        limit: int = 10
    ) -> List[Resource]:
        """
        发现资源（语义搜索）
        
        Args:
            query: 查询字符串
            resource_type: 可选的资源类型过滤
            limit: 返回结果数量限制
            
        Returns:
            匹配的资源列表
        """
        # 简单的关键词匹配实现
        # 实际应该使用向量搜索或更复杂的语义匹配
        query_keywords = self._extract_keywords_from_query(query)
        query_lower = query.lower()
        
        # 收集匹配的资源ID
        matched_ids = set()
        
        # 方法1：通过关键词索引匹配
        for keyword in query_keywords:
            if keyword in self._semantic_index:
                matched_ids.update(self._semantic_index[keyword])
        
        # 方法2：直接文本匹配（如果关键词匹配没有结果）
        if not matched_ids:
            for resource_id, resource in self._resources_by_id.items():
                # 检查名称和描述中是否包含查询词
                if (query_lower in resource.name.lower() or 
                    query_lower in resource.description.lower()):
                    matched_ids.add(resource_id)
        
        # 获取匹配的资源
        results = []
        for resource_id in matched_ids:
            resource = self._resources_by_id.get(resource_id)
            if resource:
                # 如果指定了资源类型，进行过滤
                if resource_type is None or resource.type == resource_type:
                    results.append(resource)
        
        # 按相关性排序（简单实现：按匹配关键词数量）
        results.sort(key=lambda r: sum(1 for kw in query_keywords if kw in self._extract_keywords(r)), reverse=True)
        
        return results[:limit]
    
    def get_relationships(self, resource_id: str) -> Dict[str, List[Resource]]:
        """
        获取资源关联关系
        
        Args:
            resource_id: 资源ID
            
        Returns:
            关联关系字典 {relation_type: [Resource]}
        """
        resource = self.get_by_id(resource_id)
        if not resource:
            return {}
        
        relationships = resource.get_relationships()
        result = {}
        
        for relation_type, related_ids in relationships.items():
            related_resources = []
            for related_id in related_ids:
                related_resource = self.get_by_id(related_id)
                if related_resource:
                    related_resources.append(related_resource)
            if related_resources:
                result[relation_type] = related_resources
        
        # EA增强：如果资源有EA实体ID，查询EA图谱获取更多关系
        try:
            ea_relationships = self._get_ea_relationships(resource)
            if ea_relationships:
                # 合并EA关系到结果
                for rel_type, related_resources in ea_relationships.items():
                    if rel_type not in result:
                        result[rel_type] = []
                    result[rel_type].extend(related_resources)
        except Exception as e:
            logger.debug(f"获取EA关系失败: {e}")
        
        return result
    
    def _get_ea_relationships(self, resource: Resource) -> Dict[str, List[Resource]]:
        """
        从EA图谱获取资源关系（增强）
        
        Args:
            resource: 资源对象
            
        Returns:
            Dict: EA关系字典
        """
        # 从资源元数据中提取EA实体ID
        metadata = resource.get_metadata()
        ea_entity_id = metadata.get("ea_entity_id") or metadata.get("ea_id")
        
        if not ea_entity_id:
            return {}
        
        # TODO: 调用EA知识图谱服务查询关系
        # 这里需要访问EA服务，可以通过依赖注入或服务发现
        # 简化实现：返回空字典
        logger.debug(f"资源 {resource.id} 有EA实体ID: {ea_entity_id}，但EA服务未集成")
        return {}
    
    def get_all(self) -> List[Resource]:
        """获取所有注册的资源"""
        return list(self._resources_by_id.values())
    
    def count(self) -> int:
        """获取注册的资源总数"""
        return len(self._resources_by_id)
    
    def count_by_type(self) -> Dict[ResourceType, int]:
        """按类型统计资源数量"""
        return {rtype: len(resources) for rtype, resources in self._resources_by_type.items()}
    
    def _extract_keywords(self, resource: Resource) -> List[str]:
        """从资源中提取关键词（用于语义索引）"""
        keywords = []
        
        # 从名称提取
        name_words = resource.name.lower().split()
        keywords.extend(name_words)
        
        # 从描述提取（简单分词）
        desc_words = resource.description.lower().split()
        keywords.extend(desc_words[:10])  # 限制数量
        
        # 从元数据提取（如果有）
        metadata = resource.get_metadata()
        if "tags" in metadata:
            keywords.extend([tag.lower() for tag in metadata["tags"]])
        
        return list(set(keywords))  # 去重
    
    def _extract_keywords_from_query(self, query: str) -> List[str]:
        """从查询字符串中提取关键词"""
        # 简单的分词实现
        # 实际应该使用更复杂的分词和语义分析
        words = query.lower().split()
        return [w for w in words if len(w) > 2]  # 过滤太短的词
