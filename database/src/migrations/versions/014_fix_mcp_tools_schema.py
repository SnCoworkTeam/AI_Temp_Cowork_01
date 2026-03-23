"""
修复 mcp_tools 表的 schema，添加缺失的列

Revision ID: 014
Revises: 013
Create Date: 2025-11-21

问题: mcp_tools 表缺少 version, required_parameters, return_type, config, 
     tool_metadata, call_count, success_count, failure_count, avg_execution_time 列
影响: 工具执行时出现 UndefinedColumn 错误
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    """添加缺失的列到 mcp_tools 表"""
    print("=" * 50)
    print("修复 mcp_tools 表 schema")
    print("=" * 50)
    
    conn = op.get_bind()
    
    # 1. 添加 version 列
    print("检查 version 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'mcp_tools' 
        AND column_name = 'version'
    """))
    
    if not result.fetchone():
        print("添加 version 列...")
        op.add_column(
            'mcp_tools',
            sa.Column(
                'version',
                sa.String(50),
                nullable=False,
                server_default='1.0.0',
                comment='版本号'
            )
        )
        print("✅ version 列已添加")
    else:
        print("⚠️  version 列已存在，跳过")
    
    # 2. 添加 required_parameters 列
    print("检查 required_parameters 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'mcp_tools' 
        AND column_name = 'required_parameters'
    """))
    
    if not result.fetchone():
        print("添加 required_parameters 列...")
        op.add_column(
            'mcp_tools',
            sa.Column(
                'required_parameters',
                postgresql.JSONB(),
                nullable=True,
                server_default='[]',
                comment='必需参数列表'
            )
        )
        print("✅ required_parameters 列已添加")
    else:
        print("⚠️  required_parameters 列已存在，跳过")
    
    # 3. 添加 return_type 列
    print("检查 return_type 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'mcp_tools' 
        AND column_name = 'return_type'
    """))
    
    if not result.fetchone():
        print("添加 return_type 列...")
        op.add_column(
            'mcp_tools',
            sa.Column(
                'return_type',
                sa.String(100),
                nullable=True,
                comment='返回类型'
            )
        )
        print("✅ return_type 列已添加")
    else:
        print("⚠️  return_type 列已存在，跳过")
    
    # 4. 添加 config 列
    print("检查 config 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'mcp_tools' 
        AND column_name = 'config'
    """))
    
    if not result.fetchone():
        print("添加 config 列...")
        op.add_column(
            'mcp_tools',
            sa.Column(
                'config',
                postgresql.JSONB(),
                nullable=True,
                server_default='{}',
                comment='工具配置'
            )
        )
        print("✅ config 列已添加")
    else:
        print("⚠️  config 列已存在，跳过")
    
    # 5. 添加 tool_metadata 列（如果metadata列存在，可能需要重命名或合并）
    print("检查 tool_metadata 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'mcp_tools' 
        AND column_name = 'tool_metadata'
    """))
    
    if not result.fetchone():
        print("添加 tool_metadata 列...")
        op.add_column(
            'mcp_tools',
            sa.Column(
                'tool_metadata',
                postgresql.JSONB(),
                nullable=True,
                server_default='{}',
                comment='元数据'
            )
        )
        print("✅ tool_metadata 列已添加")
    else:
        print("⚠️  tool_metadata 列已存在，跳过")
    
    # 6. 添加统计字段
    for col_name, col_type, default_val in [
        ('call_count', sa.Integer(), 0),
        ('success_count', sa.Integer(), 0),
        ('failure_count', sa.Integer(), 0),
        ('avg_execution_time', sa.Float(), None),
    ]:
        print(f"检查 {col_name} 列...")
        result = conn.execute(sa.text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'mcp_tools' 
            AND column_name = '{col_name}'
        """))
        
        if not result.fetchone():
            print(f"添加 {col_name} 列...")
            col = sa.Column(
                col_name,
                col_type,
                nullable=(default_val is not None),
                server_default=str(default_val) if default_val is not None else None,
                comment=f'{col_name.replace("_", " ").title()}'
            )
            op.add_column('mcp_tools', col)
            print(f"✅ {col_name} 列已添加")
        else:
            print(f"⚠️  {col_name} 列已存在，跳过")
    
    # 7. 重命名 parameters_schema 为 parameters（如果存在）
    print("检查 parameters 列...")
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'mcp_tools' 
        AND column_name = 'parameters'
    """))
    
    if not result.fetchone():
        # 检查是否有 parameters_schema 列
        result2 = conn.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'mcp_tools' 
            AND column_name = 'parameters_schema'
        """))
        
        if result2.fetchone():
            print("重命名 parameters_schema 为 parameters...")
            op.alter_column('mcp_tools', 'parameters_schema', new_column_name='parameters')
            print("✅ parameters_schema 已重命名为 parameters")
        else:
            print("添加 parameters 列...")
            op.add_column(
                'mcp_tools',
                sa.Column(
                    'parameters',
                    postgresql.JSONB(),
                    nullable=True,
                    comment='参数定义（JSON Schema）'
                )
            )
            print("✅ parameters 列已添加")
    else:
        print("⚠️  parameters 列已存在，跳过")
    
    print("\n✅ mcp_tools 表结构修复完成")


def downgrade():
    """回滚列添加"""
    # 删除添加的列
    op.drop_column('mcp_tools', 'version')
    op.drop_column('mcp_tools', 'required_parameters')
    op.drop_column('mcp_tools', 'return_type')
    op.drop_column('mcp_tools', 'config')
    op.drop_column('mcp_tools', 'tool_metadata')
    op.drop_column('mcp_tools', 'call_count')
    op.drop_column('mcp_tools', 'success_count')
    op.drop_column('mcp_tools', 'failure_count')
    op.drop_column('mcp_tools', 'avg_execution_time')
    
    # 如果重命名了，恢复原名
    try:
        op.alter_column('mcp_tools', 'parameters', new_column_name='parameters_schema')
    except:
        pass
































