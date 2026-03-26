"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 先创建枚举类型（如果不存在）
    # 使用 DO 块来检查并创建枚举类型，避免重复创建错误
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userstatus AS ENUM ('active', 'inactive', 'suspended', 'deleted');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE workflowstatus AS ENUM ('draft', 'active', 'inactive', 'archived');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nodetype AS ENUM ('start', 'end', 'llm', 'tool', 'condition', 'transform', 'http', 'delay', 'log', 'knowledge_search', 'document_processing', 'knowledge_enhancement');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE executionstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documenttype AS ENUM ('pdf', 'word', 'excel', 'text', 'markdown', 'unknown');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE documentstatus AS ENUM ('uploading', 'processing', 'processed', 'failed', 'deleted');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE configcategory AS ENUM ('system', 'feature', 'integration', 'security', 'performance');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE auditaction AS ENUM ('create', 'read', 'update', 'delete', 'execute', 'login', 'logout', 'permission_denied');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # 创建用户相关表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'inactive', 'suspended', 'deleted', name='userstatus', create_type=False), nullable=False, server_default='active'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(50), nullable=True),
        sa.Column('user_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource', sa.String(100), nullable=True),
        sa.Column('action', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
    )
    
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id']),
    )
    
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('access_token', sa.String(500), nullable=True),
        sa.Column('refresh_token', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    
    # 创建工作流相关表
    op.create_table(
        'workflow_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'inactive', 'archived', name='workflowstatus', create_type=False), nullable=False, server_default='draft'),
        sa.Column('config', postgresql.JSONB(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    
    op.create_table(
        'workflow_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('node_id', sa.String(100), nullable=False),
        sa.Column('node_type', postgresql.ENUM('start', 'end', 'llm', 'tool', 'condition', 'transform', 'http', 'delay', 'log', 'knowledge_search', 'document_processing', 'knowledge_enhancement', name='nodetype', create_type=False), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=True),
        sa.Column('position_y', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
    )
    
    op.create_table(
        'workflow_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('source_node_id', sa.String(100), nullable=False),
        sa.Column('target_node_id', sa.String(100), nullable=False),
        sa.Column('condition', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
    )
    
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('executed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', name='executionstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('execution_log', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id']),
        sa.ForeignKeyConstraint(['executed_by'], ['users.id']),
    )
    
    # 创建知识库相关表
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(500), nullable=False, index=True),
        sa.Column('file_type', postgresql.ENUM('pdf', 'word', 'excel', 'text', 'markdown', 'unknown', name='documenttype', create_type=False), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('status', postgresql.ENUM('uploading', 'processing', 'processed', 'failed', 'deleted', name='documentstatus', create_type=False), nullable=False, server_default='uploading'),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
    )
    
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('vector_id', sa.String(200), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    )
    
    op.create_table(
        'knowledge_graph_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('concept', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    op.create_table(
        'knowledge_graph_edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_node_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['source_node_id'], ['knowledge_graph_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_node_id'], ['knowledge_graph_nodes.id'], ondelete='CASCADE'),
    )
    
    # 创建MCP工具相关表
    op.create_table(
        'mcp_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tool_type', sa.String(50), nullable=False),
        sa.Column('parameters_schema', postgresql.JSONB(), nullable=True),
        sa.Column('endpoint_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    op.create_table(
        'mcp_tool_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('executed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parameters', postgresql.JSONB(), nullable=True),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tool_id'], ['mcp_tools.id']),
        sa.ForeignKeyConstraint(['executed_by'], ['users.id']),
    )
    
    # 创建系统相关表
    op.create_table(
        'system_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(200), nullable=False, unique=True, index=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(50), nullable=False, server_default='string'),
        sa.Column('category', postgresql.ENUM('system', 'feature', 'integration', 'security', 'performance', name='configcategory', create_type=False), nullable=False, server_default='system'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('action', postgresql.ENUM('create', 'read', 'update', 'delete', 'execute', 'login', 'logout', 'permission_denied', name='auditaction', create_type=False), nullable=False, index=True),
        sa.Column('resource_type', sa.String(100), nullable=True, index=True),
        sa.Column('resource_id', sa.String(200), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('request_path', sa.String(500), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('result', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    
    # 创建索引
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_audit_logs_timestamp', 'audit_logs')
    op.drop_index('idx_audit_logs_resource', 'audit_logs')
    op.drop_index('idx_audit_logs_user_action', 'audit_logs')
    
    # 删除表（按相反顺序）
    op.drop_table('audit_logs')
    op.drop_table('system_configs')
    op.drop_table('mcp_tool_executions')
    op.drop_table('mcp_tools')
    op.drop_table('knowledge_graph_edges')
    op.drop_table('knowledge_graph_nodes')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('workflow_executions')
    op.drop_table('workflow_connections')
    op.drop_table('workflow_nodes')
    op.drop_table('workflow_definitions')
    op.drop_table('user_sessions')
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS auditaction')
    op.execute('DROP TYPE IF EXISTS configcategory')
    op.execute('DROP TYPE IF EXISTS documentstatus')
    op.execute('DROP TYPE IF EXISTS documenttype')
    op.execute('DROP TYPE IF EXISTS executionstatus')
    op.execute('DROP TYPE IF EXISTS nodetype')
    op.execute('DROP TYPE IF EXISTS workflowstatus')
    op.execute('DROP TYPE IF EXISTS userstatus')









