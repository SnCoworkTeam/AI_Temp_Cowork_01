"""
添加提示词模板表

Revision ID: 019
Revises: 018
Create Date: 2025-11-27

功能: 创建提示词模板表和版本历史表，支持提示词的统一管理和版本控制
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    """创建提示词模板相关表"""
    print("=" * 50)
    print("创建提示词模板表")
    print("=" * 50)
    
    # 1. 创建 prompt_templates 表
    print("创建 prompt_templates 表...")
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='提示词名称'),
        sa.Column('category', sa.String(length=100), nullable=False, comment='任务分类'),
        sa.Column('description', sa.Text(), nullable=True, comment='描述'),
        sa.Column('system_prompt', sa.Text(), nullable=True, comment='系统提示词'),
        sa.Column('examples', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Few-Shot示例（JSON数组）'),
        sa.Column('temperature', sa.Float(), nullable=True, server_default='0.3', comment='温度参数'),
        sa.Column('max_tokens', sa.Integer(), nullable=True, server_default='2000', comment='最大token数'),
        sa.Column('top_p', sa.Float(), nullable=True, server_default='0.9', comment='Top-p参数'),
        sa.Column('frequency_penalty', sa.Float(), nullable=True, server_default='0.0', comment='频率惩罚'),
        sa.Column('presence_penalty', sa.Float(), nullable=True, server_default='0.0', comment='存在惩罚'),
        sa.Column('stop_sequences', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='停止序列（JSON数组）'),
        sa.Column('output_format', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='输出格式定义（JSON对象）'),
        sa.Column('dynamic_placeholders', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='动态占位符列表（JSON数组）'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='版本号'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true', comment='是否激活'),
        sa.Column('created_by', sa.String(length=100), nullable=True, comment='创建人'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='扩展元数据（JSON对象）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='提示词模板表'
    )
    
    # 创建索引
    op.create_index('ix_prompt_templates_id', 'prompt_templates', ['id'], unique=False)
    op.create_index('ix_prompt_templates_name', 'prompt_templates', ['name'], unique=False)
    op.create_index('ix_prompt_templates_category', 'prompt_templates', ['category'], unique=False)
    op.create_index('ix_prompt_templates_is_active', 'prompt_templates', ['is_active'], unique=False)
    op.create_index('ix_prompt_templates_category_active', 'prompt_templates', ['category', 'is_active'], unique=False)
    
    print("✅ prompt_templates 表已创建")
    
    # 2. 创建 prompt_template_versions 表
    print("创建 prompt_template_versions 表...")
    op.create_table(
        'prompt_template_versions',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('template_id', sa.Integer(), nullable=False, comment='模板ID'),
        sa.Column('version', sa.Integer(), nullable=False, comment='版本号'),
        sa.Column('system_prompt', sa.Text(), nullable=True, comment='系统提示词'),
        sa.Column('examples', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Few-Shot示例'),
        sa.Column('temperature', sa.Float(), nullable=True, comment='温度参数'),
        sa.Column('max_tokens', sa.Integer(), nullable=True, comment='最大token数'),
        sa.Column('change_reason', sa.Text(), nullable=True, comment='变更原因'),
        sa.Column('changed_by', sa.String(length=100), nullable=True, comment='变更人'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.ForeignKeyConstraint(['template_id'], ['prompt_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='提示词模板版本历史表'
    )
    
    # 创建索引
    op.create_index('ix_prompt_template_versions_id', 'prompt_template_versions', ['id'], unique=False)
    op.create_index('ix_prompt_template_versions_template_id', 'prompt_template_versions', ['template_id'], unique=False)
    op.create_index('ix_prompt_template_versions_template_version', 'prompt_template_versions', ['template_id', 'version'], unique=False)
    
    print("✅ prompt_template_versions 表已创建")
    
    print("=" * 50)
    print("提示词模板表创建完成")
    print("=" * 50)


def downgrade():
    """删除提示词模板相关表"""
    print("删除提示词模板表...")
    
    op.drop_index('ix_prompt_template_versions_template_version', table_name='prompt_template_versions')
    op.drop_index('ix_prompt_template_versions_template_id', table_name='prompt_template_versions')
    op.drop_index('ix_prompt_template_versions_id', table_name='prompt_template_versions')
    op.drop_table('prompt_template_versions')
    
    op.drop_index('ix_prompt_templates_category_active', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_is_active', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_category', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_name', table_name='prompt_templates')
    op.drop_index('ix_prompt_templates_id', table_name='prompt_templates')
    op.drop_table('prompt_templates')
    
    print("✅ 提示词模板表已删除")

