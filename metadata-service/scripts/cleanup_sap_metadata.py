"""
清理所有SAP相关的元数据
支持批量删除，处理10万+条记录
"""
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, or_, func, cast, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# 导入模型
from metadata_service.src.models.data_asset import DataAsset
from metadata_service.src.models.business_entity import BusinessEntity
from metadata_service.src.models.ai_model import AIModel

# 或者使用数据库模块
try:
    from database.src.core.database import get_database_manager
    from database.src.core.session import SessionLocal
    USE_DATABASE_MODULE = True
except ImportError:
    USE_DATABASE_MODULE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """获取数据库连接URL"""
    # 从环境变量或配置文件读取
    db_url = os.getenv(
        'DATABASE_URL',
        os.getenv(
            'POSTGRES_URL',
            'postgresql://postgres:postgres@localhost:5432/enterprise_ai'
        )
    )
    return db_url


def get_database_session():
    """获取数据库会话"""
    if USE_DATABASE_MODULE:
        try:
            # 使用数据库模块
            db_manager = get_database_manager()
            engine = db_manager.create_engine()
            SessionLocal = sessionmaker(bind=engine)
            return SessionLocal()
        except Exception as e:
            logger.warning(f"使用数据库模块失败，回退到直接连接: {e}")
    
    # 直接连接
    db_url = get_database_url()
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def is_sap_related(record, record_type: str) -> bool:
    """
    判断记录是否与SAP相关
    
    Args:
        record: 数据库记录对象
        record_type: 记录类型 ('data_asset', 'business_entity', 'ai_model')
    
    Returns:
        bool: 是否与SAP相关
    """
    # 检查source_system字段（data_assets表）
    if hasattr(record, 'source_system') and record.source_system:
        if 'sap' in str(record.source_system).lower():
            return True
    
    # 检查name字段
    if hasattr(record, 'name') and record.name:
        if 'sap' in str(record.name).lower():
            return True
    
    # 检查display_name字段
    if hasattr(record, 'display_name') and record.display_name:
        if 'sap' in str(record.display_name).lower():
            return True
    
    # 检查description字段
    if hasattr(record, 'description') and record.description:
        if 'sap' in str(record.description).lower():
            return True
    
    # 检查tags字段（JSON数组）
    if hasattr(record, 'tags') and record.tags:
        if isinstance(record.tags, list):
            for tag in record.tags:
                if 'sap' in str(tag).lower():
                    return True
        elif isinstance(record.tags, str):
            if 'sap' in record.tags.lower():
                return True
    
    # 检查metadata字段（JSON对象）
    if hasattr(record, 'extra_metadata') and record.extra_metadata:
        metadata_str = str(record.extra_metadata).lower()
        if 'sap' in metadata_str:
            return True
    
    # 检查source_path字段
    if hasattr(record, 'source_path') and record.source_path:
        if 'sap' in str(record.source_path).lower():
            return True
    
    # 检查source_connection字段
    if hasattr(record, 'source_connection') and record.source_connection:
        if 'sap' in str(record.source_connection).lower():
            return True
    
    return False


def count_sap_records(db: Session) -> dict:
    """统计SAP相关记录数量（使用SQL查询，更高效）"""
    counts = {
        'data_assets': 0,
        'business_entities': 0,
        'ai_models': 0
    }
    
    logger.info("正在统计SAP相关记录...")
    
    # 使用SQL LIKE查询统计（更高效）
    from sqlalchemy import func
    
    # 统计data_assets（使用SQL查询）
    sap_data_assets_query = db.query(DataAsset).filter(
        or_(
            func.lower(cast(DataAsset.source_system, String)).like('%sap%'),
            func.lower(cast(DataAsset.name, String)).like('%sap%'),
            func.lower(cast(DataAsset.display_name, String)).like('%sap%'),
            func.lower(cast(DataAsset.description, String)).like('%sap%'),
            func.lower(cast(DataAsset.source_path, String)).like('%sap%'),
            func.lower(cast(DataAsset.source_connection, String)).like('%sap%'),
            func.lower(cast(DataAsset.tags, String)).like('%sap%'),
            func.lower(cast(DataAsset.extra_metadata, String)).like('%sap%')
        )
    )
    counts['data_assets'] = sap_data_assets_query.count()
    logger.info(f"  - data_assets: {counts['data_assets']} 条")
    
    # 统计business_entities
    sap_business_entities_query = db.query(BusinessEntity).filter(
        or_(
            func.lower(cast(BusinessEntity.name, String)).like('%sap%'),
            func.lower(cast(BusinessEntity.display_name, String)).like('%sap%'),
            func.lower(cast(BusinessEntity.description, String)).like('%sap%'),
            func.lower(cast(BusinessEntity.tags, String)).like('%sap%'),
            func.lower(cast(BusinessEntity.extra_metadata, String)).like('%sap%')
        )
    )
    counts['business_entities'] = sap_business_entities_query.count()
    logger.info(f"  - business_entities: {counts['business_entities']} 条")
    
    # 统计ai_models
    sap_ai_models_query = db.query(AIModel).filter(
        or_(
            func.lower(cast(AIModel.name, String)).like('%sap%'),
            func.lower(cast(AIModel.display_name, String)).like('%sap%'),
            func.lower(cast(AIModel.description, String)).like('%sap%'),
            func.lower(cast(AIModel.tags, String)).like('%sap%'),
            func.lower(cast(AIModel.extra_metadata, String)).like('%sap%')
        )
    )
    counts['ai_models'] = sap_ai_models_query.count()
    logger.info(f"  - ai_models: {counts['ai_models']} 条")
    
    total = sum(counts.values())
    logger.info(f"总计: {total} 条SAP相关记录")
    
    return counts


