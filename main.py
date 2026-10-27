"""
Patient Service Recovery System — FastAPI Backend
Main application entry point with all API routes.

Agents:
  POST /api/pipeline/run          — Run full multi-agent pipeline
  GET  /api/feedback              — List all feedback records
  GET  /api/feedback/{id}         — Single feedback record
  GET  /api/analysis              — All analysis results
  GET  /api/risks                 — All risk flags
  GET  /api/priorities            — All priority cases
  GET  /api/recovery              — All recovery plans
  POST /api/review/{feedback_id}  — Submit human review decision
  GET  /api/reviews               — All human reviews
  GET  /api/report                — Audit report
  GET  /api/dashboard             — Dashboard statistics
  DELETE /api/reset               — Reset database (dev only)
"""

import json
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import (
    create_tables, get_db,
    PatientFeedback, AnalysisResult, RiskFlag,
    PriorityCase, RecoveryPlan, HumanReview, AuditLog
)
from agents import (
    DataPreparationAgent,
    FeedbackAnalysisAgent,
    RiskIdentificationAgent,
    PrioritisationAgent,
    RecoveryPlanningAgent,
    AuditReportingAgent,
    granite,
)
from synthetic_data import SYNTHETIC_FEEDBACK

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Patient Service Recovery System",
    description="Agentic AI system for patient feedback analysis and service recovery.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    create_tables()
    print("[OK] Database tables created.")
    print(f"[AI] IBM Granite: {'ENABLED' if granite.enabled else 'Disabled (using built-in AI logic)'}")


# ---------------------------------------------------------------------------
# Pydantic models for request/response
# ---------------------------------------------------------------------------

class HumanReviewRequest(BaseModel):
    reviewer_name: str
    decision: str          # Approved / Rejected / Modified
    reviewer_notes: str = ""
    modified_action: str = ""


# ---------------------------------------------------------------------------
# Helper: log agent action to audit trail
# ---------------------------------------------------------------------------

