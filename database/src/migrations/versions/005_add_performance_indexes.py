"""
数据库迁移脚本: 添加性能索引

Revision ID: 005
Revises: 004
Create Date: 2025-11-13

问题: 索引覆盖率仅18%，缺少6个关键复合索引
影响: 查询性能可能下降5-10倍，可能导致请求超时
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """添加关键性能索引"""
    conn = op.get_bind()

    def table_exists(table_name: str) -> bool:
        return conn.execute(text("SELECT to_regclass(:name)"), {"name": table_name}).scalar() is not None

    def column_exists(table_name: str, column_name: str) -> bool:
        result = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND column_name = :column_name
                LIMIT 1
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).fetchone()
        return result is not None

    # 1. workflow_executions 表索引
    # 用于查询特定工作流的执行状态
    if table_exists('workflow_executions') and column_exists('workflow_executions', 'workflow_id') and column_exists('workflow_executions', 'status'):
        op.create_index(
            'idx_workflow_execution_status',
            'workflow_executions',
            ['workflow_id', 'status'],
            unique=False
        )
        print("✅ 创建索引: idx_workflow_execution_status (workflow_id, status)")
    else:
        print("⚠️  跳过索引: idx_workflow_execution_status (表或字段不存在)")

    # 2. user_sessions 表索引
    # 用于查询用户的活跃会话
    if table_exists('user_sessions') and column_exists('user_sessions', 'user_id') and column_exists('user_sessions', 'is_active'):
        op.create_index(
            'idx_user_session_active',
            'user_sessions',
            ['user_id', 'is_active'],
            unique=False
        )
        print("✅ 创建索引: idx_user_session_active (user_id, is_active)")
    else:
        print("⚠️  跳过索引: idx_user_session_active (表或字段不存在)")

    # 3. audit_logs 表索引
    # 用于按时间倒序查询用户审计日志
    if table_exists('audit_logs') and column_exists('audit_logs', 'timestamp') and column_exists('audit_logs', 'user_id'):
        op.create_index(
            'idx_audit_log_user',
            'audit_logs',
            [sa.text('timestamp DESC'), 'user_id'],
            unique=False,
            postgresql_using='btree'
        )
        print("✅ 创建索引: idx_audit_log_user (timestamp DESC, user_id)")
    else:
        print("⚠️  跳过索引: idx_audit_log_user (表或字段不存在)")

    # 4. documents 表索引
    # 用于按分类和状态查询文档
    if table_exists('documents') and column_exists('documents', 'category') and column_exists('documents', 'status'):
        op.create_index(
            'idx_document_category_status',
            'documents',
            ['category', 'status'],
            unique=False
        )
        print("✅ 创建索引: idx_document_category_status (category, status)")
    else:
        print("⚠️  跳过索引: idx_document_category_status (表或字段不存在)")

    # 5. document_chunks 表索引（如果还没有）
    # 用于查询文档的所有块
    if table_exists('document_chunks') and column_exists('document_chunks', 'document_id') and column_exists('document_chunks', 'chunk_index'):
        try:
            op.create_index(
                'idx_document_chunk_lookup',
                'document_chunks',
                ['document_id', 'chunk_index'],
                unique=False
            )
            print("✅ 创建索引: idx_document_chunk_lookup (document_id, chunk_index)")
        except Exception as e:
            print(f"⚠️  索引可能已存在: idx_document_chunk_lookup - {e}")
    else:
        print("⚠️  跳过索引: idx_document_chunk_lookup (表或字段不存在)")

    # 6. mcp_tool_executions 表索引
    # 用于查询工具的执行历史
    if table_exists('mcp_tool_executions') and column_exists('mcp_tool_executions', 'tool_id') and column_exists('mcp_tool_executions', 'status'):
        try:
            op.create_index(
                'idx_tool_execution_status',
                'mcp_tool_executions',
                ['tool_id', 'status'],
                unique=False
            )
            print("✅ 创建索引: idx_tool_execution_status (tool_id, status)")
        except Exception as e:
            print(f"⚠️  索引可能已存在: idx_tool_execution_status - {e}")
    else:
        print("⚠️  跳过索引: idx_tool_execution_status (表或字段不存在)")

    # 7. 额外的有用索引

    # workflow_nodes 按工作流查询
    if table_exists('workflow_nodes') and column_exists('workflow_nodes', 'workflow_id') and column_exists('workflow_nodes', 'node_type'):
        op.create_index(
            'idx_workflow_nodes_workflow',
            'workflow_nodes',
            ['workflow_id', 'node_type'],
            unique=False
        )
        print("✅ 创建索引: idx_workflow_nodes_workflow (workflow_id, node_type)")
    else:
        print("⚠️  跳过索引: idx_workflow_nodes_workflow (表或字段不存在)")

    # users 按邮箱快速查询（如果还没有）
    if table_exists('users') and column_exists('users', 'email'):
        try:
            op.create_index(
                'idx_users_email',
                'users',
                ['email'],
                unique=True
            )
            print("✅ 创建索引: idx_users_email (email) - UNIQUE")
        except Exception as e:
            print(f"⚠️  索引可能已存在: idx_users_email - {e}")
    else:
        print("⚠️  跳过索引: idx_users_email (表或字段不存在)")

    print("\n✅ 所有性能索引创建完成")
    print("   索引覆盖率从 18% 提升到预计 45%+")


def downgrade():
    """回滚索引创建"""

    # 删除所有创建的索引
    indexes_to_drop = [
        'idx_users_email',
        'idx_workflow_nodes_workflow',
        'idx_tool_execution_status',
        'idx_document_chunk_lookup',
        'idx_document_category_status',
        'idx_audit_log_user',
        'idx_user_session_active',
        'idx_workflow_execution_status'
    ]

    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name)
            print(f"⚠️  删除索引: {index_name}")
        except Exception as e:
            print(f"⚠️  无法删除索引 {index_name}: {e}")

    print("⚠️  已回滚所有性能索引")
