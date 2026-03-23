"""
批量导入提示词模板到数据库
来源：agent-service/config/prompt_templates.yaml
"""
import os
import sys
from pathlib import Path
import yaml
from typing import Any, Dict, List

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "database" / "src"))

from sqlalchemy.orm import Session
from database.src.core.session import SessionLocal, init_session_factory
from database.src.models.prompt_template import PromptTemplate


def load_templates_from_yaml(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        print(f"YAML file not found: {path}")
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # 支持多种结构：
    # 1) {templates: [ ... ]}
    # 2) {prompt_templates: {key: {name,...}}}
    # 3) 直接为列表
    if isinstance(data, dict) and "templates" in data and isinstance(data["templates"], list):
        return data["templates"]
    if isinstance(data, dict) and "prompt_templates" in data and isinstance(data["prompt_templates"], dict):
        result = []
        for key, val in data["prompt_templates"].items():
            if isinstance(val, dict):
                if "name" not in val:
                    val["name"] = key
                result.append(val)
        return result
    if isinstance(data, list):
        return data
    return []


def upsert_templates(db: Session, templates: List[Dict[str, Any]]):
    count_created = 0
    count_updated = 0
    for tpl in templates:
        name = tpl.get("name")
        if not name:
            continue
        existing = db.query(PromptTemplate).filter(PromptTemplate.name == name).first()
        payload = {
            "category": tpl.get("category", "general"),
            "description": tpl.get("description"),
            "system_prompt": tpl.get("system_prompt"),
            "examples": tpl.get("examples") or [],
            "temperature": tpl.get("temperature", 0.3),
            "max_tokens": tpl.get("max_tokens", 2000),
            "top_p": tpl.get("top_p", 0.9),
            "frequency_penalty": tpl.get("frequency_penalty", 0.0),
            "presence_penalty": tpl.get("presence_penalty", 0.0),
            "stop_sequences": tpl.get("stop_sequences") or [],
            "output_format": tpl.get("output_format"),
            "dynamic_placeholders": tpl.get("dynamic_placeholders") or [],
            "is_active": tpl.get("is_active", True),
            "created_by": tpl.get("created_by"),
            "metadata_": tpl.get("metadata") or {},
        }
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            existing.version = (existing.version or 1) + 1
            count_updated += 1
        else:
            db.add(PromptTemplate(name=name, version=1, **payload))
            count_created += 1
    db.commit()
    print(f"Created: {count_created}, Updated: {count_updated}")


def main():
    # 初始化数据库
    init_session_factory()
    db = SessionLocal()
    try:
        yaml_path = project_root / "config" / "prompt_templates.yaml"
        templates = load_templates_from_yaml(yaml_path)
        print(f"Loaded {len(templates)} templates from {yaml_path}")
        upsert_templates(db, templates)
    finally:
        db.close()


if __name__ == "__main__":
    main()

