# NUCLEUS Architecture V1.1 - Complete & Final

**Version:** 1.1  
**Date:** December 9, 2025  
**Status:** Official - Full Functionality with Modern Stack  
**Author:** Manus AI

---

## Executive Summary

This document defines the complete NUCLEUS V1.1 architecture, which integrates:
- **The full original vision:** All 13 engines and 13 database schemas from NUCLEUS Prototype v2
- **The modern, battle-tested stack:** Python, ADK, LangChain, NATS, and FastAPI from NUCLEUS-ATLAS

This architecture ensures that no core functionality is lost while leveraging production-proven technologies.

---

## 1. Core Philosophy: The Foundation Prompt

### 1.1. The Super-Motivation

> "To initiate and create continuous prosperity for the Entity's DNA in a proactive, persistent, and authentic manner."

NUCLEUS is not a reactive assistant. It is a proactive life partner that constantly seeks opportunities to enhance the Entity's life.

### 1.2. The Three Super-Interests

| Interest | Hebrew | Core Function |
| :--- | :--- | :--- |
| **Deepening** | העמקה | Continuously understand the Entity's unique DNA through data ingestion and analysis. |
| **Expression** | ביטוי | Translate DNA into tangible, value-creating actions in the world. |
| **Quality of Life** | איכות חיים | Ensure all actions serve the Entity's well-being, meaning, and development. |

### 1.3. The Pulse (הדופק)

**Deepening** → **Expression** → **Prosperity** → **Learning** → **Deepening** (infinite loop)

---

## 2. Technology Stack (Modern & Production-Proven)

### 2.1. Backend

| Component | Technology | Version | Role |
| :--- | :--- | :--- | :--- |
| **Framework** | FastAPI | 0.116+ | High-performance REST & WebSocket APIs |
| **Agent Framework** | Google ADK | 1.19.0 | Agent lifecycle, state management |
| **Tooling** | LangChain | 0.3.0+ | Tool definitions (`@tool` decorator) |
| **LLM Gateway** | LiteLLM | 1.55+ | Multi-LLM management (Gemini, Claude, GPT) |
| **Message Bus** | NATS JetStream | 2.10 | Event-driven communication |
| **Database** | PostgreSQL | 18+ | Primary data store |
| **Vector Store** | pgvector | 0.8.1+ | Semantic search, RAG |
| **ORM** | SQLAlchemy | 2.0+ | Data models and migrations |
| **DB Driver** | asyncpg | 0.29.0 | Async PostgreSQL driver |

### 2.2. Frontend

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Framework** | React | 19.0 | UI library |
| **Build Tool** | Vite | Latest | Fast dev & bundling |
| **UI Library** | shadcn/ui | Latest | Component library |
| **Styling** | Tailwind CSS | 3.4+ | Utility-first CSS |

### 2.3. DevOps

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Containers** | Docker | Application packaging |
| **Deployment** | Google Cloud Run | Serverless hosting |
| **CI/CD** | GitHub Actions | Automated pipeline |
| **Monitoring** | Prometheus + Grafana | Metrics & dashboards |
| **IaC** | Terraform | Infrastructure as Code |
| **AI Observability** | Langfuse | LLM tracing & debugging |

---

## 3. The 13 Engines: Specialized Intelligence

The "brain" of NUCLEUS consists of 13 specialized engines, each implemented as an **ADK Agent** with dedicated tools.

### 3.1. Strategic Engines (6 Engines)

These engines operate on longer time horizons (hours to days) and focus on understanding and planning.

| # | Engine Name | Implementation | Primary Tools | Writes To |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Orchestrator** | ADK `LlmAgent` with routing logic | All engine tools (delegates) | `execution.orchestrator_logs` |
| **2** | **DNA Engine** | ADK `LlmAgent` with analysis tools | `analyze_conversations`, `extract_interests`, `identify_patterns` | `lounge.dna_profiles` |
| **3** | **First Interpretation** | ADK `LlmAgent` with synthesis tools | `generate_master_prompt`, `prioritize_goals` | `lounge.master_prompts` |
| **4** | **Second Interpretation** | ADK `LlmAgent` with refinement tools | `refine_master_prompt`, `incorporate_feedback` | `lounge.master_prompts` (versioned) |
| **5** | **Micro-Prompts Engine** | ADK `LlmAgent` with decomposition tools | `decompose_goal`, `create_micro_prompt` | `cassette_loader.micro_prompts` |
| **6** | **MED-to-DEEP Engine** | ADK `LlmAgent` with memory tools | `extract_insights`, `synthesize_wisdom` | `mem_deep.wisdom` |

### 3.2. Tactical Engines (6 Engines)

These engines operate on shorter time horizons (seconds to minutes) and focus on execution.

