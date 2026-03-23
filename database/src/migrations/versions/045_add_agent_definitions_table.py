"""add agent definitions table

Revision ID: 045_add_agent_definitions_table
Revises: 044_make_mcp_tools_avg_execution_time_nullable
Create Date: 2026-02-27 20:05:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "045_add_agent_definitions_table"
down_revision = "044_make_mcp_tools_avg_execution_time_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    agent_status_enum = postgresql.ENUM(
        "active",
        "inactive",
        "training",
        "error",
        name="agentdefstatus",
        create_type=False,
    )
    agent_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "agent_definitions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "capabilities",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column(
            "config",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("status", agent_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(), nullable=True),
    )

    op.create_index("idx_agent_definitions_name", "agent_definitions", ["name"])
    op.create_index("idx_agent_definitions_status", "agent_definitions", ["status"])


def downgrade() -> None:
    op.drop_index("idx_agent_definitions_status", table_name="agent_definitions")
    op.drop_index("idx_agent_definitions_name", table_name="agent_definitions")
    op.drop_table("agent_definitions")

    agent_status_enum = postgresql.ENUM(
        "active",
        "inactive",
        "training",
        "error",
        name="agentdefstatus",
        create_type=False,
    )
    agent_status_enum.drop(op.get_bind(), checkfirst=True)
