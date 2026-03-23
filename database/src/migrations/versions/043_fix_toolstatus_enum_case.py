"""Fix toolstatus enum case to match ORM values

Revision ID: 043_fix_toolstatus_enum_case
Revises: 042_add_mcp_tools_status
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '043_fix_toolstatus_enum_case'
down_revision = '042_add_mcp_tools_status'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    type_exists = conn.execute(sa.text("""
        SELECT 1
        FROM pg_type
        WHERE typname = 'toolstatus'
        LIMIT 1
    """)).fetchone()
    if not type_exists:
        return

    labels = conn.execute(sa.text("""
        SELECT e.enumlabel
        FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = 'toolstatus'
    """)).fetchall()
    labels = {row[0] for row in labels}

    if 'active' in labels and 'ACTIVE' not in labels:
        op.execute("ALTER TYPE toolstatus RENAME VALUE 'active' TO 'ACTIVE'")
    if 'inactive' in labels and 'INACTIVE' not in labels:
        op.execute("ALTER TYPE toolstatus RENAME VALUE 'inactive' TO 'INACTIVE'")
    if 'deprecated' in labels and 'DEPRECATED' not in labels:
        op.execute("ALTER TYPE toolstatus RENAME VALUE 'deprecated' TO 'DEPRECATED'")


def downgrade() -> None:
    conn = op.get_bind()

    type_exists = conn.execute(sa.text("""
        SELECT 1
        FROM pg_type
        WHERE typname = 'toolstatus'
        LIMIT 1
    """)).fetchone()
    if not type_exists:
        return

    labels = conn.execute(sa.text("""
        SELECT e.enumlabel
        FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = 'toolstatus'
    """)).fetchall()
    labels = {row[0] for row in labels}

    if 'ACTIVE' in labels and 'active' not in labels:
        op.execute("ALTER TYPE toolstatus RENAME VALUE 'ACTIVE' TO 'active'")
    if 'INACTIVE' in labels and 'inactive' not in labels:
        op.execute("ALTER TYPE toolstatus RENAME VALUE 'INACTIVE' TO 'inactive'")
    if 'DEPRECATED' in labels and 'deprecated' not in labels:
        op.execute("ALTER TYPE toolstatus RENAME VALUE 'DEPRECATED' TO 'deprecated'")
