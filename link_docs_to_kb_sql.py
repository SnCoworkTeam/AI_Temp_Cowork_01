#!/usr/bin/env python3
"""
通过SQL直接更新文档的knowledge_base_id
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# 数据库连接配置
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ai_platform")
DB_USER = os.getenv("DB_USER", "ai_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ai_password")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SAP MM知识库ID（从之前的输出获取）
SAP_MM_KB_ID = "56a3c7c2-c120-4914-b4f3-ab0241dac4af"

def link_documents():
    """将SAP MM文档关联到知识库"""
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("=" * 60)
        print("关联SAP MM文档到知识库")
        print("=" * 60)
        print()
        
        # 查找所有SAP MM相关文档
        query = text("""
            SELECT id, filename, title, knowledge_base_id
            FROM documents
            WHERE (filename LIKE '%SAP%' OR filename LIKE '%MM%' OR 
                   title LIKE '%SAP%' OR title LIKE '%MM%' OR
                   filename LIKE '%sap_mm%')
            AND (knowledge_base_id IS NULL OR knowledge_base_id != :kb_id)
        """)
        
        result = session.execute(query, {"kb_id": SAP_MM_KB_ID})
        documents = result.fetchall()
        
        print(f"找到 {len(documents)} 个需要关联的文档")
        print()
        
        if not documents:
            print("✅ 所有文档已关联")
            session.close()
            return
        
        # 更新文档的knowledge_base_id
        update_query = text("""
            UPDATE documents
            SET knowledge_base_id = :kb_id
            WHERE (filename LIKE '%SAP%' OR filename LIKE '%MM%' OR 
                   title LIKE '%SAP%' OR title LIKE '%MM%' OR
                   filename LIKE '%sap_mm%')
            AND (knowledge_base_id IS NULL OR knowledge_base_id != :kb_id)
        """)
        
        result = session.execute(update_query, {"kb_id": SAP_MM_KB_ID})
        session.commit()
        
        updated_count = result.rowcount
        print(f"✅ 成功更新 {updated_count} 个文档")
        print()
        
        # 验证更新结果
        verify_query = text("""
            SELECT COUNT(*) as count
            FROM documents
            WHERE knowledge_base_id = :kb_id
        """)
        
        verify_result = session.execute(verify_query, {"kb_id": SAP_MM_KB_ID})
        linked_count = verify_result.fetchone()[0]
        
        print(f"知识库中的文档数: {linked_count}")
        print()
        
        # 更新知识库的文档计数
        update_kb_count = text("""
            UPDATE knowledge_bases
            SET document_count = (
                SELECT COUNT(*) 
                FROM documents 
                WHERE knowledge_base_id = :kb_id
            )
            WHERE id = :kb_id
        """)
        
        session.execute(update_kb_count, {"kb_id": SAP_MM_KB_ID})
        session.commit()
        
        print("✅ 知识库文档计数已更新")
        print()
        print("=" * 60)
        print("关联完成")
        print("=" * 60)
        print(f"✅ 成功关联 {updated_count} 个文档到SAP MM知识库")
        print(f"知识库ID: {SAP_MM_KB_ID}")
        print()
        print("前端现在应该可以看到这些文档了！")
        
        session.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    link_documents()




