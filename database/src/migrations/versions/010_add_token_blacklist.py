"""Add token blacklist table

Revision ID: 010
Revises: 009
Create Date: 2024-01-XX 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009_add_agent_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建token_blacklist表"""
    conn = op.get_bind()
    table_exists = conn.execute(sa.text("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'token_blacklist'
        LIMIT 1
    """)).fetchone()

    if not table_exists:
        op.create_table(
            'token_blacklist',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('token_id', sa.String(64), nullable=False),
            sa.Column('token_type', sa.String(20), nullable=False),
            sa.Column('user_id', sa.String(36), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('revoked_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('token_id')
        )

    # 创建索引（若不存在）
    def ensure_index(index_name: str, columns: list[str]) -> None:
        exists = conn.execute(sa.text("""
            SELECT 1
            FROM pg_indexes
            WHERE tablename = 'token_blacklist' AND indexname = :idx
            LIMIT 1
        """), {"idx": index_name}).fetchone()
        if not exists:
            op.create_index(index_name, 'token_blacklist', columns)

    ensure_index('ix_token_blacklist_token_id', ['token_id'])
    ensure_index('ix_token_blacklist_user_id', ['user_id'])
    ensure_index('ix_token_blacklist_expires_at', ['expires_at'])
    ensure_index('idx_token_blacklist_user_expires', ['user_id', 'expires_at'])
    ensure_index('idx_token_blacklist_expires', ['expires_at'])


def downgrade() -> None:
    """删除token_blacklist表"""
    op.drop_index('idx_token_blacklist_expires', table_name='token_blacklist')
    op.drop_index('idx_token_blacklist_user_expires', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_expires_at', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_user_id', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_token_id', table_name='token_blacklist')
    op.drop_table('token_blacklist')
