from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    stored_path: Mapped[str] = mapped_column(String(500))
    upload_timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    extraction_status: Mapped[str] = mapped_column(String(40), default="completed")

    requirements: Mapped[list["Requirement"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    requirement_code: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="Functional")
    module: Mapped[str] = mapped_column(String(120), default="General")
    source_reference: Mapped[str] = mapped_column(String(255), default="Document text")

    document: Mapped[Document] = relationship(back_populates="requirements")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    change_type: Mapped[str] = mapped_column(String(20))
    proposed_change: Mapped[str] = mapped_column(Text)
    target_requirement_id: Mapped[int | None] = mapped_column(ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True)
    creation_timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    overall_summary: Mapped[str] = mapped_column(Text, default="")
    overall_risk: Mapped[str] = mapped_column(String(30), default="Low")
    result_json: Mapped[str] = mapped_column(Text, default="{}")

    document: Mapped[Document] = relationship(back_populates="analyses")
    impact_results: Mapped[list["ImpactResult"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class ImpactResult(Base):
    __tablename__ = "impact_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), index=True)
    impact_type: Mapped[str] = mapped_column(String(20))
    impact_score: Mapped[float] = mapped_column()
    severity: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column()
    explanation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(Text)
    signal_details: Mapped[str] = mapped_column(Text, default="{}")

    analysis: Mapped[Analysis] = relationship(back_populates="impact_results")


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    requirement_id: Mapped[int | None] = mapped_column(ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True)
    test_case_code: Mapped[str] = mapped_column(String(30))
    objective: Mapped[str] = mapped_column(Text)
    preconditions: Mapped[str] = mapped_column(Text)
    steps: Mapped[str] = mapped_column(Text)
    expected_result: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40))

    analysis: Mapped[Analysis] = relationship(back_populates="test_cases")


Index("ix_impact_analysis_requirement", ImpactResult.analysis_id, ImpactResult.requirement_id)
