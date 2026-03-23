"""
测试项目管理服务功能
测试数据来源：2025项目周月进度报告 (1).xlsx
"""
import requests
import json
import os
from pathlib import Path

# 服务地址
BASE_URL = "http://localhost:8016/api"

def test_health_check():
    """测试健康检查"""
    print("\n" + "="*60)
    print("1. 测试健康检查接口")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✅ 健康检查成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        return False

def test_list_projects():
    """测试获取项目列表"""
    print("\n" + "="*60)
    print("2. 测试获取项目列表")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/v1/projects", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ 获取项目列表成功")
        print(f"   总项目数: {data.get('total', 0)}")
        print(f"   返回项目数: {len(data.get('items', []))}")
        
        if data.get('items'):
            print("\n   前5个项目:")
            for i, project in enumerate(data['items'][:5], 1):
                print(f"   {i}. {project.get('name')} ({project.get('project_code')}) - {project.get('status')}")
        
        return data
    except Exception as e:
        print(f"❌ 获取项目列表失败: {str(e)}")
        return None

def test_get_project_detail(project_id):
    """测试获取项目详情"""
    print("\n" + "="*60)
    print(f"3. 测试获取项目详情 (ID: {project_id})")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/v1/projects/{project_id}", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ 获取项目详情成功")
        print(f"   项目名称: {data.get('name')}")
        print(f"   项目编码: {data.get('project_code')}")
        print(f"   状态: {data.get('status')}")
        print(f"   进度: {data.get('progress_percent', 0)}%")
        print(f"   健康评分: {data.get('health_score', 0)}")
        return data
    except Exception as e:
        print(f"❌ 获取项目详情失败: {str(e)}")
        return None

def test_import_excel():
    """测试Excel导入功能"""
    print("\n" + "="*60)
    print("4. 测试Excel导入功能")
    print("="*60)
    
    excel_file = Path("2025项目周月进度报告 (1).xlsx")
    if not excel_file.exists():
        print(f"❌ Excel文件不存在: {excel_file}")
        return None
    
    try:
        print(f"   正在上传文件: {excel_file}")
        with open(excel_file, 'rb') as f:
            files = {'file': (excel_file.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(
                f"{BASE_URL}/v1/projects/import/excel",
                files=files,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ Excel导入成功")
            print(f"   发现项目数: {data.get('total_found', 0)}")
            print(f"   成功创建: {data.get('created', 0)}")
            
            if data.get('projects'):
                print(f"\n   创建的项目列表:")
                for i, project in enumerate(data['projects'], 1):
                    print(f"   {i}. {project.get('name')} ({project.get('project_code')})")
            
            return data
    except Exception as e:
        print(f"❌ Excel导入失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"   错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   错误响应: {e.response.text}")
        return None

def test_list_tasks():
    """测试获取任务列表"""
    print("\n" + "="*60)
    print("5. 测试获取任务列表")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/v1/tasks", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ 获取任务列表成功")
        print(f"   总任务数: {data.get('total', 0)}")
        print(f"   返回任务数: {len(data.get('items', []))}")
        return data
    except Exception as e:
        print(f"❌ 获取任务列表失败: {str(e)}")
        return None

def test_list_reports():
    """测试获取周报列表"""
    print("\n" + "="*60)
    print("6. 测试获取周报列表")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/v1/reports", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ 获取周报列表成功")
        print(f"   总周报数: {data.get('total', 0)}")
        print(f"   返回周报数: {len(data.get('items', []))}")
        return data
    except Exception as e:
        print(f"❌ 获取周报列表失败: {str(e)}")
        return None

def check_data_completeness(projects_data):
    """检查数据完整性"""
    print("\n" + "="*60)
    print("7. 检查数据完整性")
    print("="*60)
    
    if not projects_data or not projects_data.get('items'):
        print("❌ 没有项目数据，无法检查完整性")
        return
    
    projects = projects_data['items']
    total = len(projects)
    
    # 统计字段完整性
    stats = {
        '有项目编码': 0,
        '有项目名称': 0,
        '有状态': 0,
        '有进度': 0,
        '有创建时间': 0
    }
    
    for project in projects:
        if project.get('project_code'):
            stats['有项目编码'] += 1
        if project.get('name'):
            stats['有项目名称'] += 1
        if project.get('status'):
            stats['有状态'] += 1
        if project.get('progress_percent') is not None:
            stats['有进度'] += 1
        if project.get('created_at'):
            stats['有创建时间'] += 1
    
    print(f"\n   数据完整性统计 (共 {total} 个项目):")
    for field, count in stats.items():
        percentage = (count / total * 100) if total > 0 else 0
        status = "✅" if count == total else "⚠️"
        print(f"   {status} {field}: {count}/{total} ({percentage:.1f}%)")
    
    # 检查状态分布
    status_dist = {}
    for project in projects:
        status = project.get('status', 'unknown')
        status_dist[status] = status_dist.get(status, 0) + 1
    
    print(f"\n   项目状态分布:")
    for status, count in sorted(status_dist.items()):
        print(f"      {status}: {count}")

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("项目管理服务功能测试")
    print("="*60)
    print(f"服务地址: {BASE_URL}")
    
    # 1. 健康检查
    if not test_health_check():
        print("\n❌ 服务不可用，停止测试")
        return
    
    # 2. 获取当前项目列表（导入前）
    print("\n" + "-"*60)
    print("导入前的项目列表:")
    projects_before = test_list_projects()
    before_count = projects_before.get('total', 0) if projects_before else 0
    
    # 3. 测试Excel导入
    import_result = test_import_excel()
    
    # 4. 获取导入后的项目列表
    print("\n" + "-"*60)
    print("导入后的项目列表:")
    projects_after = test_list_projects()
    after_count = projects_after.get('total', 0) if projects_after else 0
    
    # 5. 如果有新项目，查看详情
    if projects_after and projects_after.get('items'):
        first_project = projects_after['items'][0]
        test_get_project_detail(first_project.get('id'))
    
    # 6. 测试任务列表
    test_list_tasks()
    
    # 7. 测试周报列表
    test_list_reports()
    
    # 8. 检查数据完整性
    if projects_after:
        check_data_completeness(projects_after)
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"导入前项目数: {before_count}")
    print(f"导入后项目数: {after_count}")
    print(f"新增项目数: {after_count - before_count}")
    
    if import_result:
        print(f"Excel解析发现: {import_result.get('total_found', 0)} 个项目")
        print(f"成功创建: {import_result.get('created', 0)} 个项目")
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main()

