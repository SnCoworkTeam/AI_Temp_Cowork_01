"""
使用统计跟踪服务
自动收集和更新数据资产的使用统计信息
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.operational_metadata import OperationalMetadata, UsageStats
from ..core.database import get_db

logger = logging.getLogger(__name__)


class UsageTracker:
    """使用统计跟踪器"""
    
    def __init__(self, db: Session):
        """
        初始化使用跟踪器
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def track_access(
        self,
        asset_type: str,
        asset_id: int,
        user_id: Optional[str] = None,
        service_name: Optional[str] = None,
        query_pattern: Optional[Dict[str, Any]] = None
    ):
        """
        跟踪资产访问
        
        Args:
            asset_type: 资产类型（data_asset, ai_model, workflow等）
            asset_id: 资产ID
            user_id: 用户ID（可选）
            service_name: 服务名称（可选）
            query_pattern: 查询模式（可选）
        """
        try:
            # 获取或创建操作元数据记录
            op_metadata = self.db.query(OperationalMetadata).filter(
                and_(
                    OperationalMetadata.asset_type == asset_type,
                    OperationalMetadata.asset_id == asset_id
                )
            ).first()
            
            if not op_metadata:
                # 创建新记录
                op_metadata = OperationalMetadata(
                    asset_type=asset_type,
                    asset_id=asset_id,
                    usage_stats={},
                    change_history=[]
                )
                self.db.add(op_metadata)
            
            # 更新使用统计
            usage_stats = op_metadata.usage_stats or {}
            
            # 更新访问计数
            access_count = usage_stats.get("access_count", 0) + 1
            usage_stats["access_count"] = access_count
            
            # 更新最后访问时间
            usage_stats["last_accessed"] = datetime.now().isoformat()
            
            # 更新访问用户列表
            access_users = usage_stats.get("access_users", [])
            if user_id and user_id not in access_users:
                access_users.append(user_id)
                usage_stats["access_users"] = access_users[:100]  # 限制数量
            
            # 更新访问服务列表
            access_services = usage_stats.get("access_services", [])
            if service_name and service_name not in access_services:
                access_services.append(service_name)
                usage_stats["access_services"] = access_services[:50]  # 限制数量
            
            # 更新查询模式
            if query_pattern:
                query_patterns = usage_stats.get("query_patterns", [])
                query_patterns.append({
                    "pattern": query_pattern,
                    "timestamp": datetime.now().isoformat()
                })
                # 只保留最近100个查询模式
                usage_stats["query_patterns"] = query_patterns[-100:]
            
            # 计算访问频率
            last_accessed = usage_stats.get("last_accessed")
            if last_accessed:
                # 简单的频率计算（可以根据实际需求优化）
                if access_count < 10:
                    usage_stats["access_frequency"] = "rarely"
                elif access_count < 100:
                    usage_stats["access_frequency"] = "monthly"
                elif access_count < 1000:
                    usage_stats["access_frequency"] = "weekly"
                else:
                    usage_stats["access_frequency"] = "daily"
            
            # 更新记录
            op_metadata.usage_stats = usage_stats
            op_metadata.updated_at = datetime.now()
            
            self.db.commit()
            logger.debug(f"Tracked access for {asset_type}:{asset_id}")
            
        except Exception as e:
            logger.error(f"Failed to track access: {e}", exc_info=True)
            self.db.rollback()
    
    def get_usage_stats(
        self,
        asset_type: str,
        asset_id: int
    ) -> Optional[UsageStats]:
        """
        获取使用统计
        
        Args:
            asset_type: 资产类型
            asset_id: 资产ID
            
        Returns:
            使用统计对象
        """
        try:
            op_metadata = self.db.query(OperationalMetadata).filter(
                and_(
                    OperationalMetadata.asset_type == asset_type,
                    OperationalMetadata.asset_id == asset_id
                )
            ).first()
            
            if op_metadata and op_metadata.usage_stats:
                return UsageStats(**op_metadata.usage_stats)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}", exc_info=True)
            return None
    
    def get_popular_assets(
        self,
        asset_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取热门资产（按访问次数排序）
        
        Args:
            asset_type: 资产类型
            limit: 返回数量限制
            
        Returns:
            热门资产列表
        """
        try:
            results = self.db.query(OperationalMetadata).filter(
                OperationalMetadata.asset_type == asset_type
            ).all()
            
            # 按访问次数排序
            popular = []
            for op_metadata in results:
                usage_stats = op_metadata.usage_stats or {}
                access_count = usage_stats.get("access_count", 0)
                if access_count > 0:
                    popular.append({
                        "asset_id": op_metadata.asset_id,
                        "access_count": access_count,
                        "last_accessed": usage_stats.get("last_accessed"),
                        "access_frequency": usage_stats.get("access_frequency", "unknown")
                    })
            
            # 排序并返回
            popular.sort(key=lambda x: x["access_count"], reverse=True)
            return popular[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get popular assets: {e}", exc_info=True)
            return []

