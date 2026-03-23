"""
在服务器上生成项目管理测试数据
"""
import sys
import os
import uuid
from pathlib import Path
from datetime import datetime, date, timedelta
import json

sys.path.insert(0, '/opt/enterprise-ai-platform/database/src')
sys.path.insert(0, '/opt/enterprise-ai-platform/shared_libs')

import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'ai_platform'),
    'user': os.getenv('DB_USER', 'ai_user'),
    'password': os.getenv('DB_PASSWORD', 'ai_password')
}

def generate_test_data():
    """生成测试数据"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # 1. 获取所有项目
        cur.execute("SELECT id, name, project_code FROM pm_projects LIMIT 20")
        projects = cur.fetchall()
        
        if not projects:
            print("没有找到项目，请先导入项目数据")
            return
        
        print(f"找到 {len(projects)} 个项目，开始生成测试数据...")
        
        # 2. 为每个项目生成阶段
        phase_names = ['需求分析', '设计阶段', '开发阶段', '测试阶段', '上线阶段']
        phases_created = 0
        milestones_created = 0
        reports_created = 0
        risks_created = 0
        
        for project_id, project_name, project_code in projects:
            print(f"为项目 {project_name} 生成数据...")
            
            # 生成项目阶段
            for idx, phase_name in enumerate(phase_names[:3]):  # 每个项目3个阶段
                phase_id = str(uuid.uuid4())
                start_date = date.today() - timedelta(days=30 - idx * 10)
                end_date = start_date + timedelta(days=15)
                
                try:
                    cur.execute("""
                        INSERT INTO pm_project_phases 
                        (id, project_id, name, description, sequence, start_date, end_date, progress_percent, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        phase_id,
                        project_id,
                        phase_name,
                        f"{project_name}的{phase_name}",
                        idx,
                        start_date,
                        end_date,
                        min(100, (idx + 1) * 30),
                        json.dumps({}, ensure_ascii=False)
                    ))
                    phases_created += 1
                except Exception as e:
                    print(f"  创建阶段失败: {e}")
            
            # 获取第一个阶段ID用于里程碑
            cur.execute("SELECT id FROM pm_project_phases WHERE project_id = %s ORDER BY sequence LIMIT 1", (project_id,))
            first_phase = cur.fetchone()
            first_phase_id = first_phase[0] if first_phase else None
            
            # 生成里程碑
            milestone_names = ['需求确认', '设计评审', '开发完成', '测试通过', '正式上线']
            for idx, milestone_name in enumerate(milestone_names[:3]):
                milestone_id = str(uuid.uuid4())
                target_date = date.today() + timedelta(days=idx * 20)
                
                try:
                    cur.execute("""
                        INSERT INTO pm_milestones 
                        (id, project_id, phase_id, name, description, target_date, status, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        milestone_id,
                        project_id,
                        first_phase_id,
                        milestone_name,
                        f"{project_name}的{milestone_name}里程碑",
                        target_date,
                        'planned' if idx > 0 else 'in_progress',
                        json.dumps({}, ensure_ascii=False)
                    ))
                    milestones_created += 1
                except Exception as e:
                    print(f"  创建里程碑失败: {e}")
            
            # 生成周报（最近4周）
            for week_idx in range(4):
                report_id = str(uuid.uuid4())
                report_date = date.today() - timedelta(weeks=week_idx)
                week_number = report_date.isocalendar()[1]
                
                try:
                    cur.execute("""
                        INSERT INTO pm_weekly_reports 
                        (id, project_id, week_number, report_date, content_plan, content_achievement, 
                         issues_risks, next_week_plan, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        report_id,
                        project_id,
                        week_number,
                        report_date,
                        f"第{week_idx + 1}周计划：继续推进项目进度",
                        f"第{week_idx + 1}周成果：完成部分功能开发",
                        "无重大风险" if week_idx < 2 else "需要关注进度",
                        f"第{week_idx + 2}周计划：继续推进",
                        json.dumps({}, ensure_ascii=False)
                    ))
                    reports_created += 1
                except Exception as e:
                    print(f"  创建周报失败: {e}")
            
            # 生成风险（部分项目）
            if hash(str(project_id)) % 3 == 0:  # 约1/3的项目有风险
                risk_id = str(uuid.uuid4())
                risk_levels = ['low', 'medium', 'high']
                risk_level = risk_levels[abs(hash(str(project_id))) % 3]
                
                try:
                    cur.execute("""
                        INSERT INTO pm_risks 
                        (id, project_id, name, description, risk_level, status, mitigation_plan, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        risk_id,
                        project_id,
                        f"{project_name}潜在风险",
                        "项目进度可能存在延迟风险",
                        risk_level,
                        'open',
                        "加强进度跟踪，及时调整资源",
                        json.dumps({}, ensure_ascii=False)
                    ))
                    risks_created += 1
                except Exception as e:
                    print(f"  创建风险失败: {e}")
        
        conn.commit()
        
        print(f"\n✅ 测试数据生成完成:")
        print(f"  - 项目阶段: {phases_created} 个")
        print(f"  - 里程碑: {milestones_created} 个")
        print(f"  - 周报: {reports_created} 个")
        print(f"  - 风险: {risks_created} 个")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 生成测试数据失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    generate_test_data()











