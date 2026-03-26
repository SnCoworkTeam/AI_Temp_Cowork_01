"""
资源元数据管理
提供资源元数据的统一管理和查询接口
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

try:
    from .resource_model import Resource, ResourceType
except ImportError:
    from resource_model import Resource, ResourceType

logger = logging.getLogger(__name__)


class ResourceMetadataManager:
    """资源元数据管理器"""
    
    def __init__(self):
        """初始化元数据管理器"""
        # 元数据索引：{resource_id: {metadata_key: metadata_value}}
        self._metadata_index: Dict[str, Dict[str, Any]] = {}
        # 标签索引：{tag: [resource_ids]}
        self._tag_index: Dict[str, List[str]] = {}
        # 分类索引：{category: [resource_ids]}
        self._category_index: Dict[str, List[str]] = {}
    
    def set_metadata(
        self,
        resource: Resource,
        metadata: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """
        设置资源元数据
        
        Args:
            resource: 资源对象
            metadata: 元数据字典
            merge: 是否合并到现有元数据（默认True）
            
        Returns:
            bool: 是否成功
        """
        try:
            resource_id = resource.id
            
            if merge and resource_id in self._metadata_index:
                # 合并元数据
                self._metadata_index[resource_id].update(metadata)
            else:
                # 替换元数据
                self._metadata_index[resource_id] = metadata.copy()
            
            # 更新标签索引
            if "tags" in metadata:
                self._update_tag_index(resource_id, metadata["tags"])
            
            # 更新分类索引
            if "category" in metadata:
                self._update_category_index(resource_id, metadata["category"])
            
            logger.debug(f"资源 {resource_id} 元数据已更新")
            return True
            
        except Exception as e:
            logger.error(f"设置资源元数据失败: {resource.id}, 错误: {e}")
            return False
    
    def get_metadata(self, resource: Resource) -> Dict[str, Any]:
        """
        获取资源元数据
        
        Args:
            resource: 资源对象
            
        Returns:
            Dict: 元数据字典（合并资源自身元数据和索引中的元数据）
        """
        resource_id = resource.id
        
        # 获取资源自身的元数据
        base_metadata = resource.get_metadata()
        
        # 合并索引中的元数据
        if resource_id in self._metadata_index:
            base_metadata.update(self._metadata_index[resource_id])
        
        return base_metadata
    
    def add_tag(self, resource: Resource, tag: str) -> bool:
        """
        为资源添加标签
        
        Args:
            resource: 资源对象
            tag: 标签
            
        Returns:
            bool: 是否成功
        """
        try:
            resource_id = resource.id
            
            # 更新标签索引
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            
            if resource_id not in self._tag_index[tag]:
                self._tag_index[tag].append(resource_id)
            
            # 更新资源元数据
            if resource_id not in self._metadata_index:
                self._metadata_index[resource_id] = {}
            
            if "tags" not in self._metadata_index[resource_id]:
                self._metadata_index[resource_id]["tags"] = []
            
            if tag not in self._metadata_index[resource_id]["tags"]:
                self._metadata_index[resource_id]["tags"].append(tag)
            
            logger.debug(f"为资源 {resource_id} 添加标签: {tag}")
            return True
            
        except Exception as e:
            logger.error(f"添加标签失败: {resource.id}, 错误: {e}")
            return False
    
    def remove_tag(self, resource: Resource, tag: str) -> bool:
        """
        移除资源标签
        
        Args:
            resource: 资源对象
            tag: 标签
            
        Returns:
            bool: 是否成功
        """
        try:
            resource_id = resource.id
            
            # 从标签索引中移除
            if tag in self._tag_index and resource_id in self._tag_index[tag]:
                self._tag_index[tag].remove(resource_id)
            
            # 从资源元数据中移除
            if resource_id in self._metadata_index:
                if "tags" in self._metadata_index[resource_id]:
                    if tag in self._metadata_index[resource_id]["tags"]:
                        self._metadata_index[resource_id]["tags"].remove(tag)
            
            logger.debug(f"从资源 {resource_id} 移除标签: {tag}")
            return True
            
        except Exception as e:
            logger.error(f"移除标签失败: {resource.id}, 错误: {e}")
            return False
    
    def get_resources_by_tag(self, tag: str) -> List[str]:
        """
        根据标签获取资源ID列表
        
        Args:
            tag: 标签
            
        Returns:
            List[str]: 资源ID列表
        """
        return self._tag_index.get(tag, []).copy()
    
    def get_resources_by_category(self, category: str) -> List[str]:
        """
        根据分类获取资源ID列表
        
        Args:
            category: 分类
            
        Returns:
            List[str]: 资源ID列表
        """
        return self._category_index.get(category, []).copy()
    
    def search_metadata(
        self,
        query: Dict[str, Any],
        resource_type: Optional[ResourceType] = None
    ) -> List[str]:
        """
        根据元数据查询资源
        
        Args:
            query: 查询条件字典 {key: value}
            resource_type: 可选的资源类型过滤
            
        Returns:
            List[str]: 匹配的资源ID列表
        """
        matching_ids = []
        
        for resource_id, metadata in self._metadata_index.items():
            # 检查是否匹配所有查询条件
            matches = all(
                metadata.get(key) == value
                for key, value in query.items()
            )
            
            if matches:
                matching_ids.append(resource_id)
        
        return matching_ids
    
    def _update_tag_index(self, resource_id: str, tags: List[str]):
        """更新标签索引"""
        # 移除旧的标签关联
        for tag, resource_ids in self._tag_index.items():
            if resource_id in resource_ids:
                resource_ids.remove(resource_id)
        
        # 添加新的标签关联
        for tag in tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if resource_id not in self._tag_index[tag]:
                self._tag_index[tag].append(resource_id)
    
    def _update_category_index(self, resource_id: str, category: str):
        """更新分类索引"""
        # 移除旧的分类关联
        for cat, resource_ids in self._category_index.items():
            if resource_id in resource_ids:
                resource_ids.remove(resource_id)
        
        # 添加新的分类关联
        if category not in self._category_index:
            self._category_index[category] = []
        if resource_id not in self._category_index[category]:
            self._category_index[category].append(resource_id)
    
    def clear_metadata(self, resource: Resource) -> bool:
        """
        清除资源的所有元数据
        
        Args:
            resource: 资源对象
            
        Returns:
            bool: 是否成功
        """
        try:
            resource_id = resource.id
            
            if resource_id in self._metadata_index:
                # 清除标签索引
                if "tags" in self._metadata_index[resource_id]:
                    for tag in self._metadata_index[resource_id]["tags"]:
                        if tag in self._tag_index and resource_id in self._tag_index[tag]:
                            self._tag_index[tag].remove(resource_id)
                
                # 清除分类索引
                if "category" in self._metadata_index[resource_id]:
                    category = self._metadata_index[resource_id]["category"]
                    if category in self._category_index and resource_id in self._category_index[category]:
                        self._category_index[category].remove(resource_id)
                
                # 清除元数据
                del self._metadata_index[resource_id]
            
            logger.debug(f"资源 {resource_id} 元数据已清除")
            return True
            
        except Exception as e:
            logger.error(f"清除资源元数据失败: {resource.id}, 错误: {e}")
            return False