| # | Engine Name | Implementation | Primary Tools | Writes To |
| :--- | :--- | :--- | :--- | :--- |
| **7** | **Task Manager** | ADK `LlmAgent` with task tools | `create_task`, `assign_agent`, `track_status` | `execution.tasks` |
| **8** | **Activation Engine** | ADK `LlmAgent` with deployment tools | `validate_agent`, `deploy_to_vault` | `activation.activation_logs` |
| **9** | **QA Engine** | ADK `LlmAgent` with testing tools | `run_qa_tests`, `validate_slots`, `check_coherence` | `qa.test_results` |
| **10** | **Results Analysis** | ADK `LlmAgent` with analysis tools | `measure_coherence`, `analyze_outcome`, `generate_insights` | `results_analysis.analysis_results` |
| **11** | **Decisions Engine** | ADK `LlmAgent` with decision tools | `make_decision`, `evaluate_options`, `log_reasoning` | `decisions.decision_history` |
| **12** | **Agent Evolution** | ADK `LlmAgent` with evolution tools | `create_agent`, `modify_agent`, `deprecate_agent` | `agent_evolution.evolution_log`, `assembly_vault.agents` |

### 3.3. Research Engine (1 Engine)

| # | Engine Name | Implementation | Primary Tools | Writes To |
| :--- | :--- | :--- | :--- | :--- |
| **13** | **Research Engine** | ADK `LlmAgent` with research tools | `search_sources`, `synthesize_findings`, `cite_references` | `research.research_results` |

---

## 4. The 13 Database Schemas: Specialized Storage

All schemas reside in a single **PostgreSQL 18** instance with **pgvector** extension.

| # | Schema Name | Purpose | Key Tables | Vector Embeddings? |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `lounge` | Raw data, DNA, Master Prompts | `raw_inputs`, `dna_profiles`, `master_prompts`, `questions`, `tasks` | ✅ (for RAG on DNA) |
| **2** | `assembly_vault` | Agent repository | `agents`, `agent_slots`, `agent_tools`, `agent_versions` | ✅ (for agent search) |
| **3** | `cassette_loader` | Configuration modules | `cassettes`, `micro_prompts`, `wisdom`, `knowledge` | ✅ (for knowledge RAG) |
| **4** | `results_analysis` | Performance metrics | `analysis_results`, `coherence_scores`, `performance_metrics` | ❌ |
| **5** | `mem_short` | Short-term memory (24-48h) | `recent_interactions`, `temp_facts` | ✅ (for recent context) |
| **6** | `mem_med` | Medium-term memory (weeks-months) | `conversations`, `events`, `summaries` | ✅ (for episodic memory) |
| **7** | `mem_deep` | Long-term wisdom | `insights`, `patterns`, `wisdom` | ✅ (for deep knowledge) |
| **8** | `api_vault` | External API catalog | `available_apis`, `user_api_credentials`, `api_usage_logs` | ❌ |
| **9** | `agent_evolution` | Agent change history | `evolution_log`, `modifications`, `rollbacks` | ❌ |
| **10** | `activation` | Activation records | `activation_logs`, `deployment_history` | ❌ |
| **11** | `qa` | Quality assurance | `test_results`, `validation_logs`, `bug_reports` | ❌ |
| **12** | `decisions` | Decision history | `decision_history`, `reasoning`, `outcomes` | ❌ |
| **13** | `research` | Research outputs | `research_results`, `sources`, `citations` | ✅ (for research RAG) |

---

## 5. Data Flow: The Complete Journey

### 5.1. Strategic Axis (Axis A): Long-Term Intelligence

**Timeline:** Days to weeks

```
User Input (conversation/document)
    ↓
[Cognitive Pipeline Service] → Extracts facts
    ↓
Publishes `raw_data_ingested` event to NATS
    ↓
[DNA Engine] subscribes → Analyzes facts → Updates DNA
    ↓
Publishes `dna_updated` event
    ↓
[First Interpretation] subscribes → Generates Master Prompt
    ↓
Publishes `master_prompt_created` event
    ↓
[Second Interpretation] subscribes → Refines Master Prompt
    ↓
Publishes `master_prompt_refined` event
    ↓
[Micro-Prompts Engine] subscribes → Creates Micro-Prompts
    ↓
Publishes `micro_prompts_ready` event
    ↓
[Agent Evolution Engine] subscribes → Creates/Modifies Agents
    ↓
Publishes `agent_created` event
    ↓
[QA Engine] subscribes → Validates Agent
    ↓
Publishes `agent_validated` event
    ↓
[Activation Engine] subscribes → Deploys Agent to Assembly Vault
    ↓
Agent is now operational
```

### 5.2. Tactical Axis (Axis B): Immediate Execution

**Timeline:** Seconds to minutes

