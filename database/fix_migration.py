from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

def upgrade():
    # 检查表是否已存在
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    if 'pm_projects' not in existing_tables:
        op.create_table(
            'pm_projects',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('project_code', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='planning'),
            sa.Column('priority', sa.String(length=20), nullable=True, server_default='medium'),
            sa.Column('manager_id', sa.UUID(), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('actual_start_date', sa.Date(), nullable=True),
            sa.Column('actual_end_date', sa.Date(), nullable=True),
            sa.Column('budget', sa.Float(), nullable=True),
            sa.Column('actual_cost', sa.Float(), nullable=True),
            sa.Column('progress_percent', sa.Float(), nullable=True, server_default='0'),
            sa.Column('health_score', sa.Float(), nullable=True, server_default='0'),
            sa.Column('workflow_id', sa.UUID(), nullable=True),
            sa.Column('knowledge_base_id', sa.UUID(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('project_code'),
            sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ),
            sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], )
        )
    else:
        print("Table pm_projects already exists, skipping creation")

def downgrade():
    op.drop_table('pm_projects')
