# 🌸 IVF Care Platform

An AI-powered IVF care coordination platform built on Google ADK, FastAPI, and AlloyDB. It combines a conversational IVF advisor with a multi-agent task management system to help patients, nurses, and doctors coordinate the full IVF journey.

## Live Services

| Service | URL |
|---|---|
| IVF Advisor Chat UI | https://ivf-advisor-100876575377.us-central1.run.app |
| Task Manager API | https://task-manager-api-100876575377.us-central1.run.app |
| API Documentation | https://task-manager-api-100876575377.us-central1.run.app/docs |

## Architecture

```
Patient (Gradio UI)
    │
    ▼
IVF Advisor Agent (Google ADK + Gemini)
    │
    ├── Evidence Search (Vertex AI Search)
    ├── Cost Breakdown Tool
    ├── Journey Guide Tool
    └── Task Manager Client
            │
            ▼
    Task Manager API (FastAPI + AlloyDB)
            │
    ┌───────┼───────────────────────────┐
    │       │                           │
TaskAgent  CalendarAgent  AppointmentAgent
NurseAgent ReminderAgent  PathologyAgent
MedicationAgent CostGuardAgent NotesAgent
```

## Features

### IVF Advisor Chat
- Natural language IVF guidance grounded in clinical evidence
- Scope-guarded responses (stays within IVF/fertility domain)
- India-specific cost breakdowns (INR)

### Care Coordination (via Task Manager API)
- **Appointments** — book consultations, ultrasounds, egg retrieval, embryo transfer with pre-appointment checklists
- **Nurse Home Visits** — arrange nurse visits for daily injections with auto-assignment
- **Medication Management** — track schedules, dose adjustments, administration history
- **Reminders** — time-critical alerts with 15-minute escalation for trigger shots
- **Pathology** — order tests, track results, flag abnormal values
- **Cost Protection** — price benchmarking against market rates, bill audit, insurance summaries
- **IVF Cycle Tracking** — 8-stage lifecycle from baseline to pregnancy test

### Notifications
- Email confirmations with `.ics` calendar attachments (works with Google Calendar, Apple Calendar, Outlook)
- Google Calendar integration via service account

### AI-Powered Search
- AlloyDB vector search using `text-embedding-004` for semantic note and pathology result retrieval

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | Google ADK |
| LLM | Gemini 2.5 Flash Lite (Vertex AI) |
| Chat UI | Gradio |
| REST API | FastAPI |
| Database | AlloyDB PostgreSQL (prod) / SQLite (dev) |
| Vector Search | AlloyDB pgvector + text-embedding-004 |
| Evidence Search | Vertex AI Search |
| Deployment | Cloud Run (GCP) |
| CI/CD | Cloud Build |
| Secrets | Secret Manager |
| Calendar | Google Calendar API |
| Email | Gmail SMTP with .ics attachments |

## Project Structure

```
ivf-care-platform/
├── ivf_advisor/              # Conversational IVF advisor (Gradio UI + ADK agent)
│   ├── agent.py              # ADK agent with all tools registered
│   ├── orchestrator.py       # Session management and ADK runner
│   ├── ui.py                 # Gradio chat interface
│   ├── tools/
│   │   ├── evidence_search.py
│   │   ├── cost_breakdown.py
│   │   ├── journey_guide.py
│   │   ├── scope_guard.py
│   │   ├── task_manager_client.py  # Connects to Task Manager API
│   │   ├── google_calendar.py
│   │   └── email_notifications.py
│   └── Dockerfile
├── task_manager/             # Multi-agent task management system
│   ├── agents/               # 9 sub-agents
│   ├── api/app.py            # FastAPI endpoints
│   ├── db/database.py        # AlloyDB/SQLite facade
│   ├── db/vector_search.py   # pgvector semantic search
│   ├── orchestrator.py       # Workflow orchestration
│   └── main.py
├── tests/
│   ├── unit/                 # Unit tests for all agents
│   └── property/             # Hypothesis property-based tests
├── Dockerfile.task_manager
├── cloudbuild.yaml           # CI/CD pipeline
└── pyproject.toml
```

## Local Development

```bash
# Install dependencies
pip install -e .

# Copy env template
cp .env.example .env
# Fill in GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT, VERTEX_SEARCH_DATASTORE_ID

# Run IVF Advisor UI
python -m ivf_advisor.ui

# Run Task Manager API
python -m task_manager.main

# Run tests
pytest tests/ -v
```

## GCP Deployment

The project deploys automatically via Cloud Build on every push to `main`.

### Required Secrets (Secret Manager)

| Secret Name | Description |
|---|---|
| `task-manager-secret-key` | API bearer token for Task Manager |
| `task-manager-db-password` | AlloyDB password |
| `notification-email` | Sender Gmail address |
| `notification-email-password` | Gmail app password |
| `ivf-agent-api-key` | Google API key |

### Manual Deploy

```bash
gcloud builds submit --config cloudbuild.yaml . --project=ivf-agent
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/requests` | Submit natural language request |
| GET | `/workflows/{id}` | Check workflow status |
| GET/POST | `/tasks` | List/create tasks |
| GET/POST | `/appointments` | List/book appointments |
| POST | `/pathology/orders` | Order tests |
| GET | `/pathology/results` | Get test results |
| GET | `/pathology/semantic-search` | AI-powered test result search |
| POST | `/medications/schedules` | Create medication schedule |
| POST | `/nurse-visits` | Book nurse home visit |
| POST | `/reminders` | Schedule reminder |
| GET | `/reminders` | List reminders |
| GET | `/cycles/{id}/summary` | Full IVF cycle summary |
| GET | `/costs/summary` | Cycle cost breakdown |
| POST | `/costs/audit` | Audit a bill |
| GET | `/costs/insurance-summary` | Insurance claim summary |
| GET | `/notes/semantic-search` | AI-powered notes search |

## License

MIT
