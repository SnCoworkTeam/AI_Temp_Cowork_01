"""create feedback tables

Revision ID: 0021_create_feedback_tables
Revises: 0020_create_entity_registry
Create Date: 2025-11-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0021_create_feedback_tables'
down_revision = '0020_create_entity_registry'
branch_labels = None
depends_on = None


def upgrade():
    # 创建用户反馈表
    op.create_table(
        'user_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.String(length=255), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('feedback_type', sa.String(length=20), nullable=False),
        sa.Column('result_id', sa.String(length=255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_feedback_query_id', 'user_feedback', ['query_id'], unique=False)
    op.create_index('idx_feedback_user_id', 'user_feedback', ['user_id'], unique=False)
    op.create_index('idx_feedback_created_at', 'user_feedback', ['created_at'], unique=False)
    
    # 创建查询日志表
    op.create_table(
        'query_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.String(length=255), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('success', sa.String(length=10), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_query_log_query_id', 'query_logs', ['query_id'], unique=False)
    op.create_index('idx_query_log_user_id', 'query_logs', ['user_id'], unique=False)
    op.create_index('idx_query_log_created_at', 'query_logs', ['created_at'], unique=False)
    op.create_index('idx_query_log_success', 'query_logs', ['success'], unique=False)


def downgrade():
    op.drop_index('idx_query_log_success', table_name='query_logs')
    op.drop_index('idx_query_log_created_at', table_name='query_logs')
    op.drop_index('idx_query_log_user_id', table_name='query_logs')
    op.drop_index('idx_query_log_query_id', table_name='query_logs')
    op.drop_table('query_logs')
    
    op.drop_index('idx_feedback_created_at', table_name='user_feedback')
    op.drop_index('idx_feedback_user_id', table_name='user_feedback')
    op.drop_index('idx_feedback_query_id', table_name='user_feedback')
    op.drop_table('user_feedback')

