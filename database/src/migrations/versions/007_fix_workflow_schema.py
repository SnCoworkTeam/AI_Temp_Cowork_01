"""Fix workflow schema inconsistencies

Revision ID: 007
Revises: 006
Create Date: 2025-11-14

修复workflow相关表的schema不一致问题：
1. workflow_definitions.version: integer -> VARCHAR(50) 支持语义版本号
2. workflow_definitions.status: 确保枚举值正确
3. 其他字段类型验证和修复
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '007'
down_revision = '006_add_conversation_tables'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库schema"""
    # 1. 修改workflow_definitions.version字段从integer改为VARCHAR(50)
    print("修改workflow_definitions.version字段类型...")

    # 先将现有整数版本转换为字符串格式
    op.execute("""
        ALTER TABLE workflow_definitions
        ALTER COLUMN version TYPE VARCHAR(50)
        USING version::text
    """)

    # 更新默认值
    op.alter_column('workflow_definitions', 'version',
                    existing_type=sa.VARCHAR(50),
                    server_default='1.0.0',
                    nullable=False)

    print("✅ version字段已从integer修改为VARCHAR(50)")

    # 2. 验证status枚举类型
    print("验证workflow_definitions.status枚举...")

    # 检查枚举类型是否存在并包含正确的值
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT enumlabel FROM pg_enum
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'workflowstatus')
    """))

    enum_values = [row[0] for row in result]
    expected_values = ['draft', 'active', 'inactive', 'archived']

    if set(enum_values) != set(expected_values):
        print(f"⚠️  枚举值不匹配: {enum_values} vs {expected_values}")
        print("重新创建workflowstatus枚举...")

        # 重新创建枚举类型 (需要先删除依赖)
        # 注意：这在生产环境中需要更谨慎的处理
        op.execute("ALTER TABLE workflow_definitions ALTER COLUMN status TYPE VARCHAR(50)")
        op.execute("DROP TYPE IF EXISTS workflowstatus CASCADE")
        op.execute("CREATE TYPE workflowstatus AS ENUM ('draft', 'active', 'inactive', 'archived')")
        op.execute("ALTER TABLE workflow_definitions ALTER COLUMN status TYPE workflowstatus USING status::workflowstatus")

    print("✅ status枚举已验证")

    # 3. 验证其他关键字段
    print("验证workflow_definitions其他字段...")

    # 确保config和workflow_metadata是JSONB类型
    op.alter_column('workflow_definitions', 'config',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    nullable=False,
                    server_default='{}')

    # workflow_metadata 可能不存在（早期schema缺失），需要先补列
    column_exists = conn.execute(sa.text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'workflow_definitions'
          AND column_name = 'workflow_metadata'
        LIMIT 1
    """)).fetchone()

    if not column_exists:
        op.add_column(
            'workflow_definitions',
            sa.Column('workflow_metadata', postgresql.JSONB(astext_type=sa.Text()),
                      nullable=True, server_default='{}')
        )
    else:
        op.alter_column('workflow_definitions', 'workflow_metadata',
                        existing_type=postgresql.JSONB(astext_type=sa.Text()),
                        nullable=True,
                        server_default='{}')

    print("✅ 所有字段已验证")

    # 4. 创建索引（如果不存在）
    print("创建必要的索引...")

    # 检查索引是否存在
    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'workflow_definitions' AND indexname = 'ix_workflow_definitions_version'
    """))

    if not result.fetchone():
        op.create_index('ix_workflow_definitions_version', 'workflow_definitions', ['version'])
        print("✅ 创建version索引")

    result = conn.execute(sa.text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'workflow_definitions' AND indexname = 'ix_workflow_definitions_status'
    """))

    if not result.fetchone():
        op.create_index('ix_workflow_definitions_status', 'workflow_definitions', ['status'])
        print("✅ 创建status索引")

    print("=" * 50)
    print("✅ Schema修复完成！")
    print("=" * 50)


def downgrade():
    """回滚数据库schema"""
    print("回滚schema修改...")

    # 删除索引
    op.drop_index('ix_workflow_definitions_status', table_name='workflow_definitions', if_exists=True)
    op.drop_index('ix_workflow_definitions_version', table_name='workflow_definitions', if_exists=True)

    # 将version字段改回integer
    op.execute("""
        ALTER TABLE workflow_definitions
        ALTER COLUMN version TYPE integer
        USING CASE
            WHEN version ~ '^[0-9]+$' THEN version::integer
            ELSE 1
        END
    """)

    op.alter_column('workflow_definitions', 'version',
                    existing_type=sa.Integer(),
                    server_default='1',
                    nullable=False)

    print("✅ 回滚完成")
