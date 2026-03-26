"""
从Excel文件导入基础数据到数据库
Excel文件中的"基础数据"sheet页，每一列就是一个基础数据分类
列名就是category_type，列下面的内容是分类的具体内容
"""
import pandas as pd
import requests
import json
import os
import sys
from typing import Dict, List

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
API_GATEWAY_URL = os.getenv("NEXT_PUBLIC_API_GATEWAY_URL", "http://43.143.139.197:8080")
BASIC_DATA_API_URL = f"{API_GATEWAY_URL}/api/v1/basic-data/categories"
LOGIN_URL = f"{API_GATEWAY_URL}/api/auth/login"
EXCEL_FILE_PATH = "2025项目周月进度报告.xlsx"
SHEET_NAME = "基础数据"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123456"

def get_admin_token(username, password):
    """获取管理员认证token"""
    login_data = {"username": username, "password": password}
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"获取管理员token失败: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"响应状态码: {e.response.status_code}, 响应内容: {e.response.text}")
        return None

def import_basic_data_from_excel(excel_path: str, sheet_name: str, token: str):
    """
    从Excel文件导入基础数据
    
    Args:
        excel_path: Excel文件路径
        sheet_name: Sheet名称
        token: 认证token
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print(f"成功读取Excel文件: {excel_path}, Sheet: {sheet_name}")
        print(f"列数: {len(df.columns)}, 行数: {len(df)}")
        print(f"列名: {list(df.columns)}")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        total_imported = 0
        total_skipped = 0
        total_errors = 0
        
        # 遍历每一列（每一列是一个分类类型）
        for col_name in df.columns:
            if pd.isna(col_name) or str(col_name).strip() == '':
                print(f"\n跳过空列名")
                continue
            
            category_type = str(col_name).strip()
            print(f"\n处理分类类型: {category_type}")
            
            # 获取该列的所有非空值
            category_values = df[col_name].dropna().unique()
            print(f"  找到 {len(category_values)} 个唯一值")
            
            # 为每个值创建分类
            for idx, value in enumerate(category_values, start=1):
                if pd.isna(value) or str(value).strip() == '':
                    continue
                
                value_str = str(value).strip()
                
                # 尝试从值中提取编码和名称
                # 格式可能是: "01-中间体" 或 "中间体"
                code = ""
                name = value_str
                
                if '-' in value_str:
                    parts = value_str.split('-', 1)
                    if len(parts) == 2:
                        code = parts[0].strip()
                        name = parts[1].strip()
                else:
                    # 如果没有编码，使用索引作为编码
                    code = f"{idx:02d}"
                
                # 如果编码为空，使用索引
                if not code:
                    code = f"{idx:02d}"
                
                # 确保编码唯一（在同一分类类型下）
                category_code = f"{code}"
                
                category_data = {
                    "category_type": category_type,
                    "code": category_code,
                    "name": name,
                    "description": f"{category_type} - {name}",
                    "parent_id": None,
                    "sort_order": idx,
                    "is_active": True,
                    "extra_metadata": {}
                }
                
                try:
                    response = requests.post(BASIC_DATA_API_URL, headers=headers, json=category_data)
                    response.raise_for_status()
                    print(f"  ✅ 成功导入: {category_type} - {name} ({category_code})")
                    total_imported += 1
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 409:
                        print(f"  ⚠️  分类已存在，跳过: {category_type} - {name} ({category_code})")
                        total_skipped += 1
                    else:
                        print(f"  ❌ 导入失败 {category_type} - {name} ({category_code}): {e.response.status_code} - {e.response.text}")
                        total_errors += 1
                except Exception as e:
                    print(f"  ❌ 导入时发生未知错误 {category_type} - {name} ({category_code}): {e}")
                    total_errors += 1
        
        print(f"\n导入完成!")
        print(f"  成功导入: {total_imported} 条")
        print(f"  跳过（已存在）: {total_skipped} 条")
        print(f"  失败: {total_errors} 条")
        print(f"  总计: {total_imported + total_skipped + total_errors} 条")
        
        return total_imported, total_skipped, total_errors
        
    except FileNotFoundError:
        print(f"错误: 文件未找到 {excel_path}")
        return 0, 0, 0
    except Exception as e:
        print(f"读取或处理Excel文件时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0

def main():
    """主函数"""
    print("=" * 60)
    print("基础数据导入工具")
    print("=" * 60)
    
    # 获取token
    print("\n1. 获取管理员token...")
    token = get_admin_token(ADMIN_USERNAME, ADMIN_PASSWORD)
    if not token:
        print("无法获取认证token，退出。")
        return
    
    print("✅ Token获取成功")
    
    # 检查文件是否存在
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"错误: Excel文件不存在: {EXCEL_FILE_PATH}")
        return
    
    # 导入数据
    print(f"\n2. 开始导入基础数据...")
    print(f"   文件: {EXCEL_FILE_PATH}")
    print(f"   Sheet: {SHEET_NAME}")
    
    imported, skipped, errors = import_basic_data_from_excel(EXCEL_FILE_PATH, SHEET_NAME, token)
    
    print("\n" + "=" * 60)
    print("导入完成!")
    print(f"成功: {imported}, 跳过: {skipped}, 失败: {errors}")
    print("=" * 60)

if __name__ == "__main__":
    main()

