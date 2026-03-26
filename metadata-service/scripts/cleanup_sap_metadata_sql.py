"""
使用SQL直接批量删除SAP相关元数据（更高效）
适用于10万+条记录的大批量删除
"""
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """获取数据库连接URL"""
    # 优先使用环境变量
    db_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')
    
    if db_url:
        return db_url
    
    # 尝试使用数据库模块的配置
    try:
        from database.src.core.database import get_database_settings
        settings = get_database_settings()
        db_url = (
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        return db_url
    except Exception as e:
        logger.warning(f"无法从数据库模块获取配置: {e}")
    
    # 最后使用默认值
    return 'postgresql://ai_user:ai_password@localhost:5432/ai_platform'


def count_sap_records(engine):
    """统计SAP相关记录数量"""
    counts = {
        'data_assets': 0,
        'business_entities': 0,
        'ai_models': 0
    }
    
    logger.info("正在统计SAP相关记录...")
    
    with engine.connect() as conn:
        # 统计data_assets
        query = text("""
            SELECT COUNT(*) 
            FROM data_assets 
            WHERE 
                LOWER(COALESCE(source_system, '')) LIKE '%sap%' OR
                LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                LOWER(COALESCE(source_path, '')) LIKE '%sap%' OR
                LOWER(COALESCE(source_connection, '')) LIKE '%sap%' OR
                LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
        """)
        result = conn.execute(query)
        counts['data_assets'] = result.scalar() or 0
        logger.info(f"  - data_assets: {counts['data_assets']} 条")
        
        # 统计business_entities
        query = text("""
            SELECT COUNT(*) 
            FROM business_entities 
            WHERE 
                LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
        """)
        result = conn.execute(query)
        counts['business_entities'] = result.scalar() or 0
        logger.info(f"  - business_entities: {counts['business_entities']} 条")
        
        # 统计ai_models
        query = text("""
            SELECT COUNT(*) 
            FROM ai_models 
            WHERE 
                LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
        """)
        result = conn.execute(query)
        counts['ai_models'] = result.scalar() or 0
        logger.info(f"  - ai_models: {counts['ai_models']} 条")
        
        total = sum(counts.values())
        logger.info(f"总计: {total} 条SAP相关记录")
        
        return counts


def delete_sap_records(engine, dry_run: bool = False):
    """使用SQL直接批量删除SAP相关记录"""
    stats = {
        'data_assets': 0,
        'business_entities': 0,
        'ai_models': 0,
        'errors': []
    }
    
    try:
        with engine.begin() as conn:  # 使用事务
            # 删除data_assets
            logger.info("正在删除SAP相关的data_assets...")
            if not dry_run:
                query = text("""
                    DELETE FROM data_assets 
                    WHERE 
                        LOWER(COALESCE(source_system, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(source_path, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(source_connection, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
                """)
                result = conn.execute(query)
                stats['data_assets'] = result.rowcount
                logger.info(f"  已删除 {stats['data_assets']} 条data_assets")
            else:
                # 预览模式，只统计
                query = text("""
                    SELECT COUNT(*) 
                    FROM data_assets 
                    WHERE 
                        LOWER(COALESCE(source_system, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(source_path, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(source_connection, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
                """)
                result = conn.execute(query)
                stats['data_assets'] = result.scalar() or 0
                logger.info(f"  [预览模式] 将删除 {stats['data_assets']} 条data_assets")
            
            # 删除business_entities
            logger.info("正在删除SAP相关的business_entities...")
            if not dry_run:
                query = text("""
                    DELETE FROM business_entities 
                    WHERE 
                        LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
                """)
                result = conn.execute(query)
                stats['business_entities'] = result.rowcount
                logger.info(f"  已删除 {stats['business_entities']} 条business_entities")
            else:
                query = text("""
                    SELECT COUNT(*) 
                    FROM business_entities 
                    WHERE 
                        LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
                """)
                result = conn.execute(query)
                stats['business_entities'] = result.scalar() or 0
                logger.info(f"  [预览模式] 将删除 {stats['business_entities']} 条business_entities")
            
            # 删除ai_models
            logger.info("正在删除SAP相关的ai_models...")
            if not dry_run:
                query = text("""
                    DELETE FROM ai_models 
                    WHERE 
                        LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
                """)
                result = conn.execute(query)
                stats['ai_models'] = result.rowcount
                logger.info(f"  已删除 {stats['ai_models']} 条ai_models")
            else:
                query = text("""
                    SELECT COUNT(*) 
                    FROM ai_models 
                    WHERE 
                        LOWER(COALESCE(name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(display_name, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(description, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(tags::text, '')) LIKE '%sap%' OR
                        LOWER(COALESCE(metadata::text, '')) LIKE '%sap%'
                """)
                result = conn.execute(query)
                stats['ai_models'] = result.scalar() or 0
                logger.info(f"  [预览模式] 将删除 {stats['ai_models']} 条ai_models")
            
            if not dry_run:
                conn.commit()
                logger.info("所有删除操作已提交")
    
    except SQLAlchemyError as e:
        logger.error(f"删除过程中发生错误: {e}", exc_info=True)
        stats['errors'].append(str(e))
    
    return stats


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理所有SAP相关的元数据（SQL版本，更高效）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际删除')
    parser.add_argument('--confirm', action='store_true', help='确认删除（需要与--dry-run一起使用）')
    args = parser.parse_args()
    
    # 获取数据库连接
    db_url = get_database_url()
    logger.info(f"连接数据库: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    
    engine = create_engine(db_url, echo=False)
    
    try:
        # 统计SAP相关记录
        counts = count_sap_records(engine)
        total = sum(counts.values())
        
        if total == 0:
            logger.info("没有找到SAP相关的记录")
            return
        
        # 预览模式
        if args.dry_run:
            logger.info("\n" + "=" * 80)
            logger.info("预览模式 - 不会实际删除数据")
            logger.info("=" * 80)
            stats = delete_sap_records(engine, dry_run=True)
            logger.info("\n预览结果:")
            logger.info(f"  - data_assets: {stats['data_assets']} 条")
            logger.info(f"  - business_entities: {stats['business_entities']} 条")
            logger.info(f"  - ai_models: {stats['ai_models']} 条")
            logger.info(f"总计: {sum([stats['data_assets'], stats['business_entities'], stats['ai_models']])} 条")
            logger.info("\n要实际执行删除，请运行: python cleanup_sap_metadata_sql.py --confirm")
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
            
            stats = delete_sap_records(engine, dry_run=False)
            
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
        engine.dispose()


if __name__ == '__main__':
    main()

