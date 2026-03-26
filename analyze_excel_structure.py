#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import sys

try:
    # 读取Excel文件
    excel_file = '2025项目周月进度报告.xlsx'
    
    # 读取所有sheet
    xls = pd.ExcelFile(excel_file)
    print(f"Sheet names: {xls.sheet_names}")
    print("\n" + "="*80 + "\n")
    
    # 读取第一个sheet
    sheet_name = xls.sheet_names[0]
    print(f"Analyzing sheet: {sheet_name}\n")
    
    # 读取前几行来查看表头结构
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, nrows=10)
    
    print("First 10 rows (raw):")
    print(df.to_string())
    print("\n" + "="*80 + "\n")
    
    # 尝试读取两行表头
    df_header = pd.read_excel(excel_file, sheet_name=sheet_name, header=[0, 1], nrows=5)
    print("With two-row header:")
    print(df_header.to_string())
    print("\n" + "="*80 + "\n")
    
    # 查看列名
    print("Column names (first row):")
    df_cols = pd.read_excel(excel_file, sheet_name=sheet_name, header=0, nrows=0)
    for i, col in enumerate(df_cols.columns):
        print(f"  Column {i} ({chr(65+i) if i < 26 else chr(65+i//26-1)+chr(65+i%26)}): {col}")
    
    # 查找BL-BQ列（BL=第64列，BQ=第69列，索引从0开始是63-68）
    print("\n" + "="*80 + "\n")
    print("Columns BL-BQ (indices 63-68):")
    if len(df_cols.columns) > 68:
        for i in range(63, min(69, len(df_cols.columns))):
            col_letter = chr(65 + i // 26 - 1) + chr(65 + i % 26) if i >= 26 else chr(65 + i)
            print(f"  {col_letter} (index {i}): {df_cols.columns[i]}")
    
    # 读取完整数据（使用两行表头）
    print("\n" + "="*80 + "\n")
    print("Reading full data with two-row header...")
    df_full = pd.read_excel(excel_file, sheet_name=sheet_name, header=[0, 1])
    print(f"Shape: {df_full.shape}")
    print("\nColumn structure:")
    print(df_full.columns.tolist()[:20])  # 显示前20列
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

