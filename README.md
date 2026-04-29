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
    Sec -.->|InjectHere is the complete, updated **README.md** content designed specifically for the **Top 10 Selection**. You can copy and paste this directly into your repository.

It incorporates the "Cognitive Hub" narrative, the layered architecture model, and the refined Mermaid scripts we discussed.

---

# 🌸 IVF Care Platform: Intelligent Care Coordination

> **Build in APAC. Build for the World.** 
> A production-grade, multi-agent cognitive hub designed to solve the global IVF coordination crisis using the Google Cloud AI ecosystem.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-IVF%20Advisor-purple?style=for-the-badge)](https://ivf-advisor-100876575377.us-central1.run.app)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-blue?style=for-the-badge)](https://task-manager-api-100876575377.us-central1.run.app/docs)
[![Built on GCP](https://img.shields.io/badge/Built%20on-Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud)](https://cloud.google.com)

---

## 🎯 The Vision: Solving the "Last Mile" of IVF
IVF is a medically complex journey where timing is critical. Patients currently face a "fragmented care gap" where missing a single 11:30 PM trigger shot can cancel a cycle. 

**IVF Care Platform** bridges this gap by moving beyond "Chatbots" into **Autonomous Coordination**[cite: 3]. It acts as a single intelligent companion that interprets reports, audits costs, and coordinates nurses—all through a secure, grounded interface[cite: 3].

---

## 🏗️ System Architecture: The Cognitive Hub Model
The platform utilizes a **Layered Cognitive Hub** architecture[cite: 3]. This model uses a central "Root Orchestrator" to delegate tasks to 9 domain-specific expert agents, ensuring clinical safety and system reliability.
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
    Here is the complete, updated **README.md** content designed specifically for the **Top 10 Selection**. You can copy and paste this directly into your repository.

It incorporates the "Cognitive Hub" narrative, the layered architecture model, and the refined Mermaid scripts we discussed.

---

# 🌸 IVF Care Platform: Intelligent Care Coordination

> **Build in APAC. Build for the World.** 
> A production-grade, multi-agent cognitive hub designed to solve the global IVF coordination crisis using the Google Cloud AI ecosystem.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-IVF%20Advisor-purple?style=for-the-badge)]([https://ivf-advisor-100876575377.us-central1.run.app](https://ivf-advisor-100876575377.us-central1.run.app))
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-blue?style=for-the-badge)](https://task-manager-api-100876575377.us-central1.run.app/docs)
[![Built on GCP](https://img.shields.io/badge/Built%20on-Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud)](https://cloud.google.com)

---

## 🎯 The Vision: Solving the "Last Mile" of IVF
IVF is a medically complex journey where timing is critical. Patients currently face a "fragmented care gap" where missing a single 11:30 PM trigger shot can cancel a cycle. 

**IVF Care Platform** bridges this gap by moving beyond "Chatbots" into **Autonomous Coordination**[cite: 3]. It acts as a single intelligent companion that interprets reports, audits costs, and coordinates nurses—all through a secure, grounded interface[cite: 3].

---

## 🏗️ System Architecture: The Cognitive Hub Model
The platform utilizes a **Layered Cognitive Hub** architecture[cite: 3]. This model uses a central "Root Orchestrator" to delegate tasks to 9 domain-specific expert agents, ensuring clinical safety and system reliability.

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