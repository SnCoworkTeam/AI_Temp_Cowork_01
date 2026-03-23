"""
运行迁移 018 - 添加 knowledge_bases 表和 documents.knowledge_base_id 字段
"""
import sys
import os
from pathlib import Path

# 设置路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))
os.chdir(script_dir)

# 设置数据库连接（从环境变量或使用默认值）
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', 'ai_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'ai_password')
DB_NAME = os.environ.get('DB_NAME', 'ai_platform')

print("=" * 50)
print("运行数据库迁移 018")
print("添加 knowledge_bases 表和 documents.knowledge_base_id 字段")
print("=" * 50)
print()
print(f"数据库: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
print()

try:
    # 使用importlib导入迁移模块（因为模块名以数字开头）
    import importlib.util
    migration_path = script_dir / 'src' / 'migrations' / 'versions' / '018_add_knowledge_bases_table.py'
    spec = importlib.util.spec_from_file_location('migration_018', str(migration_path))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    
    from sqlalchemy import create_engine, inspect
    from alembic import op
    from alembic.runtime.migration import MigrationContext
    from alembic.operations import Operations
    
    # 创建数据库连接
    db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    print(f"连接数据库: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    engine = create_engine(db_url)
    
    # 执行迁移
    print("执行迁移...")
    with engine.begin() as connection:
        # 设置MigrationContext和Operations
        context = MigrationContext.configure(connection)
        op.connection = connection
        op.context = context
        # 创建Operations实例并绑定
        operations = Operations(context)
        # 将operations绑定到op模块
        import alembic.op as op_module
        op_module._proxy = operations
        migration.upgrade()
    
    print()
    print("✅ 迁移 018 执行成功！")
    print()
    print("已创建:")
    print("  - knowledge_bases 表")
    print("  - documents.knowledge_base_id 字段")
    print("  - 相关索引和外键约束")
    print()
    print("=" * 50)
    print("迁移完成")
    print("=" * 50)
    
except Exception as e:
    print()
    print(f"❌ 迁移执行出错: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

