# NUCLEUS V1.1 - GCP Deployment Architecture

**Version:** 1.1  
**Date:** December 9, 2025  
**Author:** Manus AI

---

## 1. Overview

This document describes the complete GCP deployment architecture for NUCLEUS V1.1, which includes all 13 engines deployed as Cloud Run services, plus supporting infrastructure.

---

## 2. Cloud Run Services (15 Services)

### 2.1. Engine Services (12 Services)

| Service Name | Engine | Min Instances | Max Instances | Memory | CPU |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nucleus-orchestrator` | Orchestrator | 1 | 10 | 2GB | 2 |
| `nucleus-dna-engine` | DNA Engine | 1 | 5 | 4GB | 2 |
| `nucleus-interpretation` | First & Second Interpretation | 1 | 5 | 2GB | 2 |
| `nucleus-micro-prompts` | Micro-Prompts Engine | 1 | 5 | 2GB | 1 |
| `nucleus-memory-engine` | MED-to-DEEP Engine | 1 | 3 | 4GB | 2 |
| `nucleus-task-manager` | Task Manager | 1 | 10 | 2GB | 2 |
| `nucleus-activation` | Activation Engine | 1 | 3 | 1GB | 1 |
| `nucleus-qa-engine` | QA Engine | 1 | 3 | 2GB | 1 |
| `nucleus-results-analysis` | Results Analysis Engine | 1 | 5 | 2GB | 2 |
| `nucleus-decisions` | Decisions Engine | 1 | 5 | 2GB | 2 |
| `nucleus-agent-evolution` | Agent Evolution Engine | 1 | 3 | 2GB | 2 |
| `nucleus-research` | Research Engine | 1 | 5 | 4GB | 2 |

### 2.2. Pipeline Services (2 Services)

| Service Name | Purpose | Min Instances | Max Instances | Memory | CPU |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nucleus-cognitive-pipeline` | Process raw inputs | 1 | 10 | 2GB | 2 |
| `nucleus-strategic-pipeline` | Execute complex tasks | 1 | 5 | 2GB | 2 |

### 2.3. Gateway Service (1 Service)

