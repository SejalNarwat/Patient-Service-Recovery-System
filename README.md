# 🏥 Patient Service Recovery System

> **Agentic AI-Based Patient Service Recovery System**  
> Built with **IBM Bob** · Powered by **IBM Granite** (optional) · Python + FastAPI + SQLite + HTML/CSS/JS

---

## 📋 Project Overview

This is a fully functional **Agentic AI prototype** that analyses de-identified patient feedback using a multi-agent workflow. It classifies complaints, identifies risks, prioritises cases, generates recovery plans, and enforces human approval before any action is taken.

### Architecture

```
Patient Feedback (40 Synthetic Records)
        ↓
[1] Data Preparation Agent     → Quality flags, duplicate detection
        ↓
[2] Feedback Analysis Agent    → Category, sentiment, themes, summary (IBM Granite enhanced)
        ↓
[3] Risk Identification Agent  → Critical / High / Medium / Low risk flags
        ↓
[4] Prioritisation Agent       → P1–P4 priority scores with transparent rationale
        ↓
[5] Recovery Planning Agent    → Empathetic action plans (IBM Granite enhanced)
        ↓
[6] Human Review (HITL)        → ✅ Human approval required before any action
        ↓
[7] Audit & Reporting Agent    → Consolidated report + audit trail
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Start the application

```bash
python main.py
```

Or with auto-reload for development:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 3 — Open the dashboard

Open your browser and go to:

```
http://127.0.0.1:8000
```

### Step 4 — Run the pipeline

1. Click **"Run Pipeline"** in the sidebar
2. Click the **"▶ Run Full Pipeline"** button
3. All 40 synthetic patient feedback records will be processed through all 5 AI agents
4. Navigate to each section to explore results

### Step 5 — Review cases

1. Go to **"Human Review"** in the sidebar
2. Click **"Review"** next to any pending case
3. Enter your name, select a decision (Approve / Reject / Modify), add notes
4. Submit — the plan status updates immediately

---

## 🤖 IBM Granite Integration (Optional)

The system works fully without IBM Granite using built-in rule-based AI logic.

To enable IBM Granite for enhanced summaries and empathy statements:

1. Edit `config.env` with your credentials:
```env
IBM_API_KEY=your_actual_ibm_cloud_api_key
IBM_ML_URL=https://us-south.ml.cloud.ibm.com
IBM_PROJECT_ID=your_watson_ml_project_id
```

2. Load the config before starting:
```bash
# Windows PowerShell
Get-Content config.env | ForEach-Object { if ($_ -match '^([^#][^=]*)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2]) } }
python main.py

# Linux/Mac
export $(cat config.env | grep -v '^#' | xargs)
python main.py
```

When Granite is active, the dashboard shows a green **IBM Granite: Active** indicator.

---

## 📁 Project Structure

```
P1-Patient Service Recovery System/
├── main.py              ← FastAPI backend, all API routes
├── agents.py            ← All 7 AI agents
├── database.py          ← SQLite models (SQLAlchemy)
├── synthetic_data.py    ← 40 de-identified patient feedback records
├── requirements.txt     ← Python dependencies
├── config.env           ← IBM credentials (optional)
├── static/
│   └── index.html       ← Complete frontend dashboard
└── patient_recovery.db  ← SQLite database (auto-created on first run)
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pipeline/run` | Run the full multi-agent pipeline |
| `GET`  | `/api/feedback` | All feedback records |
| `GET`  | `/api/feedback/{id}` | Full case file for one record |
| `GET`  | `/api/analysis` | All analysis results |
| `GET`  | `/api/risks` | All risk flags |
| `GET`  | `/api/priorities` | Priority cases (sorted by score) |
| `GET`  | `/api/recovery` | All recovery plans |
| `POST` | `/api/review/{id}` | Submit human review decision |
| `GET`  | `/api/reviews` | All completed reviews |
| `GET`  | `/api/report` | Consolidated audit report |
| `GET`  | `/api/dashboard` | Dashboard statistics |
| `GET`  | `/api/audit` | Audit trail log |
| `DELETE` | `/api/reset` | Reset database (dev only) |

Interactive API docs (Swagger UI): `http://127.0.0.1:8000/docs`

---

## 🧪 Testing the System

### Automated test
```bash
python test_system.py
```

### Manual testing checklist

- [ ] Run pipeline — check 40 records are processed
- [ ] Dashboard shows correct stats and charts
- [ ] Risk flags include Critical cases (PF-2024-022 allergy error)
- [ ] Priority P1-Critical cases appear at the top
- [ ] Recovery plans have empathy statements and follow-up steps
- [ ] Human review: approve PF-2024-001, reject PF-2024-031, modify PF-2024-038
- [ ] Audit trail shows all agent actions
- [ ] Report shows theme and priority distributions
- [ ] Reset database and re-run pipeline

---

## ⚠️ Important Guardrails

1. **No clinical decisions** — Agents do not diagnose patients or determine medical urgency
2. **Human approval required** — All recovery plans need human sign-off before action
3. **De-identified data only** — All 40 records use synthetic, de-identified information
4. **Escalation protocol** — Critical/High risks flag for authorised personnel review
5. **Audit trail** — Every agent action is logged with timestamp and details
6. **Responsible AI** — The report includes AI limitations and a responsible AI statement

---

## 📊 Sample Results (Expected After Pipeline Run)

| Category | Expected Count |
|----------|---------------|
| Appointment Delay | ~8 |
| Communication Gap | ~7 |
| Care Experience | ~7 |
| Scheduling Issue | ~5 |
| Medication / Safety | ~4 |
| Mental Health | ~3 |
| Positive Feedback | ~3 |
| Facility / Access | ~3 |

| Priority | Expected Count |
|----------|---------------|
| P1-Critical | ~4 |
| P2-High | ~10 |
| P3-Medium | ~16 |
| P4-Low | ~10 |

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.10+, FastAPI |
| Database | SQLite (via SQLAlchemy) |
| Frontend | Vanilla HTML5, CSS3, JavaScript |
| AI Agents | Rule-based NLP + IBM Granite (optional) |
| IBM Tools | IBM Bob (development), IBM Granite 13B |

---

## 📝 Notes for Students

- The system runs **entirely offline** without any IBM credentials
- IBM Granite enhances output quality but is not required for full functionality
- The `synthetic_data.py` file contains 40 carefully crafted patient scenarios
- Each agent in `agents.py` is clearly commented and self-contained
- The `database.py` file shows simple SQLAlchemy ORM patterns
- The frontend uses no external libraries — pure HTML/CSS/JS

---

*Built with IBM Bob · Patient Service Recovery System · Educational Project*