def log_audit(db: Session, feedback_id: str, agent: str, action: str, details: str = ""):
    entry = AuditLog(
        feedback_id=feedback_id,
        agent_name=agent,
        action=action,
        details=details,
        timestamp=datetime.utcnow(),
    )
    db.add(entry)


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main dashboard HTML."""
    html_path = os.path.join("static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend not found. Run setup first.</h1>", status_code=404)


# ---------------------------------------------------------------------------
# Pipeline: Run all agents
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/run")
async def run_pipeline(db: Session = Depends(get_db)):
    """
    Execute the full multi-agent pipeline:
    1. Data Preparation
    2. Feedback Analysis
    3. Risk Identification
    4. Prioritisation
    5. Recovery Planning
    Idempotent: existing records are skipped.
    """
    existing_ids = {r.feedback_id for r in db.query(PatientFeedback.feedback_id).all()}

    prep_agent = DataPreparationAgent()
    analysis_agent = FeedbackAnalysisAgent()
    risk_agent = RiskIdentificationAgent()
    priority_agent = PrioritisationAgent()
    recovery_agent = RecoveryPlanningAgent()

    processed = 0
    skipped = 0
    results_summary = []

    # Step 1: Data Preparation
    prepared_records = prep_agent.run(SYNTHETIC_FEEDBACK)

    for rec in prepared_records:
        fid = rec["feedback_id"]

        if fid in existing_ids:
            skipped += 1
            continue

        # --- Save raw feedback ---
        fb = PatientFeedback(
            feedback_id=fid,
            submission_date=rec.get("submission_date", ""),
            department=rec.get("department", ""),
            feedback_text=rec.get("feedback_text", ""),
            contact_method=rec.get("contact_method", ""),
            is_duplicate=rec.get("is_duplicate", False),
            has_missing_fields=rec.get("has_missing_fields", False),
            data_quality_notes=rec.get("data_quality_notes", ""),
        )
        db.add(fb)
        log_audit(db, fid, prep_agent.NAME, "Data preparation complete", rec["data_quality_notes"])

        # --- Step 2: Feedback Analysis ---
        analysis = analysis_agent.analyse(fid, rec["feedback_text"])
        ar = AnalysisResult(**analysis)
        db.add(ar)
        log_audit(db, fid, analysis_agent.NAME,
                  f"Classified as '{analysis['category']}' | Sentiment: {analysis['sentiment']}")

        # --- Step 3: Risk Identification ---
        risk = risk_agent.identify(
            fid, rec["feedback_text"], analysis["category"], analysis["sentiment"]
        )
        rf = RiskFlag(**risk)
        db.add(rf)
        log_audit(db, fid, risk_agent.NAME,
                  f"Risk level: {risk['risk_level']} | Type: {risk['risk_type']}")

        # --- Step 4: Prioritisation ---
        priority = priority_agent.prioritise(
            fid,
            risk["risk_level"],
            rec.get("department", ""),
            analysis["sentiment"],
            rec["feedback_text"],
            risk["requires_escalation"],
        )
        pc = PriorityCase(**priority)
        db.add(pc)
        log_audit(db, fid, priority_agent.NAME,
                  f"Priority: {priority['priority_level']} | Score: {priority['priority_score']}")

        # --- Step 5: Recovery Planning ---
        plan = recovery_agent.plan(
            fid,
            analysis["category"],
            risk["risk_level"],
            rec.get("department", ""),
            rec["feedback_text"],
            analysis["summary"],
        )
        rp = RecoveryPlan(**plan)
        db.add(rp)
        log_audit(db, fid, recovery_agent.NAME,
                  f"Recovery plan generated | Timeline: {plan['timeline_days']} days")

        db.commit()
        processed += 1
        results_summary.append({
            "feedback_id": fid,
            "category": analysis["category"],
            "risk_level": risk["risk_level"],
            "priority": priority["priority_level"],
        })

    return {
        "status": "success",
        "processed": processed,
        "skipped": skipped,
        "granite_enabled": granite.enabled,
        "message": f"Pipeline complete. {processed} new records processed, {skipped} skipped.",
        "results": results_summary,
    }


# ---------------------------------------------------------------------------
# Feedback endpoints
# ---------------------------------------------------------------------------

@app.get("/api/feedback")
async def get_all_feedback(db: Session = Depends(get_db)):
    records = db.query(PatientFeedback).all()
    return [
        {
            "id": r.id,
            "feedback_id": r.feedback_id,
            "submission_date": r.submission_date,
            "department": r.department,
            "feedback_text": r.feedback_text,
            "contact_method": r.contact_method,
            "is_duplicate": r.is_duplicate,
            "has_missing_fields": r.has_missing_fields,
            "data_quality_notes": r.data_quality_notes,
        }
        for r in records
    ]


@app.get("/api/feedback/{feedback_id}")
async def get_feedback(feedback_id: str, db: Session = Depends(get_db)):
    """Return a complete case file for one feedback record."""
    fb = db.query(PatientFeedback).filter(PatientFeedback.feedback_id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")

    analysis = db.query(AnalysisResult).filter(AnalysisResult.feedback_id == feedback_id).first()
    risk = db.query(RiskFlag).filter(RiskFlag.feedback_id == feedback_id).first()
    priority = db.query(PriorityCase).filter(PriorityCase.feedback_id == feedback_id).first()
    plan = db.query(RecoveryPlan).filter(RecoveryPlan.feedback_id == feedback_id).first()
    review = db.query(HumanReview).filter(HumanReview.feedback_id == feedback_id).first()

    return {
        "feedback": {
            "feedback_id": fb.feedback_id,
            "submission_date": fb.submission_date,
            "department": fb.department,
            "feedback_text": fb.feedback_text,
            "contact_method": fb.contact_method,
            "data_quality_notes": fb.data_quality_notes,
        },
        "analysis": {
            "category": analysis.category if analysis else None,
            "sentiment": analysis.sentiment if analysis else None,
            "themes": json.loads(analysis.themes) if analysis and analysis.themes else [],
            "summary": analysis.summary if analysis else None,
            "confidence_score": analysis.confidence_score if analysis else None,
            "granite_enhanced": analysis.granite_enhanced if analysis else False,
        } if analysis else None,
        "risk": {
            "risk_level": risk.risk_level if risk else None,
            "risk_type": risk.risk_type if risk else None,
            "risk_description": risk.risk_description if risk else None,
            "requires_escalation": risk.requires_escalation if risk else False,
        } if risk else None,
        "priority": {
            "priority_level": priority.priority_level if priority else None,
            "priority_score": priority.priority_score if priority else None,
            "priority_rationale": priority.priority_rationale if priority else None,
            "assigned_department": priority.assigned_department if priority else None,
        } if priority else None,
        "recovery_plan": {
            "recommended_action": plan.recommended_action if plan else None,
            "responsible_role": plan.responsible_role if plan else None,
            "follow_up_steps": plan.follow_up_steps if plan else None,
            "empathy_statement": plan.empathy_statement if plan else None,
            "timeline_days": plan.timeline_days if plan else None,
            "status": plan.status if plan else None,
        } if plan else None,
        "human_review": {
            "reviewer_name": review.reviewer_name if review else None,
            "decision": review.decision if review else None,
            "reviewer_notes": review.reviewer_notes if review else None,
            "modified_action": review.modified_action if review else None,
            "reviewed_at": review.reviewed_at.isoformat() if review else None,
        } if review else None,
    }


# ---------------------------------------------------------------------------
# Analysis, Risk, Priority, Recovery endpoints
# ---------------------------------------------------------------------------

@app.get("/api/analysis")
async def get_analysis(db: Session = Depends(get_db)):
    records = db.query(AnalysisResult).all()
    return [
        {
            "feedback_id": r.feedback_id,
            "category": r.category,
            "sentiment": r.sentiment,
            "themes": json.loads(r.themes) if r.themes else [],
            "summary": r.summary,
            "confidence_score": r.confidence_score,
            "granite_enhanced": r.granite_enhanced,
        }
        for r in records
    ]


@app.get("/api/risks")
async def get_risks(db: Session = Depends(get_db)):
    records = db.query(RiskFlag).all()
    return [
        {
            "feedback_id": r.feedback_id,
            "risk_level": r.risk_level,
            "risk_type": r.risk_type,
            "risk_description": r.risk_description,
            "requires_escalation": r.requires_escalation,
        }
        for r in records
    ]


@app.get("/api/priorities")
async def get_priorities(db: Session = Depends(get_db)):
    records = db.query(PriorityCase).order_by(PriorityCase.priority_score.desc()).all()
    return [
        {
            "feedback_id": r.feedback_id,
            "priority_score": r.priority_score,
            "priority_level": r.priority_level,
            "priority_rationale": r.priority_rationale,
            "assigned_department": r.assigned_department,
        }
        for r in records
    ]


@app.get("/api/recovery")
async def get_recovery_plans(db: Session = Depends(get_db)):
    records = db.query(RecoveryPlan).all()
    return [
        {
            "feedback_id": r.feedback_id,
            "recommended_action": r.recommended_action,
            "responsible_role": r.responsible_role,
            "follow_up_steps": r.follow_up_steps,
            "empathy_statement": r.empathy_statement,
            "timeline_days": r.timeline_days,
            "status": r.status,
        }
        for r in records
    ]


# ---------------------------------------------------------------------------
# Human Review (Human-in-the-loop)
# ---------------------------------------------------------------------------

@app.post("/api/review/{feedback_id}")
async def submit_review(
    feedback_id: str,
    review_request: HumanReviewRequest,
    db: Session = Depends(get_db),
):
    """
    Human reviewer approves, rejects, or modifies a recovery plan.
    This is the core human-in-the-loop gate — no recovery action
    can proceed without passing through this endpoint.
    """
    plan = db.query(RecoveryPlan).filter(RecoveryPlan.feedback_id == feedback_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found")

    # Validate decision value
    valid_decisions = {"Approved", "Rejected", "Modified"}
    if review_request.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Decision must be one of: {', '.join(valid_decisions)}"
        )

    # Check if already reviewed
    existing_review = db.query(HumanReview).filter(
        HumanReview.feedback_id == feedback_id
    ).first()

    if existing_review:
        # Update existing review
        existing_review.reviewer_name = review_request.reviewer_name
        existing_review.decision = review_request.decision
        existing_review.reviewer_notes = review_request.reviewer_notes
        existing_review.modified_action = review_request.modified_action
        existing_review.reviewed_at = datetime.utcnow()
    else:
        hr = HumanReview(
            feedback_id=feedback_id,
            reviewer_name=review_request.reviewer_name,
            decision=review_request.decision,
            reviewer_notes=review_request.reviewer_notes,
            modified_action=review_request.modified_action,
            reviewed_at=datetime.utcnow(),
        )
        db.add(hr)

    # Update recovery plan status
    plan.status = review_request.decision
    if review_request.modified_action:
        plan.recommended_action = review_request.modified_action

    log_audit(
        db, feedback_id, "Human Reviewer",
        f"Decision: {review_request.decision} by {review_request.reviewer_name}",
        review_request.reviewer_notes,
    )
    db.commit()

    return {
        "status": "success",
        "feedback_id": feedback_id,
        "decision": review_request.decision,
        "message": f"Review submitted. Plan status updated to '{review_request.decision}'.",
    }


@app.get("/api/reviews")
async def get_all_reviews(db: Session = Depends(get_db)):
    records = db.query(HumanReview).all()
    return [
        {
            "feedback_id": r.feedback_id,
            "reviewer_name": r.reviewer_name,
            "decision": r.decision,
            "reviewer_notes": r.reviewer_notes,
            "modified_action": r.modified_action,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        }
        for r in records
    ]


# ---------------------------------------------------------------------------
# Audit Report
# ---------------------------------------------------------------------------

@app.get("/api/report")
async def get_audit_report(db: Session = Depends(get_db)):
    agent = AuditReportingAgent()
    return agent.generate_report(db)


# ---------------------------------------------------------------------------
# Dashboard statistics (summary for front-end cards)
# ---------------------------------------------------------------------------

@app.get("/api/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(PatientFeedback).count()
    analysed = db.query(AnalysisResult).count()
    escalations = db.query(RiskFlag).filter(RiskFlag.requires_escalation == True).count()
    pending = db.query(RecoveryPlan).filter(RecoveryPlan.status == "Pending Review").count()
    approved = db.query(RecoveryPlan).filter(RecoveryPlan.status == "Approved").count()
    rejected = db.query(RecoveryPlan).filter(RecoveryPlan.status == "Rejected").count()

    # Critical/High risk counts
    critical = db.query(RiskFlag).filter(RiskFlag.risk_level == "Critical").count()
    high = db.query(RiskFlag).filter(RiskFlag.risk_level == "High").count()
    medium = db.query(RiskFlag).filter(RiskFlag.risk_level == "Medium").count()
    low = db.query(RiskFlag).filter(RiskFlag.risk_level == "Low").count()

    # Sentiment counts
    neg = db.query(AnalysisResult).filter(AnalysisResult.sentiment == "Negative").count()
    pos = db.query(AnalysisResult).filter(AnalysisResult.sentiment == "Positive").count()
    neu = db.query(AnalysisResult).filter(AnalysisResult.sentiment == "Neutral").count()

    return {
        "total_feedback": total,
        "records_analysed": analysed,
        "pending_review": pending,
        "approved_plans": approved,
        "rejected_plans": rejected,
        "requires_escalation": escalations,
        "granite_enabled": granite.enabled,
        "risk_counts": {
            "Critical": critical,
            "High": high,
            "Medium": medium,
            "Low": low,
        },
        "sentiment_counts": {
            "Negative": neg,
            "Positive": pos,
            "Neutral": neu,
        },
    }


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

@app.get("/api/audit")
async def get_audit_log(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    return [
        {
            "feedback_id": l.feedback_id,
            "agent_name": l.agent_name,
            "action": l.action,
            "details": l.details,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
        }
        for l in logs
    ]


# ---------------------------------------------------------------------------
# Reset (development only)
# ---------------------------------------------------------------------------

@app.delete("/api/reset")
async def reset_database(db: Session = Depends(get_db)):
    """Drop and recreate all tables. For development/demo use only."""
    from database import Base, engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"status": "reset", "message": "Database reset complete."}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
