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

```mermaid
graph TB
    subgraph Patient["👤 Patient Interface"]
        UI[Gradio Chat UI]
    end

    subgraph Advisor["🤖 IVF Advisor Agent (Google ADK)"]
        Agent[Gemini 2.5 Flash Lite]
        Tools["Tools: Evidence Search\nCost Breakdown\nJourney Guide\nScope Guard"]
    end

    subgraph Platform["⚙️ Task Manager Platform (FastAPI)"]
        Orch[Orchestrator]
        subgraph Agents["9 Specialized Sub-Agents"]
            A1[Task Manager]
            A2[Calendar]
            A3[Appointment]
            A4[Nurse Coordinator]
            A5[Medication]
            A6[Pathology]
            A7[Reminder]
            A8[Cost Guard]
            A9[Notes]
        end
    end

    subgraph Data["🗄️ Data Layer"]
        DB[(AlloyDB PostgreSQL)]
        VS[pgvector\nSemantic Search]
        VAI[Vertex AI Search\nResearch Papers]
    end

    subgraph Notify["📬 Notifications"]
        Email[Gmail SMTP\n+ .ics Calendar]
        GCal[Google Calendar]
    end

    UI --> Agent
    Agent --> Tools
    Agent --> Orch
    Orch --> Agents
    Agents --> DB
    DB --> VS
    Tools --> VAI
    Agents --> Email
    Agents --> GCal
```

---

## 🔄 Patient Journey Flow

```mermaid
flowchart TD
    Start([Patient opens IVF Care Platform]) --> Chat[Chat with AI Advisor]

    Chat --> Q1{What does patient need?}

    Q1 -->|Clinical question| Evidence[Evidence Search\nVertex AI Search]
    Q1 -->|Book appointment| Appt[AppointmentSubAgent\nBook + Checklist + Email .ics]
    Q1 -->|Nurse home visit| Nurse[NurseSubAgent\nAssign Nurse + Notify + Calendar]
    Q1 -->|Set medication reminder| Remind[ReminderSubAgent\nSave to AlloyDB + Email .ics]
    Q1 -->|Cost question| Cost[CostGuardSubAgent\nBenchmark + Breakdown]
    Q1 -->|View schedule| Schedule[Query AlloyDB\nTasks + Events + Reminders]

    Evidence --> Response[Agent responds with\ngrounded answer]
    Appt --> AlloyDB1[(AlloyDB)]
    Appt --> EmailAppt[📧 Confirmation email\nwith .ics attachment]
    Nurse --> AlloyDB2[(AlloyDB)]
    Nurse --> EmailNurse[📧 Notify patient + nurse\nwith .ics]
    Remind --> AlloyDB3[(AlloyDB)]
    Remind --> EmailRemind[📧 Reminder email\nwith .ics]
    Cost --> AlloyDB4[(AlloyDB)]
    Schedule --> AlloyDB5[(AlloyDB)]

    EmailAppt --> Calendar[📅 Patient adds to\nGoogle Calendar]
    EmailNurse --> Calendar
    EmailRemind --> Calendar

    AlloyDB1 & AlloyDB2 & AlloyDB3 & AlloyDB4 & AlloyDB5 --> Response
```

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
