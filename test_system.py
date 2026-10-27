"""
Automated test suite for the Patient Service Recovery System.
Tests all API endpoints and validates the multi-agent pipeline output.

Run with: python test_system.py
(Make sure the server is running: python main.py)
"""

import sys
import json
import time
import requests

BASE = "http://127.0.0.1:8000"
PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((label, condition, detail))
    print(f"  {status}  {label}" + (f"  [{detail}]" if detail else ""))
    return condition


def test(section):
    print(f"\n{'='*60}")
    print(f"  {section}")
    print(f"{'='*60}")


# ============================================================
# 1. Server Health
# ============================================================
test("1. Server Health Check")
try:
    r = requests.get(BASE + "/", timeout=5)
    check("Frontend serves HTML", r.status_code == 200 and "Patient" in r.text, f"Status {r.status_code}")
except Exception as e:
    check("Server is reachable", False, str(e))
    print("\n❌ Server not running. Start it with: python main.py")
    sys.exit(1)

# ============================================================
# 2. Database Reset
# ============================================================
test("2. Database Reset")
r = requests.delete(BASE + "/api/reset")
check("Database reset succeeds", r.status_code == 200, r.json().get("status", ""))

# ============================================================
# 3. Empty State Checks
# ============================================================
test("3. Empty State (before pipeline)")
r = requests.get(BASE + "/api/feedback")
check("Feedback list is empty", r.status_code == 200 and len(r.json()) == 0, f"{len(r.json())} records")

r = requests.get(BASE + "/api/dashboard")
check("Dashboard responds when empty", r.status_code == 200)
data = r.json()
check("Total feedback is 0", data["total_feedback"] == 0, str(data["total_feedback"]))

# ============================================================
# 4. Pipeline Execution
# ============================================================
test("4. Pipeline Execution")
r = requests.post(BASE + "/api/pipeline/run", timeout=60)
check("Pipeline returns 200", r.status_code == 200)
data = r.json()
check("Pipeline status is success", data.get("status") == "success", data.get("status"))
check("40 records processed", data.get("processed") == 40, f"{data.get('processed')} processed")
check("0 records skipped (first run)", data.get("skipped") == 0, f"{data.get('skipped')} skipped")
print(f"    IBM Granite: {'Active' if data.get('granite_enabled') else 'Offline (built-in logic)'}")

# ============================================================
# 5. Idempotency Check
# ============================================================
test("5. Pipeline Idempotency")
r = requests.post(BASE + "/api/pipeline/run", timeout=60)
data = r.json()
check("Re-run skips existing records", data.get("skipped") == 40, f"{data.get('skipped')} skipped")
check("Re-run processes 0 new records", data.get("processed") == 0, f"{data.get('processed')} processed")

# ============================================================
# 6. Feedback Endpoint
# ============================================================
test("6. Feedback Records")
r = requests.get(BASE + "/api/feedback")
feedback = r.json()
check("40 feedback records returned", len(feedback) == 40, f"{len(feedback)} records")

# Check specific records exist
ids = [f["feedback_id"] for f in feedback]
check("PF-2024-001 present", "PF-2024-001" in ids)
check("PF-2024-040 present (incomplete record)", "PF-2024-040" in ids)

# Check data quality flags
rec_040 = next((f for f in feedback if f["feedback_id"] == "PF-2024-040"), None)
if rec_040:
    check("PF-2024-040 flagged as incomplete", rec_040["has_missing_fields"] == True)
    check("PF-2024-040 has quality notes", "Missing" in rec_040["data_quality_notes"])

# ============================================================
# 7. Analysis Results
# ============================================================
test("7. Feedback Analysis Agent")
r = requests.get(BASE + "/api/analysis")
analysis = r.json()
check("40 analysis records", len(analysis) == 40, f"{len(analysis)} records")

# Verify categories are populated
cats = set(a["category"] for a in analysis)
check("Multiple categories detected", len(cats) >= 5, f"{len(cats)} categories: {', '.join(sorted(cats))}")
check("Appointment Delay detected", "Appointment Delay" in cats)
check("Communication Gap detected", "Communication Gap" in cats)

# Verify sentiments
sents = set(a["sentiment"] for a in analysis)
check("Multiple sentiments detected", len(sents) >= 2, f"Sentiments: {', '.join(sents)}")

