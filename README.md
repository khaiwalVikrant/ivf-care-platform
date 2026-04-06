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

    %% 5. Universal Theme Classes (No RGBA)
    %% We use bright hex codes with 'fill:none' so they work on any background
    classDef blue stroke:#0091ea,stroke-width:3px,fill:none;
    classDef yellow stroke:#ffd600,stroke-width:3px,fill:none;
    classDef purple stroke:#aa00ff,stroke-width:3px,fill:none;
    classDef teal stroke:#00bfa5,stroke-width:3px,fill:none;
    classDef green stroke:#00c853,stroke-width:3px,fill:none;
    classDef db stroke:#0288d1,stroke-width:4px,fill:none;

    class Chat blue;
    class Q1 yellow;
    class Evidence,Appt,Nurse,Remind,Cost purple;
    class Schedule teal;
    class Response green;
    class AlloyDB db;
```
---

## 🏥 IVF Cycle Stage Tracking

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'theme': 'neutral',
    'primaryColor': '#eff6ff',
    'primaryTextColor': '#1e40af',
    'primaryBorderColor': '#3b82f6',
    'lineColor': '#64748b',
    'secondaryColor': '#fff7ed',
    'tertiaryColor': '#f8fafc',
    'noteBkgColor': '#fef9c3',
    'noteTextColor': '#854d0e',
    'fontSize': '14px'
  }
} }%%

stateDiagram-v2
    direction TB

    state "🩸 Baseline" as Baseline
    state "💉 Stimulation" as Stimulation
    state "⏰ Trigger Shot" as Trigger
    state "🏥 Retrieval" as Retrieval
    state "🧪 Fertilisation" as Fertilisation
    state "🧬 Transfer" as Transfer
    state "💊 Luteal Support" as LutealSupport
    state "✨ Final Result" as PregnancyTest

    [*] --> Baseline
    
    Baseline --> Stimulation: Day 1 Injections
    note right of Stimulation
        <b>Daily Support</b>
        • Nurse visits
        • Med reminders
    end note

    Stimulation --> Trigger: Follicles Ready
    note right of Trigger
        <b>⚠️ CRITICAL</b>
        Exact timing is
        mandatory.
    end note

    Trigger --> Retrieval: 36h later
    
    Retrieval --> Fertilisation: Lab Phase
    note right of Fertilisation
        Status reports on
        Days 1, 3, and 5.
    end note

    Fertilisation --> Transfer: Embryo Selection
    note right of Transfer
        <b>Prep</b>
        • Hospital appt
        • 💧 Full bladder
    end note

    Transfer --> LutealSupport: Progesterone
    LutealSupport --> PregnancyTest: 14 Day Wait
    
    PregnancyTest --> [*]
```

---

## 👥 Use Case Diagram

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#eff6ff',
    'primaryTextColor': '#1e40af',
    'primaryBorderColor': '#3b82f6',
    'lineColor': '#64748b',
    'secondaryColor': '#f8fafc',
    'tertiaryColor': '#f1f5f9',
    'clusterBkg': 'rgba(200, 200, 200, 0.05)',
    'clusterBorder': '#94a3b8',
    'fontSize': '14px',
    'fontFamily': 'arial'
  }
} }%%

graph LR
    subgraph Actors [ ]
        direction TB
        P["👤 <b>Patient</b>"]
        N["👩‍⚕️ <b>Nurse</b>"]
        D["👨‍⚕️ <b>Doctor</b>"]
    end

    subgraph UseCases ["<b>IVF Care Platform — Use Cases</b>"]
        direction TB
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

    %% Patient Connections
    P --- UC1
    P --- UC2
    P --- UC3
    P --- UC4
    P --- UC5
    P --- UC6
    P --- UC7
    P --- UC8
    P --- UC9

    %% Nurse Connections
    N --- UC10
    N --- UC9
    N --- UC3

    %% Doctor Connections
    D --- UC11
    D --- UC12
    D --- UC2
    D --- UC9

    %% Styling for better contrast
    style Actors fill:none,stroke-dasharray: 5 5
    style UseCases fill:none,stroke-width:2px