| Service Name | Purpose | Min Instances | Max Instances | Memory | CPU |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nucleus-api-gateway` | Main API entry point | 2 | 20 | 1GB | 1 |

---

## 3. Database (Cloud SQL)

| Component | Specification |
| :--- | :--- |
| **Type** | Cloud SQL for PostgreSQL |
| **Version** | PostgreSQL 18 |
| **Machine Type** | db-custom-4-16384 (4 vCPU, 16GB RAM) |
| **Storage** | 500GB SSD (auto-expanding) |
| **High Availability** | Yes (regional with automatic failover) |
| **Backups** | Daily automated backups, 30-day retention |
| **Extensions** | pgvector 0.8.1+ |

### 3.1. Database Schemas (13 Schemas)

All schemas reside in a single PostgreSQL instance:

1. `lounge`
2. `assembly_vault`
3. `cassette_loader`
4. `results_analysis`
5. `mem_short`
6. `mem_med`
7. `mem_deep`
8. `api_vault`
9. `agent_evolution`
10. `activation`
11. `qa`
12. `decisions`
13. `research`

---

## 4. Message Bus (NATS JetStream)

### Option A: Self-Hosted on GKE (Recommended for Production)

| Component | Specification |
| :--- | :--- |
| **Platform** | Google Kubernetes Engine (GKE) |
| **Cluster Size** | 3 nodes (for high availability) |
| **Machine Type** | n2-standard-2 (2 vCPU, 8GB RAM) |
| **NATS Version** | 2.10+ |
| **JetStream** | Enabled with persistent storage |
| **Storage** | 100GB SSD per node |

### Option B: Cloud Run (Simpler for MVP)

| Component | Specification |
| :--- | :--- |
| **Service Name** | `nucleus-nats` |
| **Min Instances** | 1 |
| **Max Instances** | 3 |
| **Memory** | 2GB |
| **CPU** | 2 |

---

## 5. Storage (Google Cloud Storage)

| Bucket Name | Purpose | Storage Class |
| :--- | :--- | :--- |
| `nucleus-user-files` | User-uploaded documents | Standard |
| `nucleus-cassettes` | Configuration modules | Standard |
| `nucleus-backups` | Database backups | Nearline |
| `nucleus-logs` | Long-term log storage | Coldline |

---

## 6. Secrets Management

| Secret Name | Purpose |
| :--- | :--- |
| `nucleus-db-password` | PostgreSQL password |
| `nucleus-openai-api-key` | OpenAI API key |
| `nucleus-anthropic-api-key` | Anthropic API key |
| `nucleus-google-ai-key` | Google AI API key |
| `nucleus-nats-credentials` | NATS authentication |

---

## 7. Monitoring & Observability

### 7.1. Prometheus (Cloud Run)

| Service Name | Purpose | Min Instances | Memory |
| :--- | :--- | :--- | :--- |
| `nucleus-prometheus` | Metrics collection | 1 | 4GB |

### 7.2. Grafana (Cloud Run)

| Service Name | Purpose | Min Instances | Memory |
| :--- | :--- | :--- | :--- |
| `nucleus-grafana` | Dashboards | 1 | 2GB |

### 7.3. Langfuse (External SaaS)

- **Purpose:** LLM observability and tracing
- **Integration:** All ADK agents send traces to Langfuse

---

## 8. Networking

### 8.1. VPC Configuration

- **VPC Name:** `nucleus-vpc`
- **Subnets:**
  - `nucleus-services` (10.0.1.0/24) - For Cloud Run services
  - `nucleus-data` (10.0.2.0/24) - For Cloud SQL and NATS
- **Firewall Rules:**
  - Allow internal traffic between subnets
  - Allow HTTPS from internet to API Gateway
  - Block all other inbound traffic

### 8.2. Cloud Load Balancer

- **Type:** HTTPS Load Balancer
- **Backend:** `nucleus-api-gateway` Cloud Run service
- **SSL Certificate:** Google-managed certificate
- **Domain:** `api.nucleus.yourdomain.com`

---

## 9. CI/CD Pipeline (GitHub Actions)

### 9.1. Workflow Triggers

- **Push to `main`:** Deploy to production
- **Pull Request:** Run tests, build images
- **Manual:** Deploy specific service

### 9.2. Deployment Steps

1. **Lint & Test:** Run `pytest` and `ruff`
2. **Build Docker Images:** Build all 15 service images
3. **Push to Artifact Registry:** Push images to GCP Artifact Registry
4. **Deploy to Cloud Run:** Deploy each service with `gcloud run deploy`
5. **Run Smoke Tests:** Verify all services are healthy

---

## 10. Cost Estimation (Monthly)

| Component | Estimated Cost (USD) |
| :--- | :--- |
| Cloud Run (15 services) | $300-500 |
| Cloud SQL (PostgreSQL) | $200-300 |
| NATS on GKE (3 nodes) | $150-200 |
| Cloud Storage | $50-100 |
| Load Balancer | $20-30 |
| Monitoring (Prometheus/Grafana) | $50-100 |
| LLM API Calls (Gemini/Claude) | $500-2000 (variable) |
| **Total** | **$1,270-3,230/month** |

---

## 11. Terraform Structure

```
infrastructure/
├── modules/
│   ├── cloud_run/
│   ├── cloud_sql/
│   ├── gke/
│   ├── vpc/
│   └── storage/
└── environments/
    └── production/
        ├── main.tf
        ├── variables.tf
        └── terraform.tfvars
```

---

## 12. Next Steps

1. **Review and approve** this deployment architecture
2. **Create Terraform modules** for each component
3. **Set up GCP project** and enable required APIs
4. **Deploy infrastructure** using Terraform
5. **Deploy services** using GitHub Actions

---

**End of Document**
