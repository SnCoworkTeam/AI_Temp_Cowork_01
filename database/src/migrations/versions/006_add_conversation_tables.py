"""添加对话和消息表

Revision ID: 006_add_conversation_tables
Revises: 005_add_performance_indexes
Create Date: 2025-11-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers
revision = '006_add_conversation_tables'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """添加conversations和messages表"""

    # 创建conversations表
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False, server_default='新对话'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_archived', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 创建索引
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_is_archived', 'conversations', ['is_archived'])
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'])

    # 创建messages表
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', 'system', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='messagestatus'), nullable=False, server_default='completed'),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('execution_time', sa.Integer, nullable=True),
        sa.Column('tool_calls', JSONB, nullable=True),
        sa.Column('sources', JSONB, nullable=True),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 创建索引
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_role', 'messages', ['role'])
    op.create_index('ix_messages_status', 'messages', ['status'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])


def downgrade():
    """删除conversations和messages表"""
    op.drop_table('messages')
    op.drop_table('conversations')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS messagerole")
    op.execute("DROP TYPE IF EXISTS messagestatus")
