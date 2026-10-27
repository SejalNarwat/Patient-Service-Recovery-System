"""
Database models and initialization for Patient Service Recovery System.
Uses SQLite via SQLAlchemy for simple, portable storage.
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./patient_recovery.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class PatientFeedback(Base):
    """Raw de-identified patient feedback record."""
    __tablename__ = "patient_feedback"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(20), unique=True, index=True)
    submission_date = Column(String(20))
    department = Column(String(100))
    feedback_text = Column(Text)
    contact_method = Column(String(50))   # Written / Verbal / Online
    is_duplicate = Column(Boolean, default=False)
    has_missing_fields = Column(Boolean, default=False)
    data_quality_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalysisResult(Base):
    """Output from the Feedback Analysis Agent."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(20), index=True)
    category = Column(String(100))        # e.g. Appointment Delay
    sentiment = Column(String(20))        # Negative / Neutral / Positive
    themes = Column(Text)                 # JSON list of themes
    summary = Column(Text)
    confidence_score = Column(Float, default=0.0)
    granite_enhanced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskFlag(Base):
    """Output from the Risk Identification Agent."""
    __tablename__ = "risk_flags"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(20), index=True)
    risk_level = Column(String(20))       # Critical / High / Medium / Low
    risk_type = Column(String(100))       # Safety / Repeated Failure / Ambiguous / Urgent
    risk_description = Column(Text)
    requires_escalation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PriorityCase(Base):
    """Output from the Prioritisation Agent."""
    __tablename__ = "priority_cases"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(20), unique=True, index=True)
    priority_score = Column(Float, default=0.0)
    priority_level = Column(String(20))   # P1-Critical / P2-High / P3-Medium / P4-Low
    priority_rationale = Column(Text)
    assigned_department = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class RecoveryPlan(Base):
    """Output from the Recovery Planning Agent."""
    __tablename__ = "recovery_plans"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(20), unique=True, index=True)
    recommended_action = Column(Text)
    responsible_role = Column(String(100))
    follow_up_steps = Column(Text)
    empathy_statement = Column(Text)
    timeline_days = Column(Integer, default=3)
    status = Column(String(30), default="Pending Review")  # Pending / Approved / Rejected
    created_at = Column(DateTime, default=datetime.utcnow)


class HumanReview(Base):
    """Human-in-the-loop review and approval record."""
    __tablename__ = "human_reviews"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(20), index=True)
    reviewer_name = Column(String(100))
    decision = Column(String(20))         # Approved / Rejected / Modified
    reviewer_notes = Column(Text, default="")
    modified_action = Column(Text, default="")
    reviewed_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for all agent actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(20), index=True)
    agent_name = Column(String(100))
    action = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, default="")


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
