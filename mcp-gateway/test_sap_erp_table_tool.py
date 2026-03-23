"""
测试SAP ERP表查询工具
测试查询BKPF表（会计凭证表）
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.sap_erp_table_tool import execute_query_sap_table

# 设置SAP连接参数
os.environ['SAP_USER'] = 'admin'
os.environ['SAP_PASSWORD'] = 'ad@kf29!()G'
os.environ['SAP_HOST'] = '10.24.49.128'
os.environ['SAP_SYSNR'] = '00'
os.environ['SAP_CLIENT'] = '100'


async def test_query_bkpf():
    """测试查询BKPF表"""
    print("=" * 80)
    print("测试SAP ERP表查询工具 - 查询BKPF表")
    print("=" * 80)
    print(f"\nSAP连接信息:")
    print(f"  主机: {os.getenv('SAP_HOST', '10.24.49.128')}")
    print(f"  客户端: {os.getenv('SAP_CLIENT', '100')}")
    print(f"  用户: {os.getenv('SAP_USER', 'admin')}")
    print("=" * 80)
    
    # 测试1：查询BKPF表的前10条记录（指定字段）
    print("\n测试1：查询BKPF表的前10条记录（指定字段）")
    print("-" * 80)
    
    parameters = {
        "table_name": "BKPF",
        "fields": ["BELNR", "GJAHR", "BUKRS", "BLART", "BUDAT", "USNAM"],
        "max_rows": 10
    }
    
    try:
        result = await execute_query_sap_table(parameters)
        
        if result.get("success"):
            print(f"✅ 查询成功")
            print(f"   表名: {result.get('table_name')}")
            print(f"   返回行数: {result.get('row_count')}")
            print(f"   字段: {', '.join(result.get('fields', []))}")
            print(f"\n   数据（前5条）:")
            for i, row in enumerate(result.get('data', [])[:5], 1):
                print(f"   {i}. {row}")
        else:
            print(f"❌ 查询失败: {result.get('error')}")
            print(f"   错误代码: {result.get('error_code')}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2：查询BKPF表（带WHERE条件）
    print("\n\n测试2：查询BKPF表（带WHERE条件）")
    print("-" * 80)
    
    parameters2 = {
        "table_name": "BKPF",
        "fields": ["BELNR", "GJAHR", "BUKRS", "BLART", "BUDAT"],
        "where_clause": "BUKRS = '1000'",
        "max_rows": 5
    }
    
    try:
        result2 = await execute_query_sap_table(parameters2)
        
        if result2.get("success"):
            print(f"✅ 查询成功")
            print(f"   表名: {result2.get('table_name')}")
            print(f"   返回行数: {result2.get('row_count')}")
            print(f"   WHERE条件: {parameters2.get('where_clause')}")
            print(f"\n   数据:")
            for i, row in enumerate(result2.get('data', []), 1):
                print(f"   {i}. {row}")
        else:
            print(f"❌ 查询失败: {result2.get('error')}")
            print(f"   错误代码: {result2.get('error_code')}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试3：查询BKPF表（所有字段）
    print("\n\n测试3：查询BKPF表（所有字段，前3条）")
    print("-" * 80)
    
    parameters3 = {
        "table_name": "BKPF",
        "max_rows": 3
    }
    
    try:
        result3 = await execute_query_sap_table(parameters3)
        
        if result3.get("success"):
            print(f"✅ 查询成功")
            print(f"   表名: {result3.get('table_name')}")
            print(f"   返回行数: {result3.get('row_count')}")
            print(f"   字段数: {len(result3.get('fields', []))}")
            print(f"   字段列表: {', '.join(result3.get('fields', [])[:10])}...")
            print(f"\n   数据（第1条，部分字段）:")
            if result3.get('data'):
                first_row = result3.get('data')[0]
                for key, value in list(first_row.items())[:10]:
                    print(f"      {key}: {value}")
        else:
            print(f"❌ 查询失败: {result3.get('error')}")
            print(f"   错误代码: {result3.get('error_code')}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_query_bkpf())

