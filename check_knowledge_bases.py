#!/usr/bin/env python3
"""
诊断脚本：检查知识库数据
用于排查知识库数据是否丢失
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置数据库连接
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/enterprise_ai')

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from database.src.models.knowledge_models import KnowledgeBase, KnowledgeBaseStatus
    
    # 创建数据库连接
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/enterprise_ai')
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("=" * 60)
    print("知识库数据诊断")
    print("=" * 60)
    
    # 1. 检查知识库总数
    total_count = session.query(KnowledgeBase).count()
    print(f"\n1. 知识库总数: {total_count}")
    
    if total_count == 0:
        print("   ⚠️  警告：数据库中没有知识库数据！")
        print("   可能的原因：")
        print("   - 数据被删除")
        print("   - 数据库连接错误")
        print("   - 表结构不匹配")
    else:
        print(f"   ✅ 找到 {total_count} 个知识库")
    
    # 2. 按状态统计
    print("\n2. 按状态统计：")
    for status in KnowledgeBaseStatus:
        count = session.query(KnowledgeBase).filter(KnowledgeBase.status == status).count()
        print(f"   - {status.value}: {count} 个")
    
    # 3. 列出所有知识库
    print("\n3. 知识库列表：")
    knowledge_bases = session.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).all()
    
    if knowledge_bases:
        for i, kb in enumerate(knowledge_bases, 1):
            print(f"\n   [{i}] {kb.name}")
            print(f"       ID: {kb.id}")
            print(f"       状态: {kb.status.value}")
            print(f"       描述: {kb.description or '(无)'}")
            print(f"       创建时间: {kb.created_at}")
            print(f"       更新时间: {kb.updated_at}")
            print(f"       嵌入模型: {kb.embedding_model}")
            print(f"       分块策略: {kb.chunk_strategy}")
    else:
        print("   (无)")
    
    # 4. 检查数据库表结构
    print("\n4. 检查数据库表结构：")
    try:
        result = session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'knowledge_bases'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        if columns:
            print("   表 'knowledge_bases' 存在，包含以下列：")
            for col_name, col_type in columns:
                print(f"   - {col_name}: {col_type}")
        else:
            print("   ⚠️  表 'knowledge_bases' 不存在或为空")
    except Exception as e:
        print(f"   ⚠️  无法检查表结构: {str(e)}")
    
    # 5. 检查最近的数据库操作
    print("\n5. 检查数据库连接：")
    try:
        result = session.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✅ 数据库连接正常")
        print(f"   PostgreSQL 版本: {version.split(',')[0]}")
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {str(e)}")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ 导入错误: {str(e)}")
    print("\n请确保：")
    print("1. 已安装所有依赖: pip install -r requirements.txt")
    print("2. 数据库模块在正确的位置")
    print("3. 环境变量 DATABASE_URL 已设置")
except Exception as e:
    print(f"❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()


