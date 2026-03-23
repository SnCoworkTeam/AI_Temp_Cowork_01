#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从Excel文件批量创建用户账号
"""
import pandas as pd
import requests
import sys
import os
from urllib.parse import urlparse

# 配置
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://43.143.139.197:8080")
EXCEL_FILE = "中化国际数字化部员工统计_20251204.xlsx"
DEFAULT_PASSWORD = "Sinochem@2025"  # 默认密码，首次登录后需要修改

def extract_username_from_email(email):
    """从邮箱提取用户名（邮箱前缀）"""
    if pd.isna(email) or not email:
        return None
    email_str = str(email).strip()
    if '@' in email_str:
        return email_str.split('@')[0]
    return email_str

def create_user(name, email, username, password, api_url):
    """创建用户"""
    url = f"{api_url}/api/auth/register"
    
    data = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": name
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ 创建成功: {name} ({username}) - {email}")
            return True
        else:
            print(f"❌ 创建失败: {name} ({username}) - {email}")
            print(f"   错误: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 创建失败: {name} ({username}) - {email}")
        print(f"   异常: {str(e)}")
        return False

def main():
    try:
        # 读取Excel文件
        print("="*80)
        print("读取Excel文件...")
        print("="*80)
        
        df = pd.read_excel(EXCEL_FILE, sheet_name=0)
        
        print(f"共 {len(df)} 条记录")
        print(f"列名: {list(df.columns)}")
        print()
        
        # 识别列（根据实际列名调整）
        # 假设列名是：序号、姓名、邮箱
        name_col = None
        email_col = None
        
        for col in df.columns:
            col_str = str(col)
            if '姓名' in col_str or 'name' in col_str.lower():
                name_col = col
            elif '邮箱' in col_str or 'email' in col_str.lower() or 'mail' in col_str.lower():
                email_col = col
        
        if not name_col or not email_col:
            print("❌ 无法识别姓名或邮箱列")
            print(f"可用列: {list(df.columns)}")
            return
        
        print(f"姓名列: {name_col}")
        print(f"邮箱列: {email_col}")
        print()
        
        # 创建用户
        print("="*80)
        print("开始创建用户...")
        print("="*80)
        
        success_count = 0
        fail_count = 0
        
        for idx, row in df.iterrows():
            name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
            email = str(row[email_col]).strip() if pd.notna(row[email_col]) else ""
            
            if not email:
                print(f"⚠️  跳过: 第{idx+1}行，邮箱为空")
                fail_count += 1
                continue
            
            username = extract_username_from_email(email)
            if not username:
                print(f"⚠️  跳过: 第{idx+1}行，无法提取用户名 - {email}")
                fail_count += 1
                continue
            
            if create_user(name, email, username, DEFAULT_PASSWORD, API_GATEWAY_URL):
                success_count += 1
            else:
                fail_count += 1
        
        print()
        print("="*80)
        print("创建完成")
        print("="*80)
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失败: {fail_count}")
        print(f"📊 总计: {success_count + fail_count}")
        print()
        print(f"默认密码: {DEFAULT_PASSWORD}")
        print("提示: 用户首次登录后应修改密码")
        
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

