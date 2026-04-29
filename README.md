# 🌸 IVF Care Platform: Intelligent Care Coordination

> **Build in APAC. Build for the World.**  
> A production-grade, multi-agent cognitive hub designed to solve the global IVF coordination crisis using the Google Cloud AI ecosystem.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-IVF%20Advisor-purple?style=for-the-badge)](https://ivf-advisor-100876575377.us-central1.run.app)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-blue?style=for-the-badge)](https://task-manager-api-100876575377.us-central1.run.app/docs)
[![Built on GCP](https://img.shields.io/badge/Built%20on-Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud)](https://cloud.google.com)

---

## 🎯 The Vision: Solving the "Last Mile" of IVF

IVF is a medically complex journey where timing is critical. Patients currently face a "fragmented care gap" where missing a single 11:30 PM trigger shot can cancel a cycle. **IVF Care Platform** bridges this gap by moving beyond "Chatbots" into **Autonomous Coordination**. It acts as a single intelligent companion that interprets reports, audits costs, and coordinates nurses—all through a secure, grounded interface.

---

## 🏗️ System Architecture: The Cognitive Hub Model

The platform utilizes a **Layered Cognitive Hub** architecture. This model uses a central "Root Orchestrator" to delegate tasks to 9 domain-specific expert agents, ensuring clinical safety and system reliability.

```mermaid
graph TB
    subgraph Interaction_Layer ["Layer 1: Interaction (Cloud Run)"]
        UI[📱 Gradio 5.x Command Center<br/>Multi-language: EN/HI]
        Voice[🎤 Speech-to-Text API]
    end
    
    subgraph Intelligence_Layer ["Layer 2: Cognitive Hub (Google ADK)"]
        Orch[🤖 Root Orchestrator]
        LLM[🧠 Gemini 2.0 Flash Lite]
        subgraph Experts ["9 Specialized Sub-Agents"]
            A1[💊 Medication Agent]
            A2[💰 CostGuard Agent]
            A3[📅 Appt Agent]
            A4[🧪 Lab Agent]
            A5[📋 Task Agent]
        end
    end
    
    subgraph Foundation_Layer ["Layer 3: Secure Foundation (VPC Private Subnet)"]
        Alloy[(🗄️ AlloyDB PostgreSQL<br/>pgvector + Columnar Engine)]
        Sec[🔐 Secret Manager]
        GCS[☁️ Cloud Storage: PDF Reports]
    end
    
    subgraph Impact_Layer ["Layer 4: Real-World Actions"]
        Mail[📧 Gmail SMTP<br/>.ics Attachments]
        Cal[📅 Google Calendar API]
    end
    
    %% Flow
    UI <--> Orch
    Orch <--> LLM
    Orch --> Experts
    Experts <--> Alloy
    Experts --> Mail & Cal
    Sec -.->|Inject| UI & Orch
    
    classDef gcp fill:#f8f9fa,stroke:#4285f4,stroke-width:2px;
    class Interaction_Layer,Intelligence_Layer,Foundation_Layer,Impact_Layer gcp;
```

---

## 🛡️ Innovation Highlights

### 1. Safety-First "Scope Guard"

Medical AI requires strict boundaries. Every request passes through a **Scope Guard Agent** that validates domain adherence and detects emergencies before the LLM processes the intent.

```mermaid
graph TD
    Start([User Request]) --> Guard{🛡️ Scope Guard}
    Guard -- Out of Scope --> Educate[Educational Disclaimer]
    Guard -- In Scope --> Parse[ADK Orchestrator]
    
    subgraph "Expert Execution"
        Parse --> Search[Vertex AI Search]
        Parse --> Task[Task Manager API]
        Parse --> Vision[Vision API OCR]
    end
    
    Search & Task & Vision --> Alloy[(AlloyDB Atomic Commit)]
    Alloy --> End([Deliver Safe Response])
    
    style Guard fill:#fee2e2,stroke:#dc2626
    style Alloy fill:#dcfce7,stroke:#16a34a
```

### 2. Multimodal Lab Interpretation

Utilizing **Google Vision API**, patients can upload physical lab reports. The system extracts key values (AMH, FSH, AFC) and interprets them using plain language grounded in Vertex AI Search citations.

### 3. CostGuard: Patient Financial Protection

The platform benchmarks clinic quotes against real-time market rates for 11+ Indian cities. If a clinic overcharges by more than 15%, the system flags the record and generates an insurance-ready audit summary.

---

## 🤖 Multi-Agent Coordination Flow

This demonstrates a complex, autonomous coordination: Patient uploads a bill → AI audits the cost → AI schedules a follow-up → AI syncs the calendar.

```mermaid
sequenceDiagram
    participant P as Patient
    participant O as ADK Orchestrator
    participant V as Vision API
    participant C as CostGuard Agent
    participant D as AlloyDB
    participant E as External (Email/Cal)
    
    P->>O: Uploads Medical Bill Image
    O->>V: OCR & Data Extraction
    
    rect rgb(245, 243, 255)
        Note over O,C: Agentic Audit
        O->>C: Route to CostGuard
        C->>D: Query Market Rates (pgvector)
        C->>C: Flag Overcharge (>15%)
    end
    
    O->>D: Persist Record
    O->>E: Send .ics Confirmation
    O->>P: Return Audit + PDF Link
```

---

## 🛠️ Enterprise Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Agent Hub** | Google ADK | Complex session state and tool orchestration |
| **Brain** | Gemini 2.0 Flash Lite | High-speed reasoning with enterprise SLAs |
| **Database** | AlloyDB PostgreSQL | Concurrent multi-agent writes + native vector search |
| **Security** | Secret Manager | Zero-trust credential management |
| **Network** | VPC Direct Egress | Private data path for patient privacy |
| **UI** | Gradio 5.x | High-density clinical command center |

---

## 📁 Project Structure

```
ivf-care-platform/
├── ivf_advisor/      # Cloud Run Service 1: UI & Orchestration
│   ├── tools/        # 29 specialized tools (OCR, PDF, Evidence)
│   └── agent.py      # ADK agent logic
├── task_manager/     # Cloud Run Service 2: Multi-agent execution
│   ├── agents/       # 9 domain-specific sub-agents
│   └── db/           # AlloyDB connection & pgvector search
├── cloudbuild.yaml   # Parallel CI/CD pipeline
└── pyproject.toml    # Dependencies & project metadata
```

---

**Built by:** Vikrant Khaiwal  
**Hackathon:** Google Cloud Gen AI Academy - APAC Edition  
**License:** MIT
