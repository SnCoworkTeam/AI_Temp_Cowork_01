#!/usr/bin/env python3
"""
读取项目周月进度报告Excel文件，了解其结构
"""
import pandas as pd
import sys

EXCEL_FILE = "2025项目周月进度报告.xlsx"

try:
    # 读取Excel文件，跳过第一行，使用第二行作为表头
    df = pd.read_excel(EXCEL_FILE, sheet_name=0, header=1)
    
    print("=" * 80)
    print("Excel文件结构分析")
    print("=" * 80)
    print(f"\n总行数: {len(df)}")
    print(f"总列数: {len(df.columns)}")
    print(f"\n列名列表:")
    for idx, col in enumerate(df.columns, 1):
        print(f"  {idx}. {col}")
    
    print(f"\n前5行数据:")
    print(df.head().to_string())
    
    # 查找填报人列
    reporter_col = None
    for col in df.columns:
        col_str = str(col)
        if '填报人' in col_str or '填报' in col_str or 'reporter' in col_str.lower():
            reporter_col = col
            break
    
    if reporter_col:
        print(f"\n找到填报人列: {reporter_col}")
        print(f"填报人列表（去重）:")
        reporters = df[reporter_col].dropna().unique()
        for reporter in reporters[:20]:  # 只显示前20个
            print(f"  - {reporter}")
        print(f"  共 {len(reporters)} 个不同的填报人")
    else:
        print("\n未找到填报人列")
    
    # 查找项目名称列
    project_name_col = None
    for col in df.columns:
        col_str = str(col)
        if '项目名称' in col_str or '项目' in col_str or 'project' in col_str.lower() or 'name' in col_str.lower():
            project_name_col = col
            break
    
    if project_name_col:
        print(f"\n找到项目名称列: {project_name_col}")
        print(f"项目数量: {df[project_name_col].nunique()}")
    
    # 查找可能的分类列
    print(f"\n可能的分类列:")
    category_keywords = ['分类', '类型', '行业', '领域', 'category', 'type', 'industry', 'domain']
    for col in df.columns:
        col_str = str(col)
        for keyword in category_keywords:
            if keyword in col_str:
                print(f"  - {col}")
                # 显示该列的唯一值
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 20:
                    print(f"    值: {', '.join(map(str, unique_vals))}")
                else:
                    print(f"    值数量: {len(unique_vals)}")
                break
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

