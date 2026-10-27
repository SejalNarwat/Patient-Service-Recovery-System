"""
Multi-Agent System for Patient Service Recovery.

Contains all specialised agents:
  1. DataPreparationAgent
  2. FeedbackAnalysisAgent  (IBM Granite compatible)
  3. RiskIdentificationAgent
  4. PrioritisationAgent
  5. RecoveryPlanningAgent
  6. AuditReportingAgent

All agents are rule-based and self-contained. IBM Granite integration is optional
and gracefully falls back to built-in logic when API keys are unavailable.
"""

import json
import re
import os
from datetime import datetime
from typing import Optional
import httpx

# ---------------------------------------------------------------------------
# IBM Granite / Watson ML helper (optional)
# ---------------------------------------------------------------------------

class GraniteClient:
    """
    Lightweight wrapper for IBM Watson Machine Learning / Granite inference.
    Falls back to None if credentials are not configured.
    """

    def __init__(self):
        self.api_key = os.getenv("IBM_API_KEY", "")
        self.ml_url = os.getenv("IBM_ML_URL", "https://us-south.ml.cloud.ibm.com")
        self.project_id = os.getenv("IBM_PROJECT_ID", "")
        self.token: Optional[str] = None
        self.enabled = bool(self.api_key and self.api_key != "your_ibm_api_key_here")

    def _get_token(self) -> Optional[str]:
        if not self.enabled:
            return None
        try:
            resp = httpx.post(
                "https://iam.cloud.ibm.com/identity/token",
                data={"apikey": self.api_key, "grant_type": "urn:ibm:params:oauth:grant-type:apikey"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
        except Exception:
            return None

    def generate(self, prompt: str, max_tokens: int = 300) -> Optional[str]:
        """Send a prompt to IBM Granite and return the generated text."""
        if not self.enabled:
            return None
        if not self.token:
            self.token = self._get_token()
        if not self.token:
            return None
        try:
            payload = {
                "model_id": "ibm/granite-13b-instruct-v2",
                "input": prompt,
                "parameters": {
                    "decoding_method": "greedy",
                    "max_new_tokens": max_tokens,
                    "stop_sequences": ["---"],
                },
                "project_id": self.project_id,
            }
            resp = httpx.post(
                f"{self.ml_url}/ml/v1/text/generation?version=2023-05-29",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}",
                         "Content-Type": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if results:
                return results[0].get("generated_text", "").strip()
        except Exception:
            pass
        return None


granite = GraniteClient()


# ---------------------------------------------------------------------------
# 1. Data Preparation Agent
# ---------------------------------------------------------------------------

class DataPreparationAgent:
    """
    Reviews each feedback record for:
    - Missing required fields (submission_date, contact_method)
    - Duplicate feedback IDs
    - Suspiciously short / uninformative feedback text
    Returns enriched records with quality flags.
    """

    NAME = "Data Preparation Agent"
    MIN_TEXT_LENGTH = 15

    def run(self, records: list[dict]) -> list[dict]:
        seen_ids = set()
        prepared = []
        for rec in records:
            notes = []
            is_duplicate = False
            has_missing = False

            fid = rec.get("feedback_id", "")
            if fid in seen_ids:
                is_duplicate = True
                notes.append("Duplicate feedback_id detected.")
            seen_ids.add(fid)

            if not rec.get("submission_date", "").strip():
                has_missing = True
                notes.append("Missing submission_date.")
            if not rec.get("contact_method", "").strip():
                has_missing = True
                notes.append("Missing contact_method.")
            if not rec.get("department", "").strip():
                has_missing = True
                notes.append("Missing department.")

            text = rec.get("feedback_text", "")
            if len(text.strip()) < self.MIN_TEXT_LENGTH:
                notes.append("Feedback text is too short — may require follow-up.")
                has_missing = True

            prepared.append({
                **rec,
                "is_duplicate": is_duplicate,
                "has_missing_fields": has_missing,
                "data_quality_notes": " | ".join(notes) if notes else "OK",
            })
        return prepared


# ---------------------------------------------------------------------------
# 2. Feedback Analysis Agent
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS = {
    "Appointment Delay": [
        "wait", "delay", "late", "postpone", "cancel", "rescheduled", "overdue",
        "long wait", "hours", "weeks", "not seen",
    ],
    "Communication Gap": [
        "no one told", "not informed", "unclear", "didn't explain", "no follow",
        "couldn't reach", "no update", "no response", "not notified", "letters",
        "discharge instructions", "interpreter",
    ],
    "Scheduling Issue": [
        "booking", "double-booked", "online system", "conflicting", "appointment letter",
        "slot", "access", "rebook", "moved", "transport",
    ],
    "Medication / Safety": [
        "medication", "prescription", "dosage", "allergy", "insulin", "drug",
        "pharmacist", "wrong", "error", "missed dose",
    ],
    "Care Experience": [
        "staff", "nurse", "consultant", "rude", "dismissed", "support", "compassion",
        "felt ignored", "unprofessional", "dignity", "kind", "wonderful", "excellent",
    ],
    "Facility / Access": [
        "parking", "seating", "hot", "overcrowded", "wheelchair", "equipment",
        "broken", "portal", "digital", "transport", "location",
    ],
    "Mental Health": [
        "mental health", "crisis", "therapy", "anxiety", "struggling", "distress",
        "inpatient", "community support",
    ],
    "Positive Feedback": [
        "outstanding", "excellent", "wonderful", "great", "impressed", "thank",
        "no complaints", "good experience", "exceptional",
    ],
}

NEGATIVE_WORDS = [
    "not", "never", "poor", "bad", "terrible", "angry", "frustrated", "ignored",
    "dismissed", "wrong", "error", "unsafe", "failed", "no one", "missed",
    "cancelled", "delay", "wait", "concerned", "worry", "unacceptable", "harmful",
    "distress", "disappointed", "unhappy",
]
POSITIVE_WORDS = [
    "excellent", "outstanding", "wonderful", "thank", "great", "helpful",
    "kind", "impressed", "supported", "clear", "professional", "good",
]


class FeedbackAnalysisAgent:
    """
    Analyses feedback text to:
    - Classify into a primary category
    - Detect sentiment (Positive / Neutral / Negative)
    - Extract key themes
    - Generate a concise summary

    Uses IBM Granite when available; otherwise applies rule-based NLP.
    """

    NAME = "Feedback Analysis Agent"

    def _classify(self, text: str) -> tuple[str, list[str]]:
        text_lower = text.lower()
        scores = {}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[cat] = score
        if not scores:
            return "General Concern", []
        primary = max(scores, key=scores.get)
        themes = [cat for cat, s in scores.items() if s > 0 and cat != "Positive Feedback"]
        if "Positive Feedback" in scores and scores["Positive Feedback"] >= 2:
            primary = "Positive Feedback"
        return primary, themes

    def _sentiment(self, text: str) -> str:
        text_lower = text.lower()
        neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
        pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
        if pos > neg and pos >= 2:
            return "Positive"
        if neg > pos:
            return "Negative"
        return "Neutral"

    def _summarise(self, text: str, category: str, granite_enabled: bool) -> tuple[str, bool]:
        if granite_enabled:
            prompt = (
                f"Summarise the following de-identified hospital patient feedback in one clear "
                f"sentence. Focus on the main concern. Category: {category}.\n\n"
                f"Feedback: {text}\n\nSummary:"
            )
            result = granite.generate(prompt, max_tokens=80)
            if result:
                return result.strip(), True

        # Rule-based fallback: return first two sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        summary = " ".join(sentences[:2])
        if len(summary) > 200:
            summary = summary[:197] + "..."
        return summary, False

    def analyse(self, feedback_id: str, text: str) -> dict:
        category, themes = self._classify(text)
        sentiment = self._sentiment(text)
        summary, granite_used = self._summarise(text, category, granite.enabled)
        confidence = min(0.95, 0.60 + len(themes) * 0.05)
        return {
            "feedback_id": feedback_id,
            "category": category,
            "sentiment": sentiment,
            "themes": json.dumps(themes),
            "summary": summary,
            "confidence_score": round(confidence, 2),
            "granite_enhanced": granite_used,
        }


# ---------------------------------------------------------------------------
# 3. Risk Identification Agent
# ---------------------------------------------------------------------------

CRITICAL_KEYWORDS = [
    "allergy", "penicillin", "wrong medication", "wrong dosage", "appendicitis",
    "triage", "missed diagnosis", "safety", "serious", "critical",
]
HIGH_RISK_KEYWORDS = [
    "chemotherapy", "delayed treatment", "crisis", "harmful", "life-sustaining",
    "dialysis", "blood sugar", "insulin", "falling", "distress",
]
REPEATED_FAILURE_PATTERNS = [
    "third time", "fourth time", "second complaint", "raised this before",
    "previous complaint", "again", "still no", "nothing has changed",
    "another month", "same issue",
]
AMBIGUOUS_PATTERNS = [
    "not sure", "something didn't feel right", "unsettled", "unclear",
    "not satisfied", "not happy", "don't know",
]


class RiskIdentificationAgent:
    """
    Flags patient feedback for urgency:
    - Critical: potential patient safety events
    - High: health-impacting service failures
    - Medium: repeated / unresolved complaints
    - Low: general service dissatisfaction
    """

    NAME = "Risk Identification Agent"

    def identify(self, feedback_id: str, text: str, category: str, sentiment: str) -> dict:
        text_lower = text.lower()

        is_critical = any(kw in text_lower for kw in CRITICAL_KEYWORDS)
        is_high = any(kw in text_lower for kw in HIGH_RISK_KEYWORDS)
        is_repeated = any(p in text_lower for p in REPEATED_FAILURE_PATTERNS)
        is_ambiguous = any(p in text_lower for p in AMBIGUOUS_PATTERNS)

        if is_critical:
            risk_level = "Critical"
            risk_type = "Patient Safety Concern"
            desc = (
                "Feedback contains language suggesting a potential patient safety event. "
                "This must be reviewed by an authorised clinical or patient safety officer immediately."
            )
            escalate = True
        elif is_high and category in ("Medication / Safety", "Mental Health", "Appointment Delay"):
            risk_level = "High"
            risk_type = "Health-Impacting Service Failure"
            desc = (
                "Feedback indicates a service failure that may be directly impacting the patient's health. "
                "Timely review and intervention are required."
            )
            escalate = True
        elif is_repeated:
            risk_level = "High"
            risk_type = "Repeated Service Failure"
            desc = (
                "Patient has reported the same issue on multiple occasions without resolution. "
                "Requires escalation to service improvement team."
            )
            escalate = True
        elif is_ambiguous and len(text.strip()) < 80:
            risk_level = "Medium"
            risk_type = "Ambiguous — Requires Clarification"
            desc = (
                "Feedback is vague or too brief to fully assess. "
                "Patient should be contacted to provide further details."
            )
            escalate = False
        elif sentiment == "Negative" and category in ("Communication Gap", "Scheduling Issue"):
            risk_level = "Medium"
            risk_type = "Service Quality Issue"
            desc = (
                "Negative feedback about communication or scheduling. "
                "Review and standard service recovery response recommended."
            )
            escalate = False
        elif sentiment == "Positive":
            risk_level = "Low"
            risk_type = "Positive — No Action Required"
            desc = "Patient reported a positive experience. No service recovery needed."
            escalate = False
        else:
            risk_level = "Low"
            risk_type = "General Dissatisfaction"
            desc = "General service complaint. Standard review and response recommended."
            escalate = False

        return {
            "feedback_id": feedback_id,
            "risk_level": risk_level,
            "risk_type": risk_type,
            "risk_description": desc,
            "requires_escalation": escalate,
        }


# ---------------------------------------------------------------------------
# 4. Prioritisation Agent
# ---------------------------------------------------------------------------

PRIORITY_MAP = {
    "Critical": ("P1-Critical", 95),
    "High": ("P2-High", 75),
    "Medium": ("P3-Medium", 50),
    "Low": ("P4-Low", 20),
}

DEPARTMENT_WEIGHTS = {
    "Oncology": 15,
    "Mental Health": 15,
    "Renal Unit": 12,
    "Emergency Department": 12,
    "Surgical Ward": 10,
    "Cardiology": 8,
    "Maternity": 8,
    "Neurology": 6,
}


class PrioritisationAgent:
    """
    Assigns a priority level (P1–P4) to each case using:
    - Risk level from Risk Identification Agent
    - Department criticality weights
    - Sentiment score
    - Keyword boosters (escalation requests, safety language)
    """

    NAME = "Prioritisation Agent"

    def prioritise(
        self,
        feedback_id: str,
        risk_level: str,
        department: str,
        sentiment: str,
        text: str,
        requires_escalation: bool,
    ) -> dict:
        priority_label, base_score = PRIORITY_MAP.get(risk_level, ("P4-Low", 20))
        score = float(base_score)

        # Department weight
        score += DEPARTMENT_WEIGHTS.get(department, 0)

        # Escalation boost
        if requires_escalation:
            score += 10

        # Negative sentiment boost
        if sentiment == "Negative":
            score += 5

        # Keyword boosters
        text_lower = text.lower()
        if "escalat" in text_lower:
            score += 8
        if "urgent" in text_lower or "immediately" in text_lower:
            score += 7
        if "third time" in text_lower or "fourth time" in text_lower:
            score += 6

        # Re-evaluate priority label based on final score
        if score >= 90:
            priority_label = "P1-Critical"
        elif score >= 70:
            priority_label = "P2-High"
        elif score >= 45:
            priority_label = "P3-Medium"
        else:
            priority_label = "P4-Low"

        rationale = (
            f"Base score: {base_score} (Risk: {risk_level}). "
            f"Department '{department}' weight: +{DEPARTMENT_WEIGHTS.get(department, 0)}. "
            f"Escalation flag: +{10 if requires_escalation else 0}. "
            f"Sentiment ({sentiment}): +{5 if sentiment == 'Negative' else 0}. "
            f"Final score: {int(score)}. Priority: {priority_label}."
        )

        return {
            "feedback_id": feedback_id,
            "priority_score": round(score, 1),
            "priority_level": priority_label,
            "priority_rationale": rationale,
            "assigned_department": department,
        }


# ---------------------------------------------------------------------------
# 5. Recovery Planning Agent
# ---------------------------------------------------------------------------

RECOVERY_TEMPLATES = {
    "Appointment Delay": {
        "action": (
            "Contact the patient within 48 hours to apologise for the appointment delay. "
            "Offer an expedited rescheduling slot or home visit where clinically appropriate. "
            "Review appointment management processes in the affected department."
        ),
        "role": "Patient Experience Coordinator / Department Manager",
        "follow_up": (
            "Confirm new appointment in writing within 24 hours. "
            "Follow up again after attendance to ensure satisfaction. "
            "Log incident in the service improvement register."
        ),
        "empathy": (
            "We sincerely apologise for the delay you experienced. "
            "Your time is valuable, and we understand the impact this has on your daily life and wellbeing."
        ),
        "timeline_days": 2,
    },
    "Communication Gap": {
        "action": (
            "Assign a named patient liaison to contact the patient and provide a clear, "
            "complete update on their care. Review internal communication protocols to prevent recurrence."
        ),
        "role": "Patient Liaison Officer / Clinical Lead",
        "follow_up": (
            "Provide a written care summary to the patient within 3 working days. "
            "Ensure all departments have correct and up-to-date contact details for the patient."
        ),
        "empathy": (
            "We are sorry that you did not receive the communication you deserved. "
            "Clear and timely information is fundamental to good care, and we let you down."
        ),
        "timeline_days": 3,
    },
    "Scheduling Issue": {
        "action": (
            "Investigate the scheduling error and contact the patient to confirm a new appointment. "
            "Review the booking system for technical faults or process gaps. "
            "Consider patient's access needs when rebooking."
        ),
        "role": "Appointments Team / Operations Manager",
        "follow_up": (
            "Send written confirmation of new appointment. "
            "Offer telephone booking as an alternative to the online portal. "
            "Reimburse reasonable travel costs if patient was inconvenienced."
        ),
        "empathy": (
            "We apologise for the confusion and inconvenience caused by the scheduling error. "
            "We are committed to making access to care as smooth as possible for all patients."
        ),
        "timeline_days": 2,
    },
    "Medication / Safety": {
        "action": (
            "Immediately escalate to the Clinical Governance team and Patient Safety Officer. "
            "Contact the patient to confirm their current medication status and wellbeing. "
            "Initiate a formal incident review under the hospital's safety reporting process."
        ),
        "role": "Patient Safety Officer / Clinical Governance Team",
        "follow_up": (
            "Provide the patient with a written explanation of what happened and the corrective steps taken. "
            "Complete a full root cause analysis within 14 days. "
            "Update prescribing and dispensing protocols as required."
        ),
        "empathy": (
            "We take your safety concerns extremely seriously. "
            "We are deeply sorry for any distress caused and will do everything in our power "
            "to ensure this does not happen again."
        ),
        "timeline_days": 1,
    },
    "Care Experience": {
        "action": (
            "Acknowledge the patient's feedback and, where concerns are raised, arrange a meeting "
            "with the relevant ward or department manager. "
            "Share positive feedback with the named staff members."
        ),
        "role": "Ward Manager / Patient Experience Team",
        "follow_up": (
            "If complaint: confirm in writing the steps being taken to improve care. "
            "If compliment: formally recognise the staff member and share feedback with the team."
        ),
        "empathy": (
            "Thank you for sharing your experience with us. "
            "Every piece of feedback helps us improve the care we provide to all our patients."
        ),
        "timeline_days": 5,
    },
    "Facility / Access": {
        "action": (
            "Report the specific facility or access issue to the Estates and Facilities team. "
            "Contact the patient to acknowledge the concern and provide an expected resolution timeline."
        ),
        "role": "Facilities Manager / Operations Team",
        "follow_up": (
            "Confirm resolution in writing to the patient within 7 days. "
            "Add to the facilities maintenance schedule and patient environment improvement register."
        ),
        "empathy": (
            "We are sorry that the physical environment affected your experience. "
            "All patients deserve a safe, comfortable, and accessible care environment."
        ),
        "timeline_days": 7,
    },
    "Mental Health": {
        "action": (
            "Urgently escalate to the Mental Health team lead. "
            "Arrange for a member of the patient's care team to contact them within 24 hours. "
            "Ensure any referrals in progress are confirmed and communicated clearly to the patient."
        ),
        "role": "Mental Health Team Lead / Community Mental Health Nurse",
        "follow_up": (
            "Confirm care plan status in writing. "
            "Provide the patient with crisis support contact details. "
            "Review referral and transition processes to prevent future gaps."
        ),
        "empathy": (
            "We are truly sorry for the distress caused by this delay. "
            "Your mental health is as important as any other aspect of your care, "
            "and you deserve timely and compassionate support."
        ),
        "timeline_days": 1,
    },
    "Positive Feedback": {
        "action": (
            "Share positive feedback with the relevant team and named staff. "
            "No service recovery action required. "
            "Use feedback as a good practice example in team meetings."
        ),
        "role": "Department Manager / HR Team",
        "follow_up": (
            "Send a written thank-you acknowledgement to the patient. "
            "Record positive feedback in the staff recognition system."
        ),
        "empathy": (
            "Thank you for taking the time to share your kind words. "
            "Your feedback motivates our team and means a great deal to all of us."
        ),
        "timeline_days": 7,
    },
    "General Concern": {
        "action": (
            "Assign a patient experience officer to contact the patient within 3 working days "
            "to better understand the nature of their concern and agree on appropriate next steps."
        ),
        "role": "Patient Experience Officer",
        "follow_up": (
            "Document the outcome of the contact. "
            "Escalate further if safety or health concerns are identified during follow-up."
        ),
        "empathy": (
            "Thank you for taking the time to share your experience. "
            "We are committed to understanding and addressing your concerns fully."
        ),
        "timeline_days": 3,
    },
}


class RecoveryPlanningAgent:
    """
    Generates personalised, empathetic service recovery plans based on
    category, risk level, and department. IBM Granite can enhance the
    empathy statement when available.
    """

    NAME = "Recovery Planning Agent"

    def plan(
        self,
        feedback_id: str,
        category: str,
        risk_level: str,
        department: str,
        text: str,
        summary: str,
    ) -> dict:
        template = RECOVERY_TEMPLATES.get(category, RECOVERY_TEMPLATES["General Concern"])

        empathy = template["empathy"]
        if granite.enabled:
            prompt = (
                f"Write a short, warm, and empathetic statement (2-3 sentences) to a patient "
                f"who has raised the following concern at a hospital {department} department. "
                f"Do NOT make clinical promises or offer diagnoses. "
                f"Category: {category}. Risk: {risk_level}.\n\n"
                f"Patient feedback summary: {summary}\n\nEmpathy statement:"
            )
            result = granite.generate(prompt, max_tokens=100)
            if result:
                empathy = result.strip()

        # Escalation note for P1/P2
        action = template["action"]
        if risk_level in ("Critical", "High"):
            action = "⚠️ REQUIRES IMMEDIATE ESCALATION. " + action

        return {
            "feedback_id": feedback_id,
            "recommended_action": action,
            "responsible_role": template["role"],
            "follow_up_steps": template["follow_up"],
            "empathy_statement": empathy,
            "timeline_days": template["timeline_days"],
            "status": "Pending Review",
        }


# ---------------------------------------------------------------------------
# 6. Audit & Reporting Agent
# ---------------------------------------------------------------------------

class AuditReportingAgent:
    """
    Generates a consolidated audit report from all agent outputs.
    Produces theme frequency counts, priority distributions,
    review statistics, and AI limitation disclosures.
    """

    NAME = "Audit & Reporting Agent"

    def generate_report(self, db_session) -> dict:
        from database import (
            PatientFeedback, AnalysisResult, RiskFlag,
            PriorityCase, RecoveryPlan, HumanReview
        )
        from sqlalchemy import func

        total_feedback = db_session.query(PatientFeedback).count()
        total_analysed = db_session.query(AnalysisResult).count()
        total_risks = db_session.query(RiskFlag).count()
        total_plans = db_session.query(RecoveryPlan).count()
        total_reviewed = db_session.query(HumanReview).count()

        # Category distribution
        categories = db_session.query(
            AnalysisResult.category, func.count(AnalysisResult.id)
        ).group_by(AnalysisResult.category).all()

        # Priority distribution
        priorities = db_session.query(
            PriorityCase.priority_level, func.count(PriorityCase.id)
        ).group_by(PriorityCase.priority_level).all()

        # Sentiment distribution
        sentiments = db_session.query(
            AnalysisResult.sentiment, func.count(AnalysisResult.id)
        ).group_by(AnalysisResult.sentiment).all()

        # Review decisions
        decisions = db_session.query(
            HumanReview.decision, func.count(HumanReview.id)
        ).group_by(HumanReview.decision).all()

        # Escalations
        escalations = db_session.query(RiskFlag).filter(
            RiskFlag.requires_escalation == True
        ).count()

        # Data quality
        duplicates = db_session.query(PatientFeedback).filter(
            PatientFeedback.is_duplicate == True
        ).count()
        missing = db_session.query(PatientFeedback).filter(
            PatientFeedback.has_missing_fields == True
        ).count()

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_feedback_records": total_feedback,
                "records_analysed": total_analysed,
                "risk_flags_raised": total_risks,
                "recovery_plans_generated": total_plans,
                "cases_reviewed_by_human": total_reviewed,
                "cases_requiring_escalation": escalations,
                "duplicate_records": duplicates,
                "records_with_missing_fields": missing,
            },
            "theme_distribution": {cat: count for cat, count in categories},
            "priority_distribution": {pri: count for pri, count in priorities},
            "sentiment_distribution": {sent: count for sent, count in sentiments},
            "review_decisions": {dec: count for dec, count in decisions},
            "ai_limitations": [
                "All classifications are based on keyword matching and rule-based logic.",
                "IBM Granite AI is used for enhanced summaries and empathy statements when credentials are configured.",
                "No clinical diagnosis or medical urgency determination is made by any agent.",
                "All safety-flagged cases require review by a qualified clinical or patient safety professional.",
                "Confidence scores are indicative and should not be used as the sole basis for decision-making.",
                "All personally identifiable information has been removed from the dataset prior to processing.",
                "Human approval is required before any recovery action is communicated to a patient.",
            ],
            "responsible_ai_statement": (
                "This system is designed to assist — not replace — human judgement. "
                "All AI-generated outputs are subject to human review and approval. "
                "The system does not make clinical decisions. "
                "Privacy of patient information is protected at every stage."
            ),
        }
