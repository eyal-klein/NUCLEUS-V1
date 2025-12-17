# NUCLEUS V1.2 - CI/CD Guide

## Overview

NUCLEUS uses **individual GitHub Actions workflows** for each component (services and jobs), enabling:
- **Granular deployments** - Deploy only what changed
- **Fast builds** - Parallel execution
- **Easy rollbacks** - Independent versioning
- **Clear monitoring** - Per-component status

## Architecture

### Workflow Structure

```
.github/workflows/
├── terraform.yml                    # Infrastructure deployment
├── deploy-orchestrator.yml          # Service: Orchestrator
├── deploy-task-manager.yml          # Service: Task Manager
├── deploy-results-analysis.yml      # Service: Results Analysis
├── deploy-decisions-engine.yml      # Service: Decisions Engine
├── deploy-agent-evolution.yml       # Service: Agent Evolution
├── deploy-dna-engine.yml            # Job: DNA Engine
├── deploy-first-interpretation.yml  # Job: First Interpretation
├── deploy-second-interpretation.yml # Job: Second Interpretation
├── deploy-micro-prompts.yml         # Job: Micro-Prompts
└── deploy-med-to-deep.yml           # Job: MED-to-DEEP
```

### Trigger Strategy

Each workflow triggers on:
1. **Path-based push** - Only when relevant files change
2. **Manual dispatch** - For on-demand deployments

Example (Orchestrator):
```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'backend/services/orchestrator/**'
      - 'backend/shared/**'
      - '.github/workflows/deploy-orchestrator.yml'
  workflow_dispatch:
```

## Deployment Flow

### Services (Cloud Run Services)

1. **Checkout code**
2. **Authenticate to GCP**
3. **Configure Docker** for Artifact Registry
4. **Build image** with SHA and latest tags
5. **Push image** to Artifact Registry
6. **Deploy to Cloud Run** with configuration
7. **Health check** to verify deployment

### Jobs (Cloud Run Jobs)

1. **Checkout code**
2. **Authenticate to GCP**
3. **Configure Docker** for Artifact Registry
4. **Build image** with SHA and latest tags
5. **Push image** to Artifact Registry
6. **Update/Create job** in Cloud Run
7. **Verify job** configuration

## Configuration

### Required Secrets

Set these in GitHub repository settings (`Settings > Secrets and variables > Actions`):

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud Project ID | `thrive-system1` |
| `GCP_SA_KEY` | Service Account JSON key | `{"type": "service_account", ...}` |

### Environment Variables

Each workflow uses:
- `PROJECT_ID`: From `GCP_PROJECT_ID` secret
- `REGION`: `us-central1` (hardcoded)
- `SERVICE_NAME` or `JOB_NAME`: Component-specific

## Manual Deployment

### Via GitHub UI

1. Go to **Actions** tab
2. Select the workflow (e.g., "Deploy Orchestrator Service")
3. Click **Run workflow**
4. Select branch (usually `main`)
5. Click **Run workflow** button

### Via GitHub CLI

```bash
# Deploy a service
gh workflow run deploy-orchestrator.yml

# Deploy a job
gh workflow run deploy-dna-engine.yml

# Deploy infrastructure
gh workflow run terraform.yml
```

## Monitoring

### Workflow Status

Check workflow runs:
- **GitHub UI**: Actions tab
- **CLI**: `gh run list --workflow=deploy-orchestrator.yml`

### Deployment Status

Check Cloud Run status:
```bash
# Services
gcloud run services list --region=us-central1

# Jobs
gcloud run jobs list --region=us-central1
```

### Logs

View logs:
```bash
# Service logs
gcloud run services logs read nucleus-orchestrator --region=us-central1

# Job execution logs
gcloud run jobs executions logs read JOB_EXECUTION_NAME --region=us-central1
```

## Rollback

### Service Rollback

```bash
# List revisions
gcloud run revisions list --service=nucleus-orchestrator --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic nucleus-orchestrator \
  --to-revisions=REVISION_NAME=100 \
  --region=us-central1
```

### Job Rollback

```bash
# Update job to previous image
gcloud run jobs update nucleus-dna-engine \
  --image=us-central1-docker.pkg.dev/PROJECT_ID/nucleus/nucleus-dna-engine:PREVIOUS_SHA \
  --region=us-central1
```

## Best Practices

### 1. Atomic Changes

Make changes to one component at a time when possible. This:
- Simplifies debugging
- Enables easy rollbacks
- Clarifies change impact

### 2. Test Locally

Before pushing:
```bash
# Build Docker image
docker build -f backend/services/orchestrator/Dockerfile -t test-orchestrator .

# Run locally
docker run -p 8080:8080 test-orchestrator
```

### 3. Monitor Deployments

After deployment:
1. Check workflow logs for errors
2. Verify health endpoint
3. Check Cloud Run logs for runtime errors

### 4. Use Manual Dispatch for Sensitive Changes

For critical updates:
1. Use `workflow_dispatch` instead of auto-deploy
2. Review changes carefully
3. Monitor closely after deployment

## Troubleshooting

### Build Failures

**Symptom**: Docker build fails

**Common causes**:
- Missing dependencies in `requirements.txt`
- Incorrect Dockerfile paths
- Syntax errors in Python code

**Solution**:
1. Check workflow logs for specific error
2. Test build locally
3. Fix issue and push

### Deployment Failures

**Symptom**: Cloud Run deployment fails

**Common causes**:
- Insufficient permissions
- Invalid environment variables
- Missing secrets
- Resource limits exceeded

**Solution**:
1. Check IAM permissions for service account
2. Verify secrets are set in GitHub
3. Check Cloud Run quotas

### Health Check Failures

**Symptom**: Deployment succeeds but health check fails

**Common causes**:
- Service not listening on correct port
- `/health` endpoint not implemented
- Database connection issues

**Solution**:
1. Check service logs in Cloud Run
2. Verify port configuration (default: 8080)
3. Test `/health` endpoint manually

## Infrastructure Deployment

### Terraform Workflow

The `terraform.yml` workflow:
1. Runs on changes to `infrastructure/terraform/**`
2. Validates and formats Terraform code
3. Plans changes
4. Applies changes (on main branch only)
5. Outputs results as artifact

### Manual Infrastructure Update

```bash
# Trigger via GitHub CLI
gh workflow run terraform.yml

# Or use Terraform locally
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Security

### Secrets Management

- **Never** commit secrets to Git
- Use GitHub Secrets for sensitive data
- Use GCP Secret Manager for runtime secrets
- Rotate service account keys regularly

### Image Security

- Images are private in Artifact Registry
- Only service account can pull images
- SHA tags ensure immutability
- Regular security scanning recommended

## Performance

### Build Optimization

Current optimizations:
- Multi-stage Docker builds (if applicable)
- Layer caching
- Parallel workflow execution

Future improvements:
- Docker layer caching in GitHub Actions
- Shared base images
- Build matrix for multiple regions

### Deployment Speed

Average deployment times:
- **Services**: 3-5 minutes
- **Jobs**: 2-4 minutes
- **Infrastructure**: 5-10 minutes

## Next Steps

1. **Add integration tests** to workflows
2. **Implement staging environment** for pre-production testing
3. **Add automated rollback** on health check failure
4. **Set up Slack/email notifications** for deployment status
5. **Implement blue-green deployments** for zero-downtime updates

---

**CI/CD Status:** ✅ **PRODUCTION READY**

All 11 workflows are configured and ready for deployment.
