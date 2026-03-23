#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import sys

try:
    excel_file = '2025项目周月进度报告.xlsx'
    
    # 读取第一个sheet，使用两行表头
    sheet_name = pd.ExcelFile(excel_file).sheet_names[0]
    print(f"Sheet: {sheet_name}\n")
    
    # 读取前3行查看原始结构
    df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, nrows=3)
    print("="*80)
    print("Raw first 3 rows:")
    print("="*80)
    for i in range(min(3, len(df_raw))):
        print(f"\nRow {i}:")
        for j in range(min(70, len(df_raw.columns))):
            val = df_raw.iloc[i, j]
            if pd.notna(val):
                col_letter = chr(65 + j // 26 - 1) + chr(65 + j % 26) if j >= 26 else chr(65 + j)
                print(f"  {col_letter}{j}: {str(val)[:50]}")
    
    # 读取两行表头
    print("\n" + "="*80)
    print("Two-row header structure:")
    print("="*80)
    df_header = pd.read_excel(excel_file, sheet_name=sheet_name, header=[0, 1], nrows=0)
    
    # 显示所有列
    print(f"\nTotal columns: {len(df_header.columns)}")
    print("\nColumn structure (first 70 columns):")
    for i, col in enumerate(df_header.columns[:70]):
        col_letter = chr(65 + i // 26 - 1) + chr(65 + i % 26) if i >= 26 else chr(65 + i)
        level0 = str(col[0]) if isinstance(col, tuple) else str(col)
        level1 = str(col[1]) if isinstance(col, tuple) and len(col) > 1 else ""
        print(f"  {col_letter} ({i}): Level0='{level0[:30]}', Level1='{level1[:30]}'")
    
    # 特别关注BL-BQ列（索引63-68）
    print("\n" + "="*80)
    print("BL-BQ columns (indices 63-68):")
    print("="*80)
    if len(df_header.columns) > 68:
        for i in range(63, min(69, len(df_header.columns))):
            col_letter = chr(65 + i // 26 - 1) + chr(65 + i % 26) if i >= 26 else chr(65 + i)
            col = df_header.columns[i]
            level0 = str(col[0]) if isinstance(col, tuple) else str(col)
            level1 = str(col[1]) if isinstance(col, tuple) and len(col) > 1 else ""
            print(f"  {col_letter} ({i}):")
            print(f"    Level0: {level0}")
            print(f"    Level1: {level1}")
    
    # 读取完整数据查看实际内容
    print("\n" + "="*80)
    print("Sample data rows (first 3 rows):")
    print("="*80)
    df_full = pd.read_excel(excel_file, sheet_name=sheet_name, header=[0, 1], nrows=3)
    print(f"Shape: {df_full.shape}")
    
    # 查看BL-BQ列的数据
    if len(df_full.columns) > 68:
        print("\nBL-BQ column data (first row):")
        for i in range(63, min(69, len(df_full.columns))):
            col_letter = chr(65 + i // 26 - 1) + chr(65 + i % 26) if i >= 26 else chr(65 + i)
            val = df_full.iloc[0, i] if len(df_full) > 0 else None
            print(f"  {col_letter}: {val}")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