# Verify specific case
pf001 = next((a for a in analysis if a["feedback_id"] == "PF-2024-001"), None)
if pf001:
    check("PF-2024-001 classified as Appointment Delay", pf001["category"] == "Appointment Delay", pf001["category"])
    check("PF-2024-001 sentiment is Negative", pf001["sentiment"] == "Negative", pf001["sentiment"])
    check("PF-2024-001 has a summary", bool(pf001["summary"]))
    check("PF-2024-001 confidence > 0.5", (pf001["confidence_score"] or 0) > 0.5, str(pf001["confidence_score"]))

# ============================================================
# 8. Risk Flags
# ============================================================
test("8. Risk Identification Agent")
r = requests.get(BASE + "/api/risks")
risks = r.json()
check("40 risk records", len(risks) == 40, f"{len(risks)} records")

risk_levels = [r["risk_level"] for r in risks]
check("Critical risks found", "Critical" in risk_levels, f"Critical: {risk_levels.count('Critical')}")
check("High risks found", "High" in risk_levels, f"High: {risk_levels.count('High')}")
check("Low risks found (positive feedback)", "Low" in risk_levels, f"Low: {risk_levels.count('Low')}")

# Medication safety case should be Critical
pf022 = next((r for r in risks if r["feedback_id"] == "PF-2024-022"), None)
if pf022:
    check("PF-2024-022 (allergy/penicillin) is Critical", pf022["risk_level"] == "Critical", pf022["risk_level"])
    check("PF-2024-022 requires escalation", pf022["requires_escalation"] == True)

escalations = [r for r in risks if r["requires_escalation"]]
check("At least 5 escalations required", len(escalations) >= 5, f"{len(escalations)} escalations")

# ============================================================
# 9. Priority Cases
# ============================================================
test("9. Prioritisation Agent")
r = requests.get(BASE + "/api/priorities")
priorities = r.json()
check("40 priority records", len(priorities) == 40, f"{len(priorities)} records")

# Should be sorted by score
scores = [p["priority_score"] for p in priorities]
check("Priorities sorted descending", scores == sorted(scores, reverse=True), "Score order")

pri_levels = [p["priority_level"] for p in priorities]
check("P1-Critical cases exist", "P1-Critical" in pri_levels, f"P1: {pri_levels.count('P1-Critical')}")
check("P4-Low cases exist", "P4-Low" in pri_levels, f"P4: {pri_levels.count('P4-Low')}")

# All have rationale
with_rationale = [p for p in priorities if p["priority_rationale"]]
check("All cases have rationale", len(with_rationale) == 40, f"{len(with_rationale)}/40 with rationale")

# ============================================================
# 10. Recovery Plans
# ============================================================
test("10. Recovery Planning Agent")
r = requests.get(BASE + "/api/recovery")
plans = r.json()
check("40 recovery plans", len(plans) == 40, f"{len(plans)} plans")

all_pending = all(p["status"] == "Pending Review" for p in plans)
check("All plans start as Pending Review", all_pending)

with_empathy = [p for p in plans if p["empathy_statement"]]
check("All plans have empathy statements", len(with_empathy) == 40, f"{len(with_empathy)}/40")

with_action = [p for p in plans if p["recommended_action"]]
check("All plans have recommended actions", len(with_action) == 40, f"{len(with_action)}/40")

# ============================================================
# 11. Case Detail Endpoint
# ============================================================
test("11. Case Detail Endpoint")
r = requests.get(BASE + "/api/feedback/PF-2024-022")
check("Case detail returns 200", r.status_code == 200)
case = r.json()
check("Case has feedback section", "feedback" in case)
check("Case has analysis section", "analysis" in case and case["analysis"] is not None)
check("Case has risk section", "risk" in case and case["risk"] is not None)
check("Case has priority section", "priority" in case and case["priority"] is not None)
check("Case has recovery plan", "recovery_plan" in case and case["recovery_plan"] is not None)

r404 = requests.get(BASE + "/api/feedback/PF-9999-999")
check("Unknown ID returns 404", r404.status_code == 404)

# ============================================================
# 12. Human Review (HITL)
# ============================================================
test("12. Human Review (Human-in-the-Loop)")

# Approve a case
r = requests.post(BASE + "/api/review/PF-2024-001", json={
    "reviewer_name": "Dr. Sarah Johnson",
    "decision": "Approved",
    "reviewer_notes": "Verified delay occurred. Action plan is appropriate.",
    "modified_action": "",
})
check("Approve PF-2024-001 succeeds", r.status_code == 200)
data = r.json()
check("Response confirms Approved", data.get("decision") == "Approved", data.get("decision"))

