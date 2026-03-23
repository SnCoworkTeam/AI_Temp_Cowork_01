#!/usr/bin/env python3
"""
定期清理任务脚本
用于清理过期的黑名单记录
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.session import SessionLocal
from auth_service.src.services.cleanup_service import run_cleanup_task
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    db = SessionLocal()
    try:
        logger.info("Starting cleanup task...")
        results = await run_cleanup_task(db)
        logger.info(f"Cleanup completed: {results}")
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

