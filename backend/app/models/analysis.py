from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    resume_filename = Column(String, nullable=False)
    job_title = Column(String, nullable=True)

    semantic_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    keyword_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)

    summary = Column(Text, nullable=True)
    experience_text = Column(Text, nullable=True)
    projects_text = Column(Text, nullable=True)
    quality_json = Column(Text, nullable=True)
    compatibility_json = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)
    jd_text = Column(Text, nullable=True)
    status = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    skills = relationship("AnalysisSkill", back_populates="analysis", cascade="all, delete-orphan")


class AnalysisSkill(Base):
    __tablename__ = "analysis_skills"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    skill = Column(String, nullable=False)
    status = Column(String, nullable=False)  # matched | missing | additional

    analysis = relationship("Analysis", back_populates="skills")
