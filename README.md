# 🌸 IVF Care Platform

> An AI-powered IVF care coordination platform — combining a conversational advisor with a multi-agent system to coordinate the full IVF journey for patients, nurses, and doctors.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-IVF%20Advisor-purple?style=for-the-badge)](https://ivf-advisor-100876575377.us-central1.run.app)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-blue?style=for-the-badge)](https://task-manager-api-100876575377.us-central1.run.app/docs)
[![Built on GCP](https://img.shields.io/badge/Built%20on-Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud)](https://cloud.google.com)

---

## 🎯 Problem Statement

IVF patients face:
- **Daily injections** requiring nurse home visits — hard to coordinate manually
- **Time-critical medications** (trigger shots) where missing a dose can cancel a cycle
- **Opaque costs** — patients are often overcharged with no way to verify
- **Fragmented information** — appointments, test results, medications tracked in different places

**IVF Care Platform** solves this with a single AI-powered interface.

---

## 🏗️ System Architecture

flowchart TD
    %% 1. Nodes & Decision
    Start([Start]) --> Chat[[Chat with AI Advisor]]
    Chat --> Q1{What does<br/>patient need?}

    %% 2. The Agent Layer
    Q1 -->|Clinical| Evidence[Evidence Search]
    Q1 -->|Booking| Appt[Appointment Agent]
    Q1 -->|Nursing| Nurse[Nurse Agent]
    Q1 -->|Medicine| Remind[Reminder Agent]
    Q1 -->|Costs| Cost[Cost Agent]
    Q1 -->|Schedule| Schedule[View Schedule]

    %% 3. Data & Storage
    Evidence & Appt & Nurse & Remind & Cost & Schedule --> AlloyDB[(AlloyDB)]
    AlloyDB --> Response[/Grounded Response/]

    %% 4. Communications
    Appt --> Email1[Appt Email]
    Nurse --> Email2[Nurse Email]
    Remind --> Email3[Remind Email]
    Email1 & Email2 & Email3 --> Calendar[Google Calendar]

    %% 5. GitHub-Optimized Classes
    classDef blue fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef yellow fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef purple fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef teal fill:#e0f2f1,stroke:#00695c,stroke-width:2px;
    classDef green fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px;
    classDef db fill:#01579b,stroke:#01579b,color:#fff;

    class Chat blue;
    class Q1 yellow;
    class Evidence,Appt,Nurse,Remind,Cost purple;
    class Schedule teal;
    class Response green;
    class AlloyDB db;
---

## 🏥 IVF Cycle Stage Tracking

```mermaid
stateDiagram-v2
    [*] --> Baseline: Cycle starts

    Baseline --> Stimulation: Day 1 injections begin
    note right of Stimulation
        Daily nurse visits
        Medication reminders
        Monitoring scans
    end note

    Stimulation --> Trigger: Follicles ready
    note right of Trigger
        ⚠️ CRITICAL reminder
        Exact time injection
        Nurse visit booked
    end note

    Trigger --> Retrieval: 36 hours later
    note right of Retrieval
        Hospital appointment
        Post-retrieval pathology
    end note

    Retrieval --> Fertilisation: Lab updates Day 1,3,5
    Fertilisation --> Transfer: Embryo transfer
    note right of Transfer
        Hospital appointment
        Full bladder required
    end note

    Transfer --> LutealSupport: Progesterone support
    LutealSupport --> PregnancyTest: 14 days later
    PregnancyTest --> [*]: Beta HCG result
```

---

## 👥 Use Case Diagram

```mermaid
graph LR
    subgraph Actors
        P[👤 Patient]
        N[👩‍⚕️ Nurse]
        D[👨‍⚕️ Doctor]
    end

    subgraph UseCases["IVF Care Platform — Use Cases"]
        UC1[Ask IVF questions]
        UC2[Book appointment]
        UC3[Book nurse home visit]
        UC4[Set medication reminder]
        UC5[Track IVF cycle stage]
        UC6[View cost breakdown]
        UC7[Audit medical bill]
        UC8[Search medical records]
        UC9[Receive calendar invite]
        UC10[Confirm nurse visit]
        UC11[View patient schedule]
        UC12[Order pathology tests]
    end

    P --> UC1
    P --> UC2
    P --> UC3
    P --> UC4
    P --> UC5
    P --> UC6
    P --> UC7
    P --> UC8
    P --> UC9

    N --> UC10
    N --> UC9
    N --> UC3

    D --> UC11
    D --> UC12
    D --> UC2
    D --> UC9
```

---

## 🤖 Multi-Agent Coordination Example

> **Patient says:** *"Book a nurse for my trigger shot tonight at 11:30pm"*

```mermaid
sequenceDiagram
    participant P as 👤 Patient
    participant A as 🤖 IVF Advisor
    participant O as ⚙️ Orchestrator
    participant N as 🏠 NurseSubAgent
    participant C as 📅 CalendarSubAgent
    participant R as ⏰ ReminderSubAgent
    participant M as 💊 MedicationSubAgent
    participant CG as 💰 CostGuardSubAgent
    participant DB as 🗄️ AlloyDB
    participant E as 📧 Email

    P->>A: "Book nurse for trigger shot at 11:30pm"
    A->>O: submit_workflow("book nurse trigger shot 11:30pm")
    O->>N: book_nurse_visit(patient_id, 23:30)
    N->>DB: Create NurseVisit record
    N->>E: Notify nurse (visit details + dose)
    N-->>O: nurse_visit_id

    O->>C: create_event("Trigger Shot — Nurse Visit", 23:30)
    C->>DB: Create Event record
    C-->>O: event_id

    O->>R: schedule_reminder(criticality=CRITICAL, time=23:15)
    R->>DB: Create Reminder record
    R->>E: Send .ics email to patient + nurse
    R-->>O: reminder_id

    O->>M: record_administration(nurse_visit_id)
    M->>DB: Create MedicationAdministration record

    O->>CG: track_cost(category=nurse_visit)
    CG->>DB: Create CostRecord

    O-->>A: Workflow completed
    A-->>P: "✅ Nurse booked for 11:30pm. Critical reminder set for 11:15pm. Calendar invite sent."
```

---

## 💰 Cost Protection Flow

```mermaid
flowchart LR
    Quote[Clinic quotes\nGonal-F: ₹8,500] --> Benchmark{Compare vs\nmarket benchmark\n₹6,200}

    Benchmark -->|>15% over| Alert[🚨 Price Alert\nOvercharged by 37%\nSuggested: ₹6,200]
    Benchmark -->|Within 15%| OK[✅ Fair price]

    Alert --> Patient[Patient informed\nbefore paying]
    OK --> Record[Cost recorded\nin AlloyDB]
    Patient --> Record

    Record --> Summary[Monthly cost\nsummary by category]
    Summary --> Insurance[Insurance claim\nsummary generated]
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | Google ADK |
| LLM | Gemini 2.5 Flash Lite (Vertex AI) |
| Chat UI | Gradio |
| REST API | FastAPI |
| Database | AlloyDB PostgreSQL |
| Vector Search | AlloyDB pgvector + text-embedding-004 |
| Evidence Search | Vertex AI Search |
| Deployment | Cloud Run (GCP) |
| CI/CD | Cloud Build |
| Secrets | Secret Manager |
| Email + Calendar | Gmail SMTP + .ics attachments |

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/khaiwalVikrant/ivf-care-platform.git
cd ivf-care-platform

# Install
pip install -e .

# Configure
cp .env.example .env
# Fill in GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT, VERTEX_SEARCH_DATASTORE_ID

# Run IVF Advisor UI
python -m ivf_advisor.ui

# Run Task Manager API (separate terminal)
python -m task_manager.main

# Run tests
pytest tests/ -v
```

---

## 📁 Project Structure

```
ivf-care-platform/
├── ivf_advisor/              # Conversational IVF advisor
│   ├── agent.py              # ADK agent + all tools
│   ├── orchestrator.py       # Session management
│   ├── ui.py                 # Gradio chat UI
│   └── tools/                # 7 tools including task_manager_client
├── task_manager/             # Multi-agent coordination platform
│   ├── agents/               # 9 specialized sub-agents
│   ├── api/app.py            # 20+ REST endpoints
│   ├── db/                   # AlloyDB facade + vector search
│   └── orchestrator.py       # Workflow engine with rollback
├── tests/
│   ├── unit/                 # 86 unit tests
│   └── property/             # Hypothesis property-based tests
├── Dockerfile.task_manager
├── ivf_advisor/Dockerfile
└── cloudbuild.yaml           # Parallel CI/CD pipeline
```

---

## 📄 License

MIT
