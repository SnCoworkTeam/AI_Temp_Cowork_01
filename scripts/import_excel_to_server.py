#!/usr/bin/env python3
"""
在服务器上导入Excel文件到项目管理服务
"""
import requests
import sys
import os
from pathlib import Path

excel_file = Path(__file__).parent.parent / "2025项目周月进度报告 (1).xlsx"
api_url = 'http://localhost:8016/api/v1/projects/import/excel'

if not excel_file.exists():
    print(f'Excel file not found: {excel_file}')
    # 尝试在服务器路径查找
    excel_file = Path('/opt/enterprise-ai-platform/2025项目周月进度报告 (1).xlsx')
    if not excel_file.exists():
        print(f'Excel file not found in server path either')
        sys.exit(1)

print(f'Using Excel file: {excel_file}')

try:
    with open(excel_file, 'rb') as f:
        files = {
            'file': (
                excel_file.name, 
                f, 
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        }
        print(f'Uploading to {api_url}...')
        response = requests.post(api_url, files=files, timeout=120)
        
    if response.status_code == 200:
        data = response.json()
        print('✅ Excel import successful')
        print(f'   Total found: {data.get("total_found", 0)}')
        print(f'   Created: {data.get("created", 0)}')
        if data.get('projects'):
            print(f'   Created projects:')
            for p in data['projects']:
                print(f'     - {p.get("name")} ({p.get("project_code")})')
    else:
        print(f'❌ Excel import failed: {response.status_code}')
        try:
            error_data = response.json()
            print(f'   Error: {error_data}')
        except:
            print(f'   Error: {response.text}')
        sys.exit(1)
except Exception as e:
    print(f'❌ Import error: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