def delete_sap_records(db: Session, batch_size: int = 1000, dry_run: bool = False) -> dict:
    """
    删除所有SAP相关记录（使用SQL批量删除，更高效）
    
    Args:
        db: 数据库会话
        batch_size: 批量删除大小
        dry_run: 是否只是预览（不实际删除）
    
    Returns:
        dict: 删除统计信息
    """
    stats = {
        'data_assets': 0,
        'business_entities': 0,
        'ai_models': 0,
        'errors': []
    }
    
    try:
        # 删除data_assets（使用SQL批量删除）
        logger.info("正在删除SAP相关的data_assets...")
        sap_data_assets_query = db.query(DataAsset).filter(
            or_(
                func.lower(cast(DataAsset.source_system, String)).like('%sap%'),
                func.lower(cast(DataAsset.name, String)).like('%sap%'),
                func.lower(cast(DataAsset.display_name, String)).like('%sap%'),
                func.lower(cast(DataAsset.description, String)).like('%sap%'),
                func.lower(cast(DataAsset.source_path, String)).like('%sap%'),
                func.lower(cast(DataAsset.source_connection, String)).like('%sap%'),
                func.lower(cast(DataAsset.tags, String)).like('%sap%'),
                func.lower(cast(DataAsset.extra_metadata, String)).like('%sap%')
            )
        )
        
        total_data_assets = sap_data_assets_query.count()
        if total_data_assets > 0:
            logger.info(f"找到 {total_data_assets} 条SAP相关的data_assets")
            
            if not dry_run:
                # 批量删除
                deleted = 0
                while True:
                    # 获取一批ID
                    batch_ids = [row[0] for row in sap_data_assets_query.limit(batch_size).with_entities(DataAsset.id).all()]
                    if not batch_ids:
                        break
                    
                    # 删除这一批
                    batch_deleted = db.query(DataAsset).filter(DataAsset.id.in_(batch_ids)).delete(synchronize_session=False)
                    db.commit()
                    deleted += batch_deleted
                    stats['data_assets'] = deleted
                    logger.info(f"  已删除 {deleted}/{total_data_assets} 条data_assets")
            else:
                stats['data_assets'] = total_data_assets
                logger.info(f"  [预览模式] 将删除 {total_data_assets} 条data_assets")
        
        # 删除business_entities
        logger.info("正在删除SAP相关的business_entities...")
        sap_business_entities_query = db.query(BusinessEntity).filter(
            or_(
                func.lower(cast(BusinessEntity.name, String)).like('%sap%'),
                func.lower(cast(BusinessEntity.display_name, String)).like('%sap%'),
                func.lower(cast(BusinessEntity.description, String)).like('%sap%'),
                func.lower(cast(BusinessEntity.tags, String)).like('%sap%'),
                func.lower(cast(BusinessEntity.extra_metadata, String)).like('%sap%')
            )
        )
        
        total_business_entities = sap_business_entities_query.count()
        if total_business_entities > 0:
            logger.info(f"找到 {total_business_entities} 条SAP相关的business_entities")
            
            if not dry_run:
                # 批量删除
                deleted = 0
                while True:
                    batch_ids = [row[0] for row in sap_business_entities_query.limit(batch_size).with_entities(BusinessEntity.id).all()]
                    if not batch_ids:
                        break
                    
                    batch_deleted = db.query(BusinessEntity).filter(BusinessEntity.id.in_(batch_ids)).delete(synchronize_session=False)
                    db.commit()
                    deleted += batch_deleted
                    stats['business_entities'] = deleted
                    logger.info(f"  已删除 {deleted}/{total_business_entities} 条business_entities")
            else:
                stats['business_entities'] = total_business_entities
                logger.info(f"  [预览模式] 将删除 {total_business_entities} 条business_entities")
        
        # 删除ai_models
        logger.info("正在删除SAP相关的ai_models...")
        sap_ai_models_query = db.query(AIModel).filter(
            or_(
                func.lower(cast(AIModel.name, String)).like('%sap%'),
                func.lower(cast(AIModel.display_name, String)).like('%sap%'),
                func.lower(cast(AIModel.description, String)).like('%sap%'),
                func.lower(cast(AIModel.tags, String)).like('%sap%'),
                func.lower(cast(AIModel.extra_metadata, String)).like('%sap%')
            )
        )
        
        total_ai_models = sap_ai_models_query.count()
        if total_ai_models > 0:
            logger.info(f"找到 {total_ai_models} 条SAP相关的ai_models")
            
            if not dry_run:
                # 批量删除
                deleted = 0
                while True:
                    batch_ids = [row[0] for row in sap_ai_models_query.limit(batch_size).with_entities(AIModel.id).all()]
                    if not batch_ids:
                        break
                    
                    batch_deleted = db.query(AIModel).filter(AIModel.id.in_(batch_ids)).delete(synchronize_session=False)
                    db.commit()
                    deleted += batch_deleted
                    stats['ai_models'] = deleted
                    logger.info(f"  已删除 {deleted}/{total_ai_models} 条ai_models")
            else:
                stats['ai_models'] = total_ai_models
                logger.info(f"  [预览模式] 将删除 {total_ai_models} 条ai_models")
        
    except SQLAlchemyError as e:
        logger.error(f"删除过程中发生错误: {e}", exc_info=True)
        stats['errors'].append(str(e))
        db.rollback()
    
    return stats


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理所有SAP相关的元数据')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际删除')
    parser.add_argument('--batch-size', type=int, default=1000, help='批量删除大小（默认1000）')
    parser.add_argument('--confirm', action='store_true', help='确认删除（需要与--dry-run一起使用）')
    args = parser.parse_args()
    
    # 获取数据库连接
    db_url = get_database_url()
    logger.info(f"连接数据库: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    
    try:
        db = get_database_session()
        engine = db.bind if hasattr(db, 'bind') else None
    except Exception as e:
        logger.error(f"无法连接数据库: {e}")
        logger.info("尝试使用直接连接...")
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
    
    try:
        # 统计SAP相关记录
        counts = count_sap_records(db)
        total = sum(counts.values())
        
        if total == 0:
            logger.info("没有找到SAP相关的记录")
            return
        
        # 预览模式
        if args.dry_run:
            logger.info("\n" + "=" * 80)
            logger.info("预览模式 - 不会实际删除数据")
            logger.info("=" * 80)
            stats = delete_sap_records(db, batch_size=args.batch_size, dry_run=True)
            logger.info("\n预览结果:")
            logger.info(f"  - data_assets: {stats['data_assets']} 条")
            logger.info(f"  - business_entities: {stats['business_entities']} 条")
            logger.info(f"  - ai_models: {stats['ai_models']} 条")
            logger.info(f"总计: {sum([stats['data_assets'], stats['business_entities'], stats['ai_models']])} 条")
            logger.info("\n要实际执行删除，请运行: python cleanup_sap_metadata.py --confirm")
        else:
            # 确认删除
            if not args.confirm:
                logger.warning("\n" + "=" * 80)
                logger.warning("警告: 这将删除所有SAP相关的元数据！")
                logger.warning("=" * 80)
                logger.warning(f"将删除 {total} 条记录:")
                logger.warning(f"  - data_assets: {counts['data_assets']} 条")
                logger.warning(f"  - business_entities: {counts['business_entities']} 条")
                logger.warning(f"  - ai_models: {counts['ai_models']} 条")
                logger.warning("\n要执行删除，请添加 --confirm 参数")
                logger.warning("或先使用 --dry-run 预览")
                return
            
            logger.info("\n" + "=" * 80)
            logger.info("开始删除SAP相关元数据...")
            logger.info("=" * 80)
            
            stats = delete_sap_records(db, batch_size=args.batch_size, dry_run=False)
            
            logger.info("\n" + "=" * 80)
            logger.info("删除完成!")
            logger.info("=" * 80)
            logger.info(f"已删除:")
            logger.info(f"  - data_assets: {stats['data_assets']} 条")
            logger.info(f"  - business_entities: {stats['business_entities']} 条")
            logger.info(f"  - ai_models: {stats['ai_models']} 条")
            logger.info(f"总计: {sum([stats['data_assets'], stats['business_entities'], stats['ai_models']])} 条")
            
            if stats['errors']:
                logger.warning(f"发生 {len(stats['errors'])} 个错误:")
                for error in stats['errors']:
                    logger.warning(f"  - {error}")
    
    finally:
        db.close()
        if engine:
            engine.dispose()


if __name__ == '__main__':
    main()

