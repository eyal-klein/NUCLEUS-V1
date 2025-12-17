# NUCLEUS V1.0 - GCP Deployment Architecture

**Version:** 1.0  
**Date:** December 9, 2025  
**Status:** Proposed

---

## 1. Overview

This document outlines the complete deployment architecture for NUCLEUS V1.0 on Google Cloud Platform (GCP). The architecture is designed to be **scalable, secure, and cost-effective**, leveraging serverless components where possible while ensuring high availability for stateful services.

This plan is based on the best practices and proven infrastructure from the NUCLEUS-ATLAS project.

## 2. Deployment Diagram

![NUCLEUS GCP Deployment Architecture](NUCLEUS_GCP_DEPLOYMENT_V1.png)

## 3. Service Architecture (Cloud Run)

Our application logic is broken down into microservices, each deployed as a separate, independently scalable **Cloud Run** service. This serverless approach minimizes management overhead and scales to zero, reducing costs.

| Service Name | Container | Purpose | CPU / Memory |
| :--- | :--- | :--- | :--- |
| `nucleus-master-agent` | `gcr.io/thrive-system1/nucleus-master-agent` | The central nervous system. Hosts the ADK, Orchestrator, and Chat API. | 2 CPU / 4GiB |
| `results-analysis-engine` | `gcr.io/thrive-system1/results-analysis-engine` | Subscribes to NATS and analyzes task outcomes. | 1 CPU / 2GiB |
| `agent-evolution-engine` | `gcr.io/thrive-system1/agent-evolution-engine` | Subscribes to NATS and evolves agents in the Assembly Vault. | 1 CPU / 2GiB |
| `frontend` | `gcr.io/thrive-system1/frontend` | Serves the React-based user interface. | 1 CPU / 1GiB |

**Key Features:**
- **Auto-scaling:** Each service scales independently from 0 to 100 instances based on traffic.
- **IAM Invocation:** Services are configured for internal traffic only, invokable only by other authenticated services within the project.

## 4. GCP Infrastructure Components

### 4.1. Compute & Networking

| Component | Name | Configuration | Purpose |
| :--- | :--- | :--- | :--- |
| **VPC Network** | `vpc-nucleus` | Custom mode VPC | Provides a private, isolated network for all resources. |
| **Subnet** | `subnet-europe-west1` | `10.10.0.0/16` | The primary subnet for all resources in the region. |
| **Cloud Run** | (See above) | `europe-west1` | Hosts our stateless microservices. |
| **Compute Engine (GCE)** | `vm-nats-server` | `e2-medium` (2 vCPU, 4GB RAM) | **Critical:** Hosts the NATS JetStream message broker. Cloud Run is not suitable for stateful services like a message queue. |
| **VPC Connector** | `connector-serverless` | `10.11.0.0/28` | Allows Cloud Run services to access resources in the VPC (like the DB and NATS). |

### 4.2. Database & Storage

| Component | Name | Configuration | Purpose |
| :--- | :--- | :--- | :--- |
| **Cloud SQL** | `nucleus-db-v1` | PostgreSQL 18, 2 vCPU, 8GB RAM, HA enabled | The primary database, hosting the `dna`, `memory`, `assembly`, and `execution` schemas. |
| **Cloud Storage** | `bucket-nucleus-dna` | Standard, Regional | Stores all raw files, documents, and assets uploaded by the Entity. |
| **Artifact Registry** | `repo-nucleus-images` | Docker Repository | Stores all our Docker container images. |

### 4.3. Security & Management

| Component | Name | Purpose |
| :--- | :--- | :--- |
| **Secret Manager** | `secrets-nucleus` | Securely stores all secrets: DB passwords, API keys (HeyGen, OpenAI), etc. |
| **IAM** | - | Manages permissions. Each service will have its own dedicated Service Account with the principle of least privilege. |
| **Cloud Logging** | - | Aggregates logs from all services for debugging and analysis. |
| **Cloud Monitoring** | - | Provides dashboards and alerts for system health and performance. |

## 5. Network & Communication Flow

1.  **User to Frontend:** User traffic hits the `frontend` Cloud Run service via its public URL.
2.  **Frontend to Master Agent:** The React app makes API calls to the `nucleus-master-agent`'s public URL.
3.  **Internal Communication (Service-to-Service):**
    - The Master Agent communicates with other engines (if they were separate services) via **internal Cloud Run invocation** (IAM-authenticated).
    - For our architecture, the engines are within the Master Agent, but this allows for future splitting.
4.  **Access to Stateful Services (DB & NATS):**
    - All Cloud Run services are connected to the `vpc-nucleus` via the **VPC Connector**.
    - This allows them to securely access the **Cloud SQL** database and the **NATS VM** using their private IP addresses.
5.  **Event-Driven Communication (NATS):**
    - When a task is completed, the Master Agent publishes an event to a topic on the NATS server.
    - The `results-analysis-engine` and `agent-evolution-engine` are subscribed to these topics and are triggered to start their processes.

## 6. CI/CD Pipeline (GitHub Actions)

A fully automated CI/CD pipeline will be established using GitHub Actions.

**Workflow File:** `.github/workflows/deploy.yml`

**Trigger:** On push to `main` branch.

**Key Steps for each service (`nucleus-master-agent`, `frontend`, etc.):**

1.  **Authenticate to GCP:** Use Workload Identity Federation to securely authenticate GitHub Actions to GCP without service account keys.
2.  **Build Docker Image:** Build the Docker image for the service.
3.  **Push to Artifact Registry:** Tag and push the image to `gcr.io/thrive-system1/`.
4.  **Deploy to Cloud Run:** Deploy the new image to the corresponding Cloud Run service.

This ensures that every change merged to the main branch is automatically deployed to production, enabling rapid iteration.

## 7. Infrastructure as Code (Terraform)

All GCP infrastructure will be managed using Terraform to ensure it is version-controlled, repeatable, and easy to modify.

**Proposed Directory Structure:**

```
/terraform
├── main.tf         # Main entrypoint, provider config
├── variables.tf    # Input variables (project_id, region)
├── outputs.tf      # Outputs (DB IP, service URLs)
├── /modules
│   ├── /vpc
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── /cloud_sql
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── /cloud_run
│   │   ├── main.tf
│   │   └── variables.tf
│   └── /gcs
│       ├── main.tf
│       └── variables.tf
```

This modular structure allows us to manage each piece of the infrastructure cleanly.

---

## 8. Summary & Next Steps

This deployment architecture provides a robust, scalable, and secure foundation for NUCLEUS V1.0. It leverages modern GCP services and best practices, drawing heavily from the successful deployment of NUCLEUS-ATLAS.

**Next Step:** Upon approval, we will begin creating the Terraform modules and the initial GitHub Actions workflow as described in **Phase 1** of our development roadmap.
