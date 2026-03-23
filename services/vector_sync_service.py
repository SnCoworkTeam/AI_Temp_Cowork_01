"""
向量同步服务
负责检测和同步业务活动的向量更新
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from database.src.models import BusinessActivity


class VectorSyncService:
    """向量同步服务"""
    
    def __init__(self):
        """初始化向量同步服务"""
        # 初始化数据库连接
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            raise RuntimeError("数据库连接失败")
        
        init_session_factory()
        self._db = None
    
    def _get_db(self):
        """获取数据库会话"""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    def _close_db(self):
        """关闭数据库会话"""
        if self._db:
            self._db.close()
            self._db = None
    
    def check_updates(self, business_domain: Optional[str] = None) -> List[BusinessActivity]:
        """
        检查需要更新向量的活动
        
        Args:
            business_domain: 业务领域过滤
        
        Returns:
            List[BusinessActivity]: 需要更新的活动列表
        """
        try:
            db = self._get_db()
            
            # 查询需要更新的活动
            query = db.query(BusinessActivity)
            if business_domain:
                query = query.filter(BusinessActivity.business_domain == business_domain)
            
            activities = query.all()
            
            # 过滤出需要更新的活动
            needs_update = []
            for activity in activities:
                if activity.needs_vector_update():
                    needs_update.append(activity)
            
            return needs_update
        
        except Exception as e:
            raise RuntimeError(f"检查更新失败: {e}")
    
    def sync_vectors(
        self,
        business_domain: Optional[str] = None,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        同步所有需要更新的向量
        
        Args:
            business_domain: 业务领域过滤
            batch_size: 批处理大小
        
        Returns:
            Dict: 同步结果统计
        """
        try:
            # 1. 检查需要更新的活动
            activities_to_update = self.check_updates(business_domain)
            
            if not activities_to_update:
                return {
                    "total": 0,
                    "updated": 0,
                    "failed": 0,
                    "message": "没有需要更新的向量"
                }
            
            # 2. 批量更新
            updated_count = 0
            failed_count = 0
            failed_ids = []
            
            for i in range(0, len(activities_to_update), batch_size):
                batch = activities_to_update[i:i + batch_size]
                
                for activity in batch:
                    try:
                        self.update_vector(activity.id)
                        updated_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_ids.append(activity.id)
                        print(f"[ERROR] 更新活动 {activity.id} 的向量失败: {e}")
            
            return {
                "total": len(activities_to_update),
                "updated": updated_count,
                "failed": failed_count,
                "failed_ids": failed_ids,
                "message": f"成功更新 {updated_count} 个，失败 {failed_count} 个"
            }
        
        except Exception as e:
            raise RuntimeError(f"同步向量失败: {e}")
    
    def update_vector(self, activity_id: str) -> bool:
        """
        更新单个活动的向量
        
        Args:
            activity_id: 活动ID
        
        Returns:
            bool: 是否成功
        """
        try:
            db = self._get_db()
            
            # 获取活动
            activity = db.query(BusinessActivity).filter_by(id=activity_id).first()
            if not activity:
                raise ValueError(f"活动不存在: {activity_id}")
            
            # TODO: 调用真实的向量化服务生成向量
            # 这里只是更新last_vectorized_at时间戳
            activity.last_vectorized_at = datetime.now()
            activity.embedding_version = "1.0"
            
            db.commit()
            
            return True
        
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"更新向量失败: {e}")
    
    def get_sync_status(self, business_domain: Optional[str] = None) -> Dict[str, Any]:
        """
        获取同步状态统计
        
        Args:
            business_domain: 业务领域过滤
        
        Returns:
            Dict: 同步状态统计
        """
        try:
            db = self._get_db()
            
            query = db.query(BusinessActivity)
            if business_domain:
                query = query.filter(BusinessActivity.business_domain == business_domain)
            
            all_activities = query.all()
            
            total_count = len(all_activities)
            needs_update_count = 0
            up_to_date_count = 0
            
            for activity in all_activities:
                if activity.needs_vector_update():
                    needs_update_count += 1
                else:
                    up_to_date_count += 1
            
            return {
                "total": total_count,
                "needs_update": needs_update_count,
                "up_to_date": up_to_date_count,
                "update_percentage": (up_to_date_count / total_count * 100) if total_count > 0 else 0
            }
        
        except Exception as e:
            raise RuntimeError(f"获取同步状态失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._close_db()


def main():
    """测试函数"""
    print("=" * 60)
    print("向量同步服务测试")
    print("=" * 60)
    print()
    
    try:
        service = VectorSyncService()
        
        # 测试1: 检查需要更新的活动
        print("[TEST] 检查需要更新的活动...")
        activities_to_update = service.check_updates("procurement")
        print(f"  找到 {len(activities_to_update)} 个需要更新的活动")
        if activities_to_update:
            for activity in activities_to_update[:5]:
                print(f"    - {activity.name} ({activity.id})")
        print()
        
        # 测试2: 获取同步状态
        print("[TEST] 获取同步状态...")
        status = service.get_sync_status("procurement")
        print(f"  总数: {status['total']}")
        print(f"  需要更新: {status['needs_update']}")
        print(f"  已更新: {status['up_to_date']}")
        print(f"  更新率: {status['update_percentage']:.1f}%")
        print()
        
        # 测试3: 同步向量
        print("[TEST] 同步向量...")
        result = service.sync_vectors("procurement", batch_size=5)
        print(f"  总数: {result['total']}")
        print(f"  成功: {result['updated']}")
        print(f"  失败: {result['failed']}")
        print(f"  消息: {result['message']}")
        print()
        
        # 测试4: 再次检查状态
        print("[TEST] 再次检查同步状态...")
        status_after = service.get_sync_status("procurement")
        print(f"  需要更新: {status_after['needs_update']}")
        print(f"  已更新: {status_after['up_to_date']}")
        print(f"  更新率: {status_after['update_percentage']:.1f}%")
        print()
        
        print("=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())




