import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .auth import get_current_user
from .config import settings
from .db import Base, engine, get_db
from .models import AIScenario, AIScenarioAttachment
from .schemas import (
    AIScenarioCreate,
    AIScenarioOut,
    AIScenarioUpdate,
    AttachmentOut,
    PaginatedAIScenarios,
    SubmitResponse,
)


app = FastAPI(
    title="AI Scenario Service",
    version="1.0.0",
    description="AI应用场景收集服务（V1）",
)


@app.on_event("startup")
def on_startup():
    # V1：自动建表（后续可用 Alembic 迁移替换）
    Base.metadata.create_all(bind=engine)
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def _is_admin(user: dict) -> bool:
    if not user:
        return False
    if (user.get("username") or "").lower() == "admin":
        return True
    roles = user.get("roles") or []
    return any(str(r).lower() == "admin" for r in roles)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ai-scenario-service"}


@app.get("/api/v1/ai-scenarios", response_model=PaginatedAIScenarios)
def list_scenarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    mine: bool = Query(True, description="普通用户默认只看自己；管理员可 mine=false 查看全部"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    q = db.query(AIScenario)

    if domain:
        q = q.filter(AIScenario.domain == domain)
    if status:
        q = q.filter(AIScenario.status == status)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            or_(
                AIScenario.pain_points.ilike(like),
                AIScenario.problems_to_solve.ilike(like),
                AIScenario.expected_outcomes.ilike(like),
                AIScenario.implementation_approach.ilike(like),
                AIScenario.technical_route.ilike(like),
                AIScenario.plan_schedule.ilike(like),
                AIScenario.domain.ilike(like),
                AIScenario.app_company.ilike(like),
                AIScenario.platform.ilike(like),
            )
        )

    if not _is_admin(user) or mine:
        q = q.filter(AIScenario.created_by == user["user_id"])

    total = q.with_entities(func.count(AIScenario.id)).scalar() or 0
    items = (
        q.order_by(AIScenario.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.post("/api/v1/ai-scenarios", response_model=AIScenarioOut)
def create_scenario(
    payload: AIScenarioCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    scenario = AIScenario(
        **payload.model_dump(),
        status="draft",
        created_by=user["user_id"],
        created_by_name=user.get("username"),
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def _get_scenario_or_404(db: Session, scenario_id: str) -> AIScenario:
    try:
        sid = uuid.UUID(scenario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario id")
    scenario = db.query(AIScenario).filter(AIScenario.id == sid).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@app.get("/api/v1/ai-scenarios/{scenario_id}", response_model=AIScenarioOut)
def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    scenario = _get_scenario_or_404(db, scenario_id)
    if not _is_admin(user) and scenario.created_by != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return scenario


@app.put("/api/v1/ai-scenarios/{scenario_id}", response_model=AIScenarioOut)
def update_scenario(
    scenario_id: str,
    payload: AIScenarioUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    scenario = _get_scenario_or_404(db, scenario_id)
    if not _is_admin(user) and scenario.created_by != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if scenario.status != "draft" and not _is_admin(user):
        raise HTTPException(status_code=400, detail="Only draft scenario can be edited")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(scenario, k, v)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@app.delete("/api/v1/ai-scenarios/{scenario_id}", status_code=204)
def delete_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    scenario = _get_scenario_or_404(db, scenario_id)
    if not _is_admin(user) and scenario.created_by != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if scenario.status != "draft" and not _is_admin(user):
        raise HTTPException(status_code=400, detail="Only draft scenario can be deleted")

    # 删除附件文件（尽力而为）
    for att in scenario.attachments:
        try:
            os.remove(att.storage_path)
        except Exception:
            pass

    db.delete(scenario)
    db.commit()
    return None


@app.post("/api/v1/ai-scenarios/{scenario_id}/submit", response_model=SubmitResponse)
def submit_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    scenario = _get_scenario_or_404(db, scenario_id)
    if not _is_admin(user) and scenario.created_by != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if scenario.status != "draft":
        return {"id": scenario.id, "status": scenario.status}
    scenario.status = "submitted"
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return {"id": scenario.id, "status": scenario.status}


@app.get("/api/v1/ai-scenarios/{scenario_id}/attachments", response_model=list[AttachmentOut])
def list_attachments(
    scenario_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    scenario = _get_scenario_or_404(db, scenario_id)
    if not _is_admin(user) and scenario.created_by != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return scenario.attachments


@app.post("/api/v1/ai-scenarios/{scenario_id}/attachments", response_model=list[AttachmentOut])
async def upload_attachments(
    scenario_id: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    scenario = _get_scenario_or_404(db, scenario_id)
    if not _is_admin(user) and scenario.created_by != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if scenario.status != "draft" and not _is_admin(user):
        raise HTTPException(status_code=400, detail="Only draft scenario can upload attachments")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    saved: list[AIScenarioAttachment] = []
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        content = await f.read()
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File too large: {f.filename}")

        file_id = uuid.uuid4().hex
        safe_name = (f.filename or "file").replace("/", "_").replace("\\", "_")
        target = upload_dir / f"{scenario.id}_{file_id}_{safe_name}"
        target.write_bytes(content)

        att = AIScenarioAttachment(
            scenario_id=scenario.id,
            file_name=f.filename or "file",
            content_type=f.content_type,
            size=len(content),
            storage_path=str(target),
            created_by=user["user_id"],
        )
        db.add(att)
        saved.append(att)

    db.commit()
    for att in saved:
        db.refresh(att)
    return saved


@app.get("/api/v1/ai-scenarios/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        aid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid attachment id")

    att = db.query(AIScenarioAttachment).filter(AIScenarioAttachment.id == aid).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    scenario = db.query(AIScenario).filter(AIScenario.id == att.scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if not _is_admin(user) and scenario.created_by != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    path = Path(att.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing")
    return FileResponse(path, filename=att.file_name, media_type=att.content_type)


@app.delete("/api/v1/ai-scenarios/attachments/{attachment_id}", status_code=204)
def delete_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        aid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid attachment id")

    att = db.query(AIScenarioAttachment).filter(AIScenarioAttachment.id == aid).first()
    if not att:
        return None
    scenario = db.query(AIScenario).filter(AIScenario.id == att.scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if not _is_admin(user) and scenario.created_by != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if scenario.status != "draft" and not _is_admin(user):
        raise HTTPException(status_code=400, detail="Only draft scenario can delete attachments")

    try:
        os.remove(att.storage_path)
    except Exception:
        pass
    db.delete(att)
    db.commit()
    return None