```

---

## 🤖 Multi-Agent Coordination Example

> **Patient says:** *"Book a nurse for my trigger shot tonight at 11:30pm"*

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#eff6ff',
    'primaryTextColor': '#1e40af',
    'primaryBorderColor': '#3b82f6',
    'lineColor': '#64748b',
    'secondaryColor': '#f8fafc',
    'tertiaryColor': '#f1f5f9',
    'actorBkg': '#eff6ff',
    'actorBorder': '#3b82f6',
    'actorTextColor': '#1e40af',
    'signalColor': '#64748b',
    'signalTextColor': 'var(--color-fg-default)',
    'labelBoxBkgColor': '#f1f5f9',
    'labelBoxBorderColor': '#3b82f6',
    'labelTextColor': '#1e40af',
    'loopTextColor': '#1e40af',
    'activationBkgColor': 'rgba(59, 130, 246, 0.1)'
  }
} }%%

sequenceDiagram
    autonumber
    
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

    Note over P, A: Intent: Book Trigger Shot Visit
    
    P->>A: "Book nurse for trigger shot at 11:30pm"
    activate A
    A->>O: submit_workflow("book nurse trigger shot 11:30pm")
    activate O
    
    rect rgb(240, 249, 255)
        Note right of O: Execution Loop
        O->>N: book_nurse_visit(patient_id, 23:30)
        activate N
        N->>DB: Create NurseVisit record
        N->>E: Notify nurse (visit details + dose)
        N-->>O: nurse_visit_id
        deactivate N

        O->>C: create_event("Trigger Shot Visit", 23:30)
        activate C
        C->>DB: Create Event record
        C-->>O: event_id
        deactivate C

        O->>R: schedule_reminder(CRITICAL, 23:15)
        activate R
        R->>DB: Create Reminder record
        R->>E: Send .ics email (Patient + Nurse)
        R-->>O: reminder_id
        deactivate R

        O->>M: record_administration(nurse_visit_id)
        O->>CG: track_cost(category=nurse_visit)
        CG->>DB: Create CostRecord
    end

    O-->>A: Workflow completed
    deactivate O
    A-->>P: "✅ Nurse booked. Reminder set. Calendar invite sent."
    deactivate A
```

---

## 💰 Cost Protection Flow

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#eff6ff',
    'primaryTextColor': '#1e40af',
    'primaryBorderColor': '#3b82f6',
    'lineColor': '#64748b',
    'secondaryColor': '#fef2f2',
    'tertiaryColor': '#f0fdf4',
    'mainBkg': '#ffffff',
    'nodeBorder': '#3b82f6',
    'clusterBkg': 'rgba(255, 255, 255, 0.05)',
    'fontSize': '14px'
  }
} }%%

flowchart LR
    %% Node Definitions
    Quote["📄 <b>Clinic Quote</b><br/>Gonal-F: ₹8,500"]
    Benchmark{"⚖️ <b>Benchmark</b><br/>Market: ₹6,200"}
    
    Alert[["🚨 <b>Price Alert</b><br/>Overcharged by 37%<br/>Suggested: ₹6,200"]]
    OK(["✅ <b>Fair Price</b><br/>Within Range"])
    
    Patient["👤 <b>Patient Informed</b><br/>Prior to Payment"]
    Record[("🗄️ <b>AlloyDB</b><br/>Cost Logged")]
    
    Summary["📊 <b>Monthly Summary</b><br/>Cost by Category"]
    Insurance["📝 <b>Insurance Claim</b><br/>Summary Generated"]

    %% Flow Connections
    Quote --> Benchmark

    Benchmark -- ">15% Over" --> Alert
    Benchmark -- "Within 15%" --> OK

    Alert --> Patient
    Patient --> Record
    OK --> Record

    Record --> Summary
    Summary --> Insurance

    %% Specific Styling for Logic Paths
    style Alert fill:#fff1f2,stroke:#e11d48,color:#9f1239
    style OK fill:#f0fdf4,stroke:#16a34a,color:#166534
    style Record fill:#f8fafc,stroke:#64748b
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