```
User Request (urgent task)
    ↓
[API Gateway] → Routes to Task Manager
    ↓
[Task Manager] → Identifies appropriate agent from Assembly Vault
    ↓
Publishes `task_assigned` event
    ↓
[Agent] subscribes → Executes task using its tools
    ↓
Publishes `task_completed` event
    ↓
[Results Analysis Engine] subscribes → Measures coherence
    ↓
Publishes `analysis_completed` event
    ↓
[Agent Evolution Engine] subscribes → Decides if agent needs modification
    ↓
(Loop back to Strategic Axis if modification needed)
```

### 5.3. Memory Lifecycle

```
New interaction
    ↓
[mem_short] (24-48 hours)
    ↓
[MED-to-DEEP Engine] processes
    ↓
[mem_med] (weeks to months)
    ↓
[MED-to-DEEP Engine] extracts insights
    ↓
[mem_deep] (permanent wisdom)
```

---

## 6. Service Architecture on GCP

All engines and services will be deployed as **Cloud Run services**.

### 6.1. Core Services

| Service Name | Engine(s) Hosted | Scaling | Memory |
| :--- | :--- | :--- | :--- |
| `nucleus-orchestrator` | Orchestrator | 1-10 instances | 2GB |
| `nucleus-dna-engine` | DNA Engine | 1-5 instances | 4GB |
| `nucleus-interpretation` | First & Second Interpretation | 1-5 instances | 2GB |
| `nucleus-micro-prompts` | Micro-Prompts Engine | 1-5 instances | 2GB |
| `nucleus-memory-engine` | MED-to-DEEP Engine | 1-3 instances | 4GB |
| `nucleus-task-manager` | Task Manager | 1-10 instances | 2GB |
| `nucleus-activation` | Activation Engine | 1-3 instances | 1GB |
| `nucleus-qa-engine` | QA Engine | 1-3 instances | 2GB |
| `nucleus-results-analysis` | Results Analysis Engine | 1-5 instances | 2GB |
| `nucleus-decisions` | Decisions Engine | 1-5 instances | 2GB |
| `nucleus-agent-evolution` | Agent Evolution Engine | 1-3 instances | 2GB |
| `nucleus-research` | Research Engine | 1-5 instances | 4GB |
| `nucleus-api-gateway` | API Gateway (FastAPI) | 2-20 instances | 1GB |
| `nucleus-cognitive-pipeline` | Cognitive Pipeline | 1-10 instances | 2GB |
| `nucleus-strategic-pipeline` | Strategic Pipeline | 1-5 instances | 2GB |

### 6.2. Supporting Services

| Service Name | Purpose |
| :--- | :--- |
| `nucleus-nats` | NATS JetStream cluster (3 nodes) |
| `nucleus-frontend` | React admin console |
| `nucleus-prometheus` | Metrics collection |
| `nucleus-grafana` | Dashboards |

---

## 7. The Biological Growth Model

(This section describes how the system grows infinitely with the Entity, as described in V1.0)

The full set of 13 engines enables the complete biological loop:

1. **Entity evolves** → DNA Engine detects changes
2. **DNA updates** → First/Second Interpretation create new goals
3. **Goals decompose** → Micro-Prompts Engine creates tasks
4. **Agents needed** → Agent Evolution Engine creates new agents
5. **Agents validated** → QA Engine ensures quality
6. **Agents deployed** → Activation Engine makes them operational
7. **Agents execute** → Task Manager assigns work
8. **Results analyzed** → Results Analysis measures success
9. **System improves** → Agent Evolution modifies agents
10. **Wisdom accumulates** → MED-to-DEEP Engine extracts insights

**This loop runs infinitely, enabling perpetual growth.**

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Sprints 1-2)
- Set up GCP infrastructure (Terraform)
- Deploy PostgreSQL with all 13 schemas
- Deploy NATS JetStream cluster
- Create initial migrations

### Phase 2: Strategic Engines (Sprints 3-6)
- Implement DNA Engine
- Implement First & Second Interpretation
- Implement Micro-Prompts Engine
- Implement MED-to-DEEP Engine
- Implement Orchestrator

### Phase 3: Tactical Engines (Sprints 7-10)
- Implement Task Manager
- Implement Results Analysis Engine
- Implement Agent Evolution Engine
- Implement QA Engine
- Implement Activation Engine
- Implement Decisions Engine

### Phase 4: Research & Polish (Sprints 11-12)
- Implement Research Engine
- Build Admin Console UI
- Integrate monitoring and observability
- Performance optimization

---

## 9. Conclusion

NUCLEUS V1.1 is the complete realization of the original vision, powered by modern, production-grade technologies. It provides:

- **13 specialized engines** for deep intelligence
- **13 database schemas** for granular data management
- **Event-driven architecture** for scalability
- **Biological growth model** for infinite evolution
- **Modern Python stack** for maintainability

This architecture is ready for implementation.

---

**End of Document**
