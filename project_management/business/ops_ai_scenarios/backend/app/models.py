import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .db import Base


class AIScenario(Base):
    __tablename__ = "ai_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    domain = Column(String(100), nullable=False)
    categories = Column(JSONB, nullable=False, default=list)  # string[]
    app_company = Column(String(200), nullable=True)
    platform = Column(String(200), nullable=True)

    pain_points = Column(Text, nullable=False)
    problems_to_solve = Column(Text, nullable=False)
    expected_outcomes = Column(Text, nullable=False)

    implementation_approach = Column(Text, nullable=False)
    technical_route = Column(Text, nullable=True)
    plan_schedule = Column(Text, nullable=False)

    status = Column(String(30), nullable=False, default="draft")  # draft/submitted
    created_by = Column(String(64), nullable=False)
    created_by_name = Column(String(100), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    attachments = relationship(
        "AIScenarioAttachment",
        back_populates="scenario",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AIScenarioAttachment(Base):
    __tablename__ = "ai_scenario_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("ai_scenarios.id", ondelete="CASCADE"))

    file_name = Column(String(255), nullable=False)
    content_type = Column(String(120), nullable=True)
    size = Column(Integer, nullable=False, default=0)
    storage_path = Column(String(500), nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(64), nullable=False)

    scenario = relationship("AIScenario", back_populates="attachments")

