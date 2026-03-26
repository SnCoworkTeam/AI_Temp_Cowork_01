"""Add notification model

Revision ID: 039_add_notification_model
Revises: 038_add_project_program_and_plan_models
Create Date: 2025-12-26 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '039_add_notification_model'
down_revision = '038_add_project_program_and_plan_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'notifications' in existing_tables:
        print("表 notifications 已存在，跳过创建")
        return

    # 创建通知表
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='通知ID'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='用户ID'),
        sa.Column('type', sa.String(50), nullable=False, comment='通知类型'),
        sa.Column('title', sa.String(200), nullable=False, comment='通知标题'),
        sa.Column('message', sa.Text(), nullable=False, comment='通知消息'),
        sa.Column('link', sa.String(500), nullable=True, comment='跳转链接'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false', comment='是否已读'),
        sa.Column('read_at', sa.DateTime(), nullable=True, comment='阅读时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_notification_user', ondelete='CASCADE'),
        sa.Index('idx_notifications_user_id', 'user_id'),
        sa.Index('idx_notifications_is_read', 'is_read'),
        sa.Index('idx_notifications_type', 'type'),
        sa.Index('idx_notifications_user_read', 'user_id', 'is_read'),
        comment='用户通知表'
    )


def downgrade() -> None:
    op.drop_table('notifications')

