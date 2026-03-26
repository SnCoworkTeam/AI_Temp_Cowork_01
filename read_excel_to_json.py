#!/usr/bin/env python3
"""
读取Excel文件并生成JSON文件
"""
import pandas as pd
import json
import sys

EXCEL_FILE = "中化国际数字化部员工统计_20251204.xlsx"
OUTPUT_FILE = "users_from_excel.json"

try:
    # 尝试不同的编码
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=0)
    except:
        # 如果失败，尝试指定编码
        df = pd.read_excel(EXCEL_FILE, sheet_name=0, engine='openpyxl')
    
    print(f"Total columns: {len(df.columns)}")
    print(f"Column names: {list(df.columns)}")
    print(f"First few rows:")
    print(df.head())
    
    # 识别列（尝试多种方式）
    name_col = None
    email_col = None
    
    # 方法1: 按列名匹配
    for col in df.columns:
        col_str = str(col)
        # 尝试解码
        try:
            col_str_decoded = col_str.encode('latin1').decode('gbk')
        except:
            col_str_decoded = col_str
        
        if '姓名' in col_str or '姓名' in col_str_decoded or 'name' in col_str.lower():
            name_col = col
        elif '邮箱' in col_str or '邮箱' in col_str_decoded or 'email' in col_str.lower() or 'mail' in col_str.lower():
            email_col = col
    
    # 方法2: 如果没找到，尝试按位置（通常序号在第1列，姓名在第2列，邮箱在第3列）
    if not name_col or not email_col:
        print("Trying to identify columns by position...")
        if len(df.columns) >= 3:
            # 通常：第1列=序号，第2列=姓名，第3列=邮箱
            name_col = df.columns[1]  # 第2列是姓名
            email_col = df.columns[2]  # 第3列是邮箱
        elif len(df.columns) >= 2:
            # 如果只有2列，第1列可能是姓名，第2列是邮箱
            name_col = df.columns[0]
            email_col = df.columns[1]
    
    if not name_col or not email_col:
        print(f"Error: Cannot identify name or email column.")
        print(f"Available columns: {list(df.columns)}")
        print("Please check the Excel file structure")
        sys.exit(1)
    
    print(f"Using name column: {name_col}")
    print(f"Using email column: {email_col}")
    
    # 提取用户数据
    users = []
    for idx, row in df.iterrows():
        try:
            name_val = row[name_col]
            email_val = row[email_col]
            
            name = str(name_val).strip() if pd.notna(name_val) else ""
            email = str(email_val).strip() if pd.notna(email_val) else ""
            
            if not email or email == 'nan' or email.lower() == 'none':
                continue
            
            # 从邮箱提取用户名
            username = email.split('@')[0] if '@' in email else email
            
            users.append({
                'name': name,
                'email': email,
                'username': username
            })
        except Exception as e:
            print(f"Warning: Error processing row {idx}: {str(e)}")
            continue
    
    # 保存为JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    
    print(f"Success: Read {len(users)} users")
    print(f"Success: Saved to {OUTPUT_FILE}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

