"""
修复 workflow_executions 表的 schema，添加缺失的列并处理列名映射

Revision ID: 013
Revises: 012
Create Date: 2025-11-19

问题: workflow_executions 表缺少 progress, current_node_id, node_results, 
     start_time, end_time, execution_time, execution_metadata 列
影响: 工作流执行时出现 UndefinedColumn 错误
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '013'
down_revision = '012'  # 使用完整的revision ID
branch_labels = None
depends_on = None


def upgrade():
    """添加缺失的列到 workflow_executions 表"""
    print("=" * 50)
    print("修复 workflow_executions 表 schema")
    print("=" * 50)
    
    conn = op.get_bind()
    
    # 1. 添加 progress 列
    print("检查 progress 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name = 'progress'
    """))
    
    if not result.fetchone():
        print("添加 progress 列...")
        op.add_column(
            'workflow_executions',
            sa.Column(
                'progress',
                sa.Float(),
                nullable=False,
                server_default='0.0',
                comment='执行进度（0-1）'
            )
        )
        print("✅ progress 列已添加")
    else:
        print("⚠️  progress 列已存在，跳过")
    
    # 2. 添加 current_node_id 列
    print("检查 current_node_id 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name = 'current_node_id'
    """))
    
    if not result.fetchone():
        print("添加 current_node_id 列...")
        op.add_column(
            'workflow_executions',
            sa.Column(
                'current_node_id',
                sa.String(100),
                nullable=True,
                comment='当前节点ID'
            )
        )
        print("✅ current_node_id 列已添加")
    else:
        print("⚠️  current_node_id 列已存在，跳过")
    
    # 3. 添加 node_results 列（如果 execution_log 存在，可以保留两者）
    print("检查 node_results 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name = 'node_results'
    """))
    
    if not result.fetchone():
        print("添加 node_results 列...")
        op.add_column(
            'workflow_executions',
            sa.Column(
                'node_results',
                postgresql.JSONB(),
                nullable=True,
                comment='节点执行结果'
            )
        )
        print("✅ node_results 列已添加")
    else:
        print("⚠️  node_results 列已存在，跳过")
    
    # 4. 添加 start_time 列（如果 started_at 存在，添加别名列）
    print("检查 start_time 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name = 'start_time'
    """))
    
    if not result.fetchone():
        # 检查 started_at 是否存在
        result2 = conn.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_executions' 
            AND column_name = 'started_at'
        """))
        
        if result2.fetchone():
            # 如果 started_at 存在，创建视图或添加别名列
            # 为了简单，我们添加一个新列，并在后续同步数据
            print("添加 start_time 列（started_at 已存在，将同步数据）...")
            op.add_column(
                'workflow_executions',
                sa.Column(
                    'start_time',
                    sa.DateTime(),
                    nullable=True,
                    comment='开始时间'
                )
            )
            # 同步数据
            conn.execute(sa.text("""
                UPDATE workflow_executions 
                SET start_time = started_at 
                WHERE started_at IS NOT NULL AND start_time IS NULL
            """))
            print("✅ start_time 列已添加并同步数据")
        else:
            # 如果 started_at 不存在，直接添加 start_time
            op.add_column(
                'workflow_executions',
                sa.Column(
                    'start_time',
                    sa.DateTime(),
                    nullable=True,
                    comment='开始时间'
                )
            )
            print("✅ start_time 列已添加")
    else:
        print("⚠️  start_time 列已存在，跳过")
    
    # 5. 添加 end_time 列（如果 finished_at 存在，添加别名列）
    print("检查 end_time 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name = 'end_time'
    """))
    
    if not result.fetchone():
        # 检查 finished_at 是否存在
        result2 = conn.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_executions' 
            AND column_name = 'finished_at'
        """))
        
        if result2.fetchone():
            print("添加 end_time 列（finished_at 已存在，将同步数据）...")
            op.add_column(
                'workflow_executions',
                sa.Column(
                    'end_time',
                    sa.DateTime(),
                    nullable=True,
                    comment='结束时间'
                )
            )
            # 同步数据
            conn.execute(sa.text("""
                UPDATE workflow_executions 
                SET end_time = finished_at 
                WHERE finished_at IS NOT NULL AND end_time IS NULL
            """))
            print("✅ end_time 列已添加并同步数据")
        else:
            op.add_column(
                'workflow_executions',
                sa.Column(
                    'end_time',
                    sa.DateTime(),
                    nullable=True,
                    comment='结束时间'
                )
            )
            print("✅ end_time 列已添加")
    else:
        print("⚠️  end_time 列已存在，跳过")
    
    # 6. 添加 execution_time 列（如果 duration_seconds 存在，添加别名列）
    print("检查 execution_time 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name = 'execution_time'
    """))
    
    if not result.fetchone():
        # 检查 duration_seconds 是否存在
        result2 = conn.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_executions' 
            AND column_name = 'duration_seconds'
        """))
        
        if result2.fetchone():
            print("添加 execution_time 列（duration_seconds 已存在，将同步数据）...")
            op.add_column(
                'workflow_executions',
                sa.Column(
                    'execution_time',
                    sa.Float(),
                    nullable=True,
                    comment='执行耗时（秒）'
                )
            )
            # 同步数据
            conn.execute(sa.text("""
                UPDATE workflow_executions 
                SET execution_time = duration_seconds 
                WHERE duration_seconds IS NOT NULL AND execution_time IS NULL
            """))
            print("✅ execution_time 列已添加并同步数据")
        else:
            op.add_column(
                'workflow_executions',
                sa.Column(
                    'execution_time',
                    sa.Float(),
                    nullable=True,
                    comment='执行耗时（秒）'
                )
            )
            print("✅ execution_time 列已添加")
    else:
        print("⚠️  execution_time 列已存在，跳过")
    
    # 7. 添加 execution_metadata 列
    print("检查 execution_metadata 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name = 'execution_metadata'
    """))
    
    if not result.fetchone():
        print("添加 execution_metadata 列...")
        op.add_column(
            'workflow_executions',
            sa.Column(
                'execution_metadata',
                postgresql.JSONB(),
                nullable=True,
                server_default='{}',
                comment='执行元数据'
            )
        )
        print("✅ execution_metadata 列已添加")
    else:
        print("⚠️  execution_metadata 列已存在，跳过")
    
    print("=" * 50)
    print("✅ workflow_executions 表 schema 修复完成")
    print("=" * 50)


def downgrade():
    """移除添加的列"""
    print("移除 workflow_executions 表的列...")
    
    conn = op.get_bind()
    
    # 移除列（按相反顺序）
    columns_to_remove = [
        'execution_metadata',
        'execution_time',
        'end_time',
        'start_time',
        'node_results',
        'current_node_id',
        'progress'
    ]
    
    for column_name in columns_to_remove:
        result = conn.execute(sa.text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'workflow_executions' 
            AND column_name = '{column_name}'
        """))
        
        if result.fetchone():
            print(f"移除 {column_name} 列...")
            op.drop_column('workflow_executions', column_name)
            print(f"✅ {column_name} 列已移除")
        else:
            print(f"⚠️  {column_name} 列不存在，跳过")
    
    print("✅ 所有列已移除")

