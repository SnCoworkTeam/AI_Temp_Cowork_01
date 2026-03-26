"""create value_metrics table

Revision ID: 0022_create_value_metrics_table
Revises: 0021_create_feedback_tables
Create Date: 2025-11-28 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0022_create_value_metrics_table'
down_revision = '0021_create_feedback_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 创建价值指标表
    op.create_table(
        'value_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('time_saved_seconds', sa.Float(), nullable=True),
        sa.Column('error_reduced', sa.Integer(), nullable=True),
        sa.Column('efficiency_improvement', sa.Float(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_value_metrics_operation', 'value_metrics', ['operation'], unique=False)
    op.create_index('idx_value_metrics_user_id', 'value_metrics', ['user_id'], unique=False)
    op.create_index('idx_value_metrics_created_at', 'value_metrics', ['created_at'], unique=False)


def downgrade():
    op.drop_index('idx_value_metrics_created_at', table_name='value_metrics')
    op.drop_index('idx_value_metrics_user_id', table_name='value_metrics')
    op.drop_index('idx_value_metrics_operation', table_name='value_metrics')
    op.drop_table('value_metrics')

