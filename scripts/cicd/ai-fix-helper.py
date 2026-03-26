#!/usr/bin/env python3
"""
AI辅助修复工具
从GitHub Actions日志中提取错误，生成修复建议
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

class ErrorAnalyzer:
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.errors = []
        
    def extract_typescript_errors(self, log_file: Path) -> List[Dict]:
        """提取TypeScript错误"""
        errors = []
        
        if not log_file.exists():
            return errors
            
        content = log_file.read_text(encoding='utf-8', errors='ignore')
        
        # 匹配TypeScript错误模式
        pattern = r'\./(src/[^:]+):(\d+):(\d+)\s+Type error:\s*(.+)'
        matches = re.finditer(pattern, content, re.MULTILINE)
        
        for match in matches:
            errors.append({
                'type': 'typescript',
                'file': match.group(1),
                'line': int(match.group(2)),
                'column': int(match.group(3)),
                'message': match.group(4).strip(),
                'full_match': match.group(0)
            })
            
        return errors
    
    def extract_build_errors(self, log_file: Path) -> List[Dict]:
        """提取构建错误"""
        errors = []
        
        if not log_file.exists():
            return errors
            
        content = log_file.read_text(encoding='utf-8', errors='ignore')
        
        # 匹配常见构建错误
        patterns = [
            (r'ERROR:\s*(.+)', 'error'),
            (r'error:\s*(.+)', 'error'),
            (r'failed to\s+(.+)', 'failure'),
            (r'Cannot find module\s+[\'"]?([^\'"]+)', 'missing_module'),
        ]
        
        for pattern, error_type in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                errors.append({
                    'type': error_type,
                    'message': match.group(1).strip(),
                    'full_match': match.group(0)
                })
                
        return errors
    
    def analyze_all_logs(self) -> Dict:
        """分析所有日志文件"""
        all_errors = {
            'typescript': [],
            'build': [],
            'test': [],
            'other': []
        }
        
        # 查找所有日志文件
        for log_file in self.log_dir.glob('*.log'):
            if 'frontend' in log_file.name or 'test' in log_file.name:
                ts_errors = self.extract_typescript_errors(log_file)
                all_errors['typescript'].extend(ts_errors)
                
            if 'build' in log_file.name:
                build_errors = self.extract_build_errors(log_file)
                all_errors['build'].extend(build_errors)
        
        return all_errors
    
    def generate_fix_suggestions(self, errors: Dict) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        # TypeScript错误修复建议
        for error in errors.get('typescript', []):
            file_path = error.get('file', '')
            message = error.get('message', '')
            
            if 'does not exist' in message:
                prop = re.search(r"'(\w+)'", message)
                if prop:
                    suggestions.append(
                        f"在 {file_path} 中添加缺失的属性: {prop.group(1)}"
                    )
                    
            if 'Cannot find name' in message:
                name = re.search(r"'(\w+)'", message)
                if name:
                    suggestions.append(
                        f"在 {file_path} 中导入: {name.group(1)}"
                    )
                    
            if 'is not assignable' in message:
                suggestions.append(
                    f"修复 {file_path}:{error.get('line')} 的类型不匹配问题"
                )
        
        # 构建错误修复建议
        for error in errors.get('build', []):
            message = error.get('message', '')
            if 'Cannot find module' in message:
                module = re.search(r"module\s+['\"]?([^'\"]+)", message)
                if module:
                    suggestions.append(
                        f"安装缺失的模块: {module.group(1)}"
                    )
        
        return suggestions

def main():
    if len(sys.argv) < 2:
        print("用法: python ai-fix-helper.py <log_directory>")
        sys.exit(1)
    
    log_dir = sys.argv[1]
    analyzer = ErrorAnalyzer(log_dir)
    
    print("分析错误...")
    errors = analyzer.analyze_all_logs()
    
    print("\n发现的错误:")
    print(f"  TypeScript错误: {len(errors['typescript'])}")
    print(f"  构建错误: {len(errors['build'])}")
    
    if errors['typescript']:
        print("\nTypeScript错误详情:")
        for error in errors['typescript'][:5]:  # 只显示前5个
            print(f"  {error['file']}:{error['line']} - {error['message']}")
    
    print("\n修复建议:")
    suggestions = analyzer.generate_fix_suggestions(errors)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")
    
    # 输出JSON格式供其他脚本使用
    output = {
        'errors': errors,
        'suggestions': suggestions
    }
    
    output_file = Path(log_dir) / 'error-analysis.json'
    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n分析结果已保存: {output_file}")

if __name__ == '__main__':
    main()





