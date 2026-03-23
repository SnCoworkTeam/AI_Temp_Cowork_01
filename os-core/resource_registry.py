"""
资源注册表
企业资源注册表（类似OS的设备注册表）
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging
import time

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
        # 缓存：最近查询结果（用于性能优化）
        self._query_cache: Dict[str, tuple] = {}  # {query: (results, timestamp)}
        self._cache_ttl = 300  # 缓存TTL：5分钟
    
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
                # 先注销旧资源
                self.unregister(resource.id)
            
            # 注册到各个索引
            self._resources_by_id[resource.id] = resource
            self._resources_by_type[resource.type].append(resource)
            self._resources_by_uri[resource.uri] = resource
            
            # 更新语义索引（简单实现，基于名称和描述）
            keywords = self._extract_keywords(resource)
            for keyword in keywords:
                if resource.id not in self._semantic_index[keyword]:
                    self._semantic_index[keyword].append(resource.id)
            
            # 清除相关缓存
            self._clear_cache()
            
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
        
        # 清除相关缓存
        self._clear_cache()
        
        logger.info(f"资源注销成功: {resource_id}")
        return True
    
    def resolve(self, uri: str) -> Optional[Resource]:
        """
        解析URI到资源对象
        
        Args:
            uri: 统一资源标识符
            
        Returns:
            Resource对象，如果不存在返回None
        """
        return self._resources_by_uri.get(uri)
    
    def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """
        根据ID获取资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            Resource对象，如果不存在返回None
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
    
    def get_all(self) -> List[Resource]:
        """
        获取所有资源
        
        Returns:
            所有资源的列表
        """
        return list(self._resources_by_id.values())
    
    def discover(self, query: str, resource_type: Optional[ResourceType] = None, limit: int = 10) -> List[Resource]:
        """
        发现资源（语义搜索）
        
        Args:
            query: 查询字符串
            resource_type: 可选的资源类型过滤
            limit: 返回结果数量限制
            
        Returns:
            匹配的资源列表
        """
        # 检查缓存
        cache_key = f"{query}:{resource_type}:{limit}"
        if cache_key in self._query_cache:
            results, timestamp = self._query_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"使用缓存结果: {cache_key}")
                return results
        
        # 提取查询关键词
        query_keywords = self._extract_keywords_from_text(query)
        
        # 收集匹配的资源ID
        matched_ids = set()
        for keyword in query_keywords:
            if keyword in self._semantic_index:
                matched_ids.update(self._semantic_index[keyword])
        
        # 获取匹配的资源
        matched_resources = []
        for resource_id in matched_ids:
            resource = self._resources_by_id.get(resource_id)
            if resource is None:
                continue
            
            # 类型过滤
            if resource_type is not None and resource.type != resource_type:
                continue
            
            matched_resources.append(resource)
        
        # 简单排序：按名称匹配度（这里简化处理，实际可以使用更复杂的排序算法）
        matched_resources.sort(key=lambda r: (
            query.lower() in r.name.lower(),
            query.lower() in r.description.lower() if r.description else False
        ), reverse=True)
        
        # 限制结果数量
        results = matched_resources[:limit]
        
        # 更新缓存
        self._query_cache[cache_key] = (results, time.time())
        
        return results
    
    def get_relationships(self, resource_id: str) -> Dict[str, List[Resource]]:
        """
        获取资源关联关系
        
        Args:
            resource_id: 资源ID
            
        Returns:
            关联关系字典，格式：{relationship_type: [Resource]}
        """
        resource = self.get_by_id(resource_id)
        if resource is None:
            return {}
        
        relationships = {}
        if hasattr(resource, 'relationships') and resource.relationships:
            for rel_type, related_ids in resource.relationships.items():
                related_resources = []
                for related_id in related_ids:
                    related_resource = self.get_by_id(related_id)
                    if related_resource:
                        related_resources.append(related_resource)
                if related_resources:
                    relationships[rel_type] = related_resources
        
        return relationships
    
    def _extract_keywords(self, resource: Resource) -> List[str]:
        """
        从资源中提取关键词
        
        Args:
            resource: 资源对象
            
        Returns:
            关键词列表
        """
        keywords = []
        
        # 从名称提取
        if resource.name:
            keywords.extend(self._extract_keywords_from_text(resource.name))
        
        # 从描述提取
        if resource.description:
            keywords.extend(self._extract_keywords_from_text(resource.description))
        
        # 从URI提取
        if resource.uri:
            # 提取URI中的路径部分作为关键词
            uri_parts = resource.uri.split('/')
            keywords.extend([part for part in uri_parts if part and len(part) > 1])
        
        return list(set(keywords))  # 去重
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 文本内容
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 简单实现：按空格和标点符号分割
        import re
        # 移除标点符号，保留中英文和数字
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        # 分割并过滤
        words = [w.lower() for w in cleaned.split() if len(w) > 1]
        
        # 对于中文，也提取单个字符（如果长度合适）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        words.extend(chinese_chars)
        
        return list(set(words))  # 去重
    
    def _clear_cache(self):
        """清除查询缓存"""
        self._query_cache.clear()
    
    def clear_cache(self):
        """公开方法：清除查询缓存"""
        self._clear_cache()
        logger.info("资源注册表缓存已清除")
