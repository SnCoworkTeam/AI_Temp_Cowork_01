#!/usr/bin/env python3
"""
API参考文档生成
从OpenAPI规范生成完整的API参考文档
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def generate_api_reference_markdown(openapi_spec: Dict[str, Any], service_name: str) -> str:
    """从OpenAPI规范生成Markdown API参考文档"""
    lines = []
    
    info = openapi_spec.get("info", {})
    lines.append(f"# {service_name} API参考")
    lines.append("")
    lines.append(f"**版本**: {info.get('version', '1.0.0')}")
    lines.append("")
    if info.get("description"):
        lines.append(info["description"])
        lines.append("")
    
    # 服务器信息
    servers = openapi_spec.get("servers", [])
    if servers:
        lines.append("## 服务器")
        lines.append("")
        for server in servers:
            lines.append(f"- {server.get('url', '')}")
        lines.append("")
    
    # API端点
    paths = openapi_spec.get("paths", {})
    if paths:
        lines.append("## API端点")
        lines.append("")
        
        for path, methods in sorted(paths.items()):
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                lines.append(f"### {method.upper()} {path}")
                lines.append("")
                
                # 摘要和描述
                if details.get("summary"):
                    lines.append(f"**{details['summary']}**")
                    lines.append("")
                if details.get("description"):
                    lines.append(details["description"])
                    lines.append("")
                
                # 参数
                parameters = details.get("parameters", [])
                if parameters:
                    lines.append("#### 参数")
                    lines.append("")
                    for param in parameters:
                        param_info = f"- `{param.get('name')}`"
                        if param.get("in"):
                            param_info += f" ({param['in']})"
                        if param.get("required"):
                            param_info += " **必需**"
                        lines.append(param_info)
                        if param.get("description"):
                            lines.append(f"  - {param['description']}")
                    lines.append("")
                
                # 请求体
                request_body = details.get("requestBody", {})
                if request_body:
                    lines.append("#### 请求体")
                    lines.append("")
                    content = request_body.get("content", {})
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})
                        lines.append("```json")
                        # 这里可以生成示例JSON
                        lines.append("{}")
                        lines.append("```")
                        lines.append("")
                
                # 响应
                responses = details.get("responses", {})
                if responses:
                    lines.append("#### 响应")
                    lines.append("")
                    for status_code, response_info in sorted(responses.items()):
                        lines.append(f"**{status_code}**: {response_info.get('description', '')}")
                        lines.append("")
                
                lines.append("---")
                lines.append("")
    
    return "\n".join(lines)


def generate_api_reference():
    """生成所有服务的API参考文档"""
    print("开始生成API参考文档...")
    
    output_dir = project_root / "docs" / "auto-generated" / "api-reference"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    openapi_dir = project_root / "docs" / "api-docs" / "openapi"
    
    services = [
        "mcp-gateway",
        "workflow-engine",
        "auth-service",
        "knowledge-base"
    ]
    
    for service in services:
        openapi_file = openapi_dir / f"{service}-openapi.json"
        
        if not openapi_file.exists():
            print(f"  跳过 {service}（OpenAPI文件不存在）")
            continue
        
        print(f"处理服务: {service}")
        
        with open(openapi_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        
        markdown = generate_api_reference_markdown(spec, service)
        
        output_file = output_dir / f"{service}-api-reference.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"  ✅ API参考已保存: {output_file}")
    
    print(f"\n✅ API参考文档生成完成")
    print(f"文档保存在: {output_dir}")


if __name__ == "__main__":
    generate_api_reference()









