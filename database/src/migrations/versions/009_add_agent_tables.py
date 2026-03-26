"""Add agent tables for intelligent agent node architecture

Revision ID: 009_add_agent_tables
Revises: 008_fix_workflow_nodes_schema
Create Date: 2024-11-14 20:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_agent_tables'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    """Add agent-related tables to the database"""

    # Create agent type enum
    agent_type_enum = postgresql.ENUM(
        'conversational',
        'tool_calling',
        'reasoning',
        'planning',
        'code_generation',
        'data_analysis',
        'document_processing',
        name='agenttype',
        create_type=False
    )
    agent_type_enum.create(op.get_bind(), checkfirst=True)

    # Create agent status enum
    agent_status_enum = postgresql.ENUM(
        'active',
        'inactive',
        'training',
        'deprecated',
        'failed',
        name='agentstatus',
        create_type=False
    )
    agent_status_enum.create(op.get_bind(), checkfirst=True)

    # Create agent execution state enum
    agent_execution_state_enum = postgresql.ENUM(
        'pending',
        'running',
        'thinking',
        'calling_tools',
        'waiting_for_input',
        'completed',
        'failed',
        'timeout',
        'cancelled',
        name='agentexecutionstate',
        create_type=False
    )
    agent_execution_state_enum.create(op.get_bind(), checkfirst=True)

    # Create conversation role enum
    conversation_role_enum = postgresql.ENUM(
        'system',
        'user',
        'assistant',
        'function',
        'tool',
        name='conversationrole',
        create_type=False
    )
    conversation_role_enum.create(op.get_bind(), checkfirst=True)

    # Create agent_registry table
    op.create_table('agent_registry',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('agent_type', agent_type_enum, nullable=False),
        sa.Column('status', agent_status_enum, nullable=False, default='inactive'),
        sa.Column('version', sa.String(), nullable=False, default='1.0.0'),

        # Personality
        sa.Column('personality_name', sa.String(), nullable=False),
        sa.Column('personality_description', sa.Text(), nullable=False),
        sa.Column('personality_traits', postgresql.JSONB(), nullable=False, default='[]'),
        sa.Column('communication_style', sa.String(), nullable=False, default='professional'),
        sa.Column('expertise_areas', postgresql.JSONB(), nullable=False, default='[]'),
        sa.Column('limitations', postgresql.JSONB(), nullable=False, default='[]'),

        # Capabilities (stored as JSONB array)
        sa.Column('capabilities', postgresql.JSONB(), nullable=False, default='[]'),

        # Configuration
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False, default=0.7),
        sa.Column('max_tokens', sa.Integer(), nullable=False, default=2048),
        sa.Column('top_p', sa.Float(), nullable=False, default=1.0),
        sa.Column('frequency_penalty', sa.Float(), nullable=False, default=0.0),
        sa.Column('presence_penalty', sa.Float(), nullable=False, default=0.0),
        sa.Column('timeout', sa.Integer(), nullable=False, default=300),
        sa.Column('max_tool_calls', sa.Integer(), nullable=False, default=10),
        sa.Column('enable_memory', sa.Boolean(), nullable=False, default=True),
        sa.Column('memory_size', sa.Integer(), nullable=False, default=20),

        # System prompts
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_prompt_template', sa.Text(), nullable=False, default='{input}'),

        # Tools and permissions
        sa.Column('available_tools', postgresql.JSONB(), nullable=False, default='[]'),
        sa.Column('required_permissions', postgresql.JSONB(), nullable=False, default='[]'),

        # Metadata
        sa.Column('tags', postgresql.JSONB(), nullable=False, default='[]'),
        sa.Column('category', sa.String(), nullable=False, default='general'),
        sa.Column('author', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),

        # Statistics
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('success_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('average_execution_time', sa.Float(), nullable=False, default=0.0),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_agent_registry_name')
    )

    # Create agent_nodes table
    op.create_table('agent_nodes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('node_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Node configuration
        sa.Column('position', postgresql.JSONB(), nullable=True),
        sa.Column('size', postgresql.JSONB(), nullable=True),
        sa.Column('style', postgresql.JSONB(), nullable=True),

        # Input/Output mapping
        sa.Column('input_mapping', postgresql.JSONB(), nullable=False, default='{}'),
        sa.Column('output_mapping', postgresql.JSONB(), nullable=False, default='{}'),

        # Execution configuration
        sa.Column('retry_count', sa.Integer(), nullable=False, default=3),
        sa.Column('retry_delay', sa.Integer(), nullable=False, default=5),
        sa.Column('enable_streaming', sa.Boolean(), nullable=False, default=False),

        # Context management
        sa.Column('context_window_size', sa.Integer(), nullable=False, default=10),
        sa.Column('preserve_conversation', sa.Boolean(), nullable=False, default=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ),
        sa.ForeignKeyConstraint(['agent_id'], ['agent_registry.id'], )
    )

    # Create agent_contexts table
    op.create_table('agent_contexts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('node_id', sa.String(), nullable=False),

        # Context state
        sa.Column('current_state', agent_execution_state_enum, nullable=False, default='pending'),
        sa.Column('variables', postgresql.JSONB(), nullable=False, default='{}'),
        sa.Column('shared_memory', postgresql.JSONB(), nullable=False, default='{}'),

        # Execution information
        sa.Column('execution_count', sa.Integer(), nullable=False, default=0),
        sa.Column('total_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('total_execution_time', sa.Float(), nullable=False, default=0.0),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agent_registry.id'], ),
        sa.ForeignKeyConstraint(['node_id'], ['agent_nodes.id'], ),
        sa.UniqueConstraint('conversation_id', 'agent_id', 'node_id', name='uq_agent_context')
    )

    # Create conversation_messages table
    op.create_table('conversation_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('role', conversation_role_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_calls', postgresql.JSONB(), nullable=False, default='[]'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, default='{}'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_conversation_messages_conversation_id', 'conversation_id'),
        sa.Index('idx_conversation_messages_timestamp', 'timestamp')
    )

    # Create agent_execution_records table
    op.create_table('agent_execution_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('node_id', sa.String(), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', sa.String(), nullable=False),

        # Input/Output data (stored as JSONB)
        sa.Column('input_data', postgresql.JSONB(), nullable=False),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),

        # Execution status
        sa.Column('state', agent_execution_state_enum, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(), nullable=True),

        # Performance metrics
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('tool_calls_count', sa.Integer(), nullable=False, default=0),

        # Quality assessment
        sa.Column('success', sa.Boolean(), nullable=False, default=False),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),

        # Metadata
        sa.Column('metadata', postgresql.JSONB(), nullable=False, default='{}'),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agent_registry.id'], ),
        sa.ForeignKeyConstraint(['node_id'], ['agent_nodes.id'], ),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ),
        sa.Index('idx_agent_execution_records_agent_id', 'agent_id'),
        sa.Index('idx_agent_execution_records_workflow_id', 'workflow_id'),
        sa.Index('idx_agent_execution_records_start_time', 'start_time')
    )


def downgrade():
    """Remove agent-related tables and enums"""

    # Drop tables
    op.drop_table('agent_execution_records')
    op.drop_table('conversation_messages')
    op.drop_table('agent_contexts')
    op.drop_table('agent_nodes')
    op.drop_table('agent_registry')

    # Drop enums
    postgresql.ENUM(name='conversationrole').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='agentexecutionstate').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='agentstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='agenttype').drop(op.get_bind(), checkfirst=True)
