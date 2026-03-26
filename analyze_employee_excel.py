#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import sys

try:
    excel_file = '中化国际数字化部员工统计_20251204.xlsx'
    
    # 读取所有sheet
    xls = pd.ExcelFile(excel_file)
    print(f"Sheet names: {xls.sheet_names}")
    print("\n" + "="*80 + "\n")
    
    # 读取第一个sheet
    sheet_name = xls.sheet_names[0]
    print(f"Analyzing sheet: {sheet_name}\n")
    
    # 读取数据
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print("\n" + "="*80 + "\n")
    
    # 显示前几行
    print("First 5 rows:")
    print(df.head(5).to_string())
    print("\n" + "="*80 + "\n")
    
    # 检查是否有邮箱列
    email_cols = [col for col in df.columns if '邮箱' in str(col) or 'email' in str(col).lower() or 'mail' in str(col).lower()]
    print(f"Email columns found: {email_cols}")
    
    # 检查是否有姓名列
    name_cols = [col for col in df.columns if '姓名' in str(col) or 'name' in str(col).lower()]
    print(f"Name columns found: {name_cols}")
    
    # 检查是否有部门列
    dept_cols = [col for col in df.columns if '部门' in str(col) or 'department' in str(col).lower()]
    print(f"Department columns found: {dept_cols}")
    
    # 显示所有列名
    print("\nAll columns:")
    for i, col in enumerate(df.columns):
        print(f"  {i}: {col}")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

