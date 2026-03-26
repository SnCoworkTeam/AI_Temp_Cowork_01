#!/usr/bin/env python3
"""
生成ADR索引
自动生成ADR列表和索引文档
"""
import sys
import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
adr_dir = project_root / "docs" / "architecture-docs" / "decision-records"


def extract_adr_info(adr_file: Path) -> Dict:
    """提取ADR信息"""
    try:
        content = adr_file.read_text(encoding='utf-8')
        
        # 提取ADR编号
        number_match = re.search(r'^#\s+ADR-(\d+):\s*(.+)$', content, re.MULTILINE)
        if not number_match:
            return None
        
        adr_number = number_match.group(1)
        title = number_match.group(2).strip()
        
        # 提取元数据
        status_match = re.search(r'\*\*状态\*\*:\s*([^\n]+)', content)
        status = status_match.group(1).strip() if status_match else "未知"
        
        date_match = re.search(r'\*\*日期\*\*:\s*([^\n]+)', content)
        date = date_match.group(1).strip() if date_match else "未知"
        
        author_match = re.search(r'\*\*作者\*\*:\s*([^\n]+)', content)
        author = author_match.group(1).strip() if author_match else "未知"
        
        tags_match = re.search(r'\*\*标签\*\*:\s*([^\n]+)', content)
        tags = tags_match.group(1).strip() if tags_match else ""
        
        # 提取决策结果
        decision_match = re.search(
            r'###\s+选择的方案\s*\n\*\*方案\[X\]\*\*:\s*\[([^\]]+)\]',
            content
        )
        decision = decision_match.group(1).strip() if decision_match else ""
        
        return {
            "number": int(adr_number),
            "title": title,
            "status": status,
            "date": date,
            "author": author,
            "tags": tags,
            "decision": decision,
            "file": adr_file.name
        }
    except Exception as e:
        print(f"警告: 无法解析 {adr_file.name}: {e}")
        return None


def generate_index():
    """生成ADR索引"""
    if not adr_dir.exists():
        print("ADR目录不存在")
        return
    
    # 收集所有ADR
    adr_files = sorted(adr_dir.glob("*.md"))
    adr_files = [f for f in adr_files if f.name not in ["README.md", "adr-template.md"]]
    
    adrs = []
    for adr_file in adr_files:
        info = extract_adr_info(adr_file)
        if info:
            adrs.append(info)
    
    # 按编号排序
    adrs.sort(key=lambda x: x["number"])
    
    # 生成索引内容
    lines = []
    lines.append("# 架构决策记录 (ADR) 索引")
    lines.append("")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**ADR总数**: {len(adrs)}")
    lines.append("")
    
    # 按状态分组
    status_groups = {}
    for adr in adrs:
        status = adr["status"]
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(adr)
    
    # 状态统计
    lines.append("## 状态统计")
    lines.append("")
    for status, group in sorted(status_groups.items()):
        lines.append(f"- **{status}**: {len(group)}")
    lines.append("")
    
    # ADR列表
    lines.append("## ADR列表")
    lines.append("")
    lines.append("| 编号 | 标题 | 状态 | 日期 | 作者 | 决策 |")
    lines.append("|------|------|------|------|------|------|")
    
    for adr in adrs:
        number = f"[ADR-{adr['number']:04d}](./{adr['file']})"
        title = adr['title']
        status = adr['status']
        date = adr['date']
        author = adr['author']
        decision = adr['decision'][:50] + "..." if len(adr['decision']) > 50 else adr['decision']
        
        lines.append(f"| {number} | {title} | {status} | {date} | {author} | {decision} |")
    
    lines.append("")
    
    # 按标签分组
    tag_groups = {}
    for adr in adrs:
        tags = [tag.strip() for tag in adr["tags"].split("|") if tag.strip()]
        for tag in tags:
            if tag not in tag_groups:
                tag_groups[tag] = []
            tag_groups[tag].append(adr)
    
    if tag_groups:
        lines.append("## 按标签分组")
        lines.append("")
        for tag, group in sorted(tag_groups.items()):
            lines.append(f"### {tag}")
            lines.append("")
            for adr in group:
                lines.append(f"- [ADR-{adr['number']:04d}: {adr['title']}](./{adr['file']}) ({adr['status']})")
            lines.append("")
    
    # 相关决策关系
    lines.append("## 相关决策关系")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph TD")
    
    for adr in adrs:
        adr_id = f"ADR{adr['number']:04d}"
        title_short = adr['title'][:20] + "..." if len(adr['title']) > 20 else adr['title']
        lines.append(f'    {adr_id}["ADR-{adr["number"]:04d}<br/>{title_short}"]')
    
    lines.append("```")
    lines.append("")
    
    # 保存索引文件
    index_file = adr_dir / "INDEX.md"
    index_file.write_text("\n".join(lines), encoding='utf-8')
    
    print(f"✅ ADR索引已生成: {index_file}")
    print(f"   共 {len(adrs)} 个ADR")


if __name__ == "__main__":
    generate_index()









