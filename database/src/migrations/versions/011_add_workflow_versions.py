"""add workflow versions

Revision ID: 011_add_workflow_versions
Revises: 010_add_token_blacklist
Create Date: 2024-01-XX 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_add_workflow_versions'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建workflow_versions和workflow_version_tags表"""
    
    # 创建 workflow_versions 表
    op.create_table(
        'workflow_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('definition', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('changes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'version', name='uq_workflow_version')
    )
    
    # 创建 workflow_version_tags 表
    op.create_table(
        'workflow_version_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['workflow_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_id', 'tag', name='uq_version_tag')
    )
    
    # 创建索引
    op.create_index('ix_workflow_versions_id', 'workflow_versions', ['id'], unique=False)
    op.create_index('ix_workflow_versions_workflow_id', 'workflow_versions', ['workflow_id'], unique=False)
    op.create_index('ix_workflow_versions_version', 'workflow_versions', ['version'], unique=False)
    op.create_index('ix_workflow_versions_is_current', 'workflow_versions', ['is_current'], unique=False)
    op.create_index('ix_workflow_version_tags_id', 'workflow_version_tags', ['id'], unique=False)
    op.create_index('ix_workflow_version_tags_version_id', 'workflow_version_tags', ['version_id'], unique=False)
    op.create_index('ix_workflow_version_tags_tag', 'workflow_version_tags', ['tag'], unique=False)
    
    # 创建复合索引（用于查询优化）
    op.create_index(
        'ix_workflow_versions_workflow_version_number',
        'workflow_versions',
        ['workflow_id', 'version_number'],
        unique=False
    )


def downgrade() -> None:
    """删除workflow_versions和workflow_version_tags表"""
    
    # 删除索引
    op.drop_index('ix_workflow_versions_workflow_version_number', table_name='workflow_versions')
    op.drop_index('ix_workflow_version_tags_tag', table_name='workflow_version_tags')
    op.drop_index('ix_workflow_version_tags_version_id', table_name='workflow_version_tags')
    op.drop_index('ix_workflow_version_tags_id', table_name='workflow_version_tags')
    op.drop_index('ix_workflow_versions_is_current', table_name='workflow_versions')
    op.drop_index('ix_workflow_versions_version', table_name='workflow_versions')
    op.drop_index('ix_workflow_versions_workflow_id', table_name='workflow_versions')
    op.drop_index('ix_workflow_versions_id', table_name='workflow_versions')
    
    # 删除表
    op.drop_table('workflow_version_tags')
    op.drop_table('workflow_versions')

