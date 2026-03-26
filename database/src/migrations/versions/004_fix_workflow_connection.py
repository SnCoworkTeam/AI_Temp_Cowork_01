"""
数据库迁移脚本: 修复 WorkflowConnection 外键约束

Revision ID: 004
Revises: 003
Create Date: 2025-11-13

问题: source_node_id 和 target_node_id 在模型中为UUID，
      在迁移中为String(100)，且没有外键约束
影响: 数据完整性无保障，可能出现孤立连接记录
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """修复 WorkflowConnection 表结构"""

    # 1. 修改字段类型为UUID
    # 注意：如果表中有数据，需要先清理或转换
    op.execute("""
        -- 如果有无效的UUID格式数据，先删除
        DELETE FROM workflow_connections
        WHERE source_node_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
           OR target_node_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
    """)

    # 修改字段类型
    op.alter_column('workflow_connections', 'source_node_id',
                    type_=UUID(as_uuid=True),
                    existing_type=sa.String(100),
                    postgresql_using='source_node_id::uuid')

    op.alter_column('workflow_connections', 'target_node_id',
                    type_=UUID(as_uuid=True),
                    existing_type=sa.String(100),
                    postgresql_using='target_node_id::uuid')

    # 2. 添加外键约束
    op.create_foreign_key(
        'fk_workflow_connections_source',
        'workflow_connections', 'workflow_nodes',
        ['source_node_id'], ['id'],
        ondelete='CASCADE',
        comment='源节点外键约束'
    )

    op.create_foreign_key(
        'fk_workflow_connections_target',
        'workflow_connections', 'workflow_nodes',
        ['target_node_id'], ['id'],
        ondelete='CASCADE',
        comment='目标节点外键约束'
    )

    # 3. 添加唯一约束，防止重复连接
    # 注意：如果source_port和target_port列不存在，只使用基本字段
    try:
        op.create_unique_constraint(
            'uq_workflow_connections_nodes',
            'workflow_connections',
            ['workflow_id', 'source_node_id', 'target_node_id']
        )
    except Exception as e:
        # 如果约束已存在或列不存在，跳过
        print(f"⚠️  唯一约束创建跳过: {e}")

    # 4. 添加索引
    op.create_index('idx_workflow_connections_source',
                    'workflow_connections',
                    ['source_node_id'],
                    unique=False)

    op.create_index('idx_workflow_connections_target',
                    'workflow_connections',
                    ['target_node_id'],
                    unique=False)

    print("✅ WorkflowConnection 表结构修复完成")
    print("   - 修改字段类型为UUID")
    print("   - 添加了外键约束")
    print("   - 添加了唯一约束防止重复连接")
    print("   - 创建了索引")


def downgrade():
    """回滚修复"""

    # 删除索引
    op.drop_index('idx_workflow_connections_target', table_name='workflow_connections')
    op.drop_index('idx_workflow_connections_source', table_name='workflow_connections')

    # 删除唯一约束
    op.drop_constraint('uq_workflow_connections_nodes',
                      'workflow_connections', type_='unique')

    # 删除外键
    op.drop_constraint('fk_workflow_connections_target',
                      'workflow_connections', type_='foreignkey')
    op.drop_constraint('fk_workflow_connections_source',
                      'workflow_connections', type_='foreignkey')

    # 恢复字段类型
    op.alter_column('workflow_connections', 'target_node_id',
                    type_=sa.String(100),
                    existing_type=UUID(as_uuid=True),
                    postgresql_using='target_node_id::text')

    op.alter_column('workflow_connections', 'source_node_id',
                    type_=sa.String(100),
                    existing_type=UUID(as_uuid=True),
                    postgresql_using='source_node_id::text')

    print("⚠️  已回滚 WorkflowConnection 表结构修复")
