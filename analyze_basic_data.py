#!/usr/bin/env python3
"""分析Excel文件中的基础数据页签"""
import pandas as pd
import json
import sys

EXCEL_FILE = "2025项目周月进度报告.xlsx"

try:
    # 读取"基础数据"页签
    df = pd.read_excel(EXCEL_FILE, sheet_name="基础数据")
    
    print("=" * 80)
    print("基础数据页签分析")
    print("=" * 80)
    print(f"\n总行数: {len(df)}")
    print(f"总列数: {len(df.columns)}")
    print(f"\n列名:")
    for i, col in enumerate(df.columns):
        print(f"  {i+1}. {col}")
    
    print(f"\n前10行数据:")
    print(df.head(10).to_string())
    
    print(f"\n数据类型:")
    print(df.dtypes)
    
    # 分析分类数据
    print(f"\n分类数据统计:")
    for col in df.columns:
        if df[col].dtype == 'object':
            unique_count = df[col].nunique()
            print(f"  {col}: {unique_count} 个唯一值")
            if unique_count < 20:
                print(f"    值: {df[col].unique().tolist()}")
    
    # 导出为JSON
    result = {
        "columns": df.columns.tolist(),
        "total_rows": len(df),
        "sample_data": df.head(20).to_dict(orient='records'),
        "unique_values": {}
    }
    
    for col in df.columns:
        if df[col].dtype == 'object':
            unique_vals = df[col].dropna().unique().tolist()
            if len(unique_vals) < 50:
                result["unique_values"][col] = unique_vals
    
    print(f"\n\nJSON输出:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"错误: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