# Reject a case
r = requests.post(BASE + "/api/review/PF-2024-031", json={
    "reviewer_name": "Dr. Sarah Johnson",
    "decision": "Rejected",
    "reviewer_notes": "Feedback too vague to action without more information.",
})
check("Reject PF-2024-031 succeeds", r.status_code == 200)

# Modify a case
r = requests.post(BASE + "/api/review/PF-2024-038", json={
    "reviewer_name": "Mr. James Patel",
    "decision": "Modified",
    "reviewer_notes": "Triage review conducted. Additional safeguards added.",
    "modified_action": "Initiate a formal triage process review. Schedule debrief with A&E team lead. Contact patient to provide explanation and apology within 24 hours.",
})
check("Modify PF-2024-038 succeeds", r.status_code == 200)

# Invalid decision
r = requests.post(BASE + "/api/review/PF-2024-002", json={
    "reviewer_name": "Test",
    "decision": "InvalidDecision",
})
check("Invalid decision returns 400", r.status_code == 400)

# List reviews
r = requests.get(BASE + "/api/reviews")
reviews = r.json()
check("3 reviews recorded", len(reviews) == 3, f"{len(reviews)} reviews")

decisions = {rv["feedback_id"]: rv["decision"] for rv in reviews}
check("PF-2024-001 decision is Approved", decisions.get("PF-2024-001") == "Approved")
check("PF-2024-031 decision is Rejected", decisions.get("PF-2024-031") == "Rejected")
check("PF-2024-038 decision is Modified", decisions.get("PF-2024-038") == "Modified")

# Verify recovery plan status updated
r = requests.get(BASE + "/api/feedback/PF-2024-001")
case = r.json()
check("PF-2024-001 plan status is Approved", case["recovery_plan"]["status"] == "Approved")

# ============================================================
# 13. Dashboard Statistics
# ============================================================
test("13. Dashboard Statistics")
r = requests.get(BASE + "/api/dashboard")
data = r.json()
check("40 total feedback", data["total_feedback"] == 40)
check("40 analysed", data["records_analysed"] == 40)
check("3 approved plans", data["approved_plans"] == 3, str(data["approved_plans"]))
check("37 pending review", data["pending_review"] == 37, str(data["pending_review"]))
check("Risk counts present", all(k in data["risk_counts"] for k in ["Critical","High","Medium","Low"]))
check("Sentiment counts present", all(k in data["sentiment_counts"] for k in ["Negative","Positive","Neutral"]))

# ============================================================
# 14. Audit Report
# ============================================================
test("14. Audit & Reporting Agent")
r = requests.get(BASE + "/api/report")
report = r.json()
check("Report has summary", "summary" in report)
check("Report has theme distribution", "theme_distribution" in report and len(report["theme_distribution"]) > 0)
check("Report has priority distribution", "priority_distribution" in report)
check("Report has AI limitations", "ai_limitations" in report and len(report["ai_limitations"]) >= 5)
check("Report has responsible AI statement", bool(report.get("responsible_ai_statement")))
check("Report records 3 reviews", report["summary"]["cases_reviewed_by_human"] == 3)

# ============================================================
# 15. Audit Trail
# ============================================================
test("15. Audit Trail")
r = requests.get(BASE + "/api/audit")
logs = r.json()
check("Audit trail has entries", len(logs) > 0, f"{len(logs)} entries")
check("Audit covers all agents", len(set(l["agent_name"] for l in logs)) >= 5)

# ============================================================
# Summary
# ============================================================
print(f"\n{'='*60}")
print(f"  TEST SUMMARY")
print(f"{'='*60}")
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
total = len(results)
print(f"\n  Total:  {total}")
print(f"  Passed: {passed} ✅")
print(f"  Failed: {failed} ❌")

if failed > 0:
    print("\n  Failed tests:")
    for label, ok, detail in results:
        if not ok:
            print(f"    ❌ {label}" + (f" [{detail}]" if detail else ""))

print()
if failed == 0:
    print("  🎉 ALL TESTS PASSED! System is fully functional.")
else:
    print(f"  ⚠️  {failed} test(s) failed. Check output above.")
print()
