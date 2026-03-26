"""添加基础数据表

Revision ID: 031
Revises: 030
Create Date: 2025-12-24

创建基础数据分类表和项目基础数据关联表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade():
    """创建基础数据表"""
    print("=" * 50)
    print("创建基础数据表")
    print("=" * 50)

    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 创建基础数据分类表
    if 'pm_basic_data_categories' in existing_tables:
        print("表 pm_basic_data_categories 已存在，跳过创建")
    else:
        op.create_table(
        'pm_basic_data_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='分类ID'),
        sa.Column('category_type', sa.String(50), nullable=False, comment='分类类型'),
        sa.Column('code', sa.String(50), nullable=False, comment='分类编码'),
        sa.Column('name', sa.String(200), nullable=False, comment='分类名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='分类描述'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True, comment='父分类ID'),
        sa.Column('sort_order', sa.Integer(), default=0, comment='排序顺序'),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False, comment='是否启用'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default=dict, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),

        # 外键
        sa.ForeignKeyConstraint(['parent_id'], ['pm_basic_data_categories.id'], ondelete='SET NULL'),

        # 唯一约束
        sa.UniqueConstraint('category_type', 'code', name='uq_category_type_code'),

        comment='基础数据分类表'
    )

        # 创建索引（如果不存在）
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('pm_basic_data_categories')]
        if 'idx_basic_data_categories_type' not in existing_indexes:
            op.create_index('idx_basic_data_categories_type', 'pm_basic_data_categories', ['category_type'])
        if 'idx_basic_data_categories_code' not in existing_indexes:
            op.create_index('idx_basic_data_categories_code', 'pm_basic_data_categories', ['code'])
        if 'idx_basic_data_categories_parent' not in existing_indexes:
            op.create_index('idx_basic_data_categories_parent', 'pm_basic_data_categories', ['parent_id'])
        if 'idx_basic_data_categories_active' not in existing_indexes:
            op.create_index('idx_basic_data_categories_active', 'pm_basic_data_categories', ['is_active'])

    # 创建项目基础数据关联表
    if 'pm_project_basic_data_mapping' in existing_tables:
        print("表 pm_project_basic_data_mapping 已存在，跳过创建")
    else:
        op.create_table(
        'pm_project_basic_data_mapping',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='关联ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False, comment='分类ID'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default=dict, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),

        # 外键
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['pm_basic_data_categories.id'], ondelete='CASCADE'),

        # 唯一约束
        sa.UniqueConstraint('project_id', 'category_id', name='uq_project_category'),

        comment='项目基础数据关联表'
    )

        # 创建索引（如果不存在）
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('pm_project_basic_data_mapping')]
        if 'idx_project_basic_data_project' not in existing_indexes:
            op.create_index('idx_project_basic_data_project', 'pm_project_basic_data_mapping', ['project_id'])
        if 'idx_project_basic_data_category' not in existing_indexes:
            op.create_index('idx_project_basic_data_category', 'pm_project_basic_data_mapping', ['category_id'])

    print("基础数据表创建完成！")
    print("=" * 50)


def downgrade():
    """删除基础数据表"""
    op.drop_index('idx_project_basic_data_category', table_name='pm_project_basic_data_mapping')
    op.drop_index('idx_project_basic_data_project', table_name='pm_project_basic_data_mapping')
    op.drop_table('pm_project_basic_data_mapping')

    op.drop_index('idx_basic_data_categories_active', table_name='pm_basic_data_categories')
    op.drop_index('idx_basic_data_categories_parent', table_name='pm_basic_data_categories')
    op.drop_index('idx_basic_data_categories_code', table_name='pm_basic_data_categories')
    op.drop_index('idx_basic_data_categories_type', table_name='pm_basic_data_categories')
    op.drop_table('pm_basic_data_categories')

