# Agent Lifecycle Manager Job

**Part of NUCLEUS Phase 2: "The Living Organism"**

## Overview

The Agent Lifecycle Manager is a daily job that automatically manages the lifecycle of AI agents in the NUCLEUS ecosystem. It implements three biological processes:

1. **Apoptosis (Shutdown)**: Deactivates weak or failing agents
2. **Evolution (Improvement)**: Enhances mediocre agents with optimization recommendations
3. **Mitosis (Splitting)**: Splits successful agents into specialized variants

## Architecture

### Decision Engines

#### 1. Shutdown Engine
- **Trigger**: Health score < 0.3 OR critical risk level
- **Process**:
  - Analyzes agent health metrics
  - Consults LLM for decision validation
  - Deactivates agent if confirmed
  - Logs lifecycle event
- **Safety**: Requires high confidence (0.85+) for shutdown

#### 2. Improvement Engine
- **Trigger**: Health score 0.3-0.6 OR declining trend
- **Process**:
  - Analyzes failure patterns
  - Generates improvement recommendations via LLM
  - Creates action plan
  - Logs improvement event
- **Future**: Will trigger automatic optimization

#### 3. Split Engine
- **Trigger**: Health score > 0.85 AND high usage
- **Process**:
  - Analyzes usage patterns
  - Identifies specialization opportunities via LLM
  - Creates split plan
  - Logs split event
- **Future**: Will create specialized agent variants

### LLM Integration

Uses GPT-4.1-mini for intelligent decision-making:
- Analyzes agent health data
- Provides structured recommendations
- Validates lifecycle decisions
- Suggests specific actions

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...

# Optional (with defaults)
SHUTDOWN_THRESHOLD=0.3      # Health score below this triggers shutdown consideration
IMPROVE_THRESHOLD=0.6       # Health score below this triggers improvement consideration
SPLIT_THRESHOLD=0.85        # Health score above this triggers split consideration
CRITICAL_RISK_ACTION=shutdown  # Action for critical risk: 'shutdown' or 'improve'
```

### Thresholds

| Threshold | Default | Description |
|-----------|---------|-------------|
| `SHUTDOWN_THRESHOLD` | 0.3 | Agents below this health score are considered for shutdown |
| `IMPROVE_THRESHOLD` | 0.6 | Agents below this health score are considered for improvement |
| `SPLIT_THRESHOLD` | 0.85 | Agents above this health score are considered for splitting |

## Deployment

### Manual Deployment

```bash
# Build and push Docker image
docker build -t gcr.io/PROJECT_ID/agent-lifecycle-manager .
docker push gcr.io/PROJECT_ID/agent-lifecycle-manager

# Deploy to Cloud Run Job
gcloud run jobs deploy agent-lifecycle-manager \
  --image=gcr.io/PROJECT_ID/agent-lifecycle-manager \
  --region=us-central1 \
  --set-env-vars="DATABASE_URL=..." \
  --set-env-vars="OPENAI_API_KEY=..." \
  --max-retries=3 \
  --task-timeout=30m
```

### Automatic Deployment (GitHub Actions)

1. **Deploy Job**: Triggered on push to `main` branch
   - Workflow: `.github/workflows/deploy-agent-lifecycle-manager.yml`
   - Builds Docker image
   - Deploys to Cloud Run Job

2. **Schedule Job**: Manual trigger to set up Cloud Scheduler
   - Workflow: `.github/workflows/schedule-agent-lifecycle-manager.yml`
   - Creates Cloud Scheduler job
   - Default: Daily at 3 AM UTC

## Execution

### Manual Execution

```bash
# Run job once
gcloud run jobs execute agent-lifecycle-manager --region=us-central1
```

### Scheduled Execution

The job runs automatically via Cloud Scheduler:
- **Schedule**: Daily at 3 AM UTC
- **Timeout**: 30 minutes
- **Retries**: Up to 3 times on failure

## Database Schema

### Tables Used

#### `assembly.agents`
- Source of agent data
- Updated with `is_active` flag on shutdown

#### `assembly.agent_health_latest` (view)
- Latest health scores for each agent
- Used for decision-making

#### `assembly.agent_lifecycle_events`
- Logs all lifecycle events
- Stores decisions and recommendations

### Lifecycle Events

Each decision is logged with:
- `agent_id`: Agent affected
- `event_type`: 'shutdown', 'improve', 'split', or 'maintain'
- `reason`: Human-readable explanation
- `triggered_by`: 'lifecycle_manager'
- `metadata`: JSON with confidence and recommendations
- `occurred_at`: Timestamp

## Monitoring

### Logs

View job execution logs:
```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=agent-lifecycle-manager" --limit=50
```

### Metrics

Key metrics to monitor:
- **Execution time**: Should complete in < 5 minutes for 100 agents
- **Decision distribution**: Balance of shutdown/improve/split/maintain
- **Error rate**: Should be < 1%
- **LLM API calls**: One per non-maintain decision

## Future Enhancements

### Phase 3: Intelligent Agent Factory
- Automatic agent creation based on detected needs
- Integration with agent templates
- Load-based spawning

### Phase 4: Enhanced Evolution
- Automatic prompt optimization
- Parameter tuning based on performance
- A/B testing of improvements

### Phase 5: Advanced Mitosis
- Automatic creation of specialized agents
- Load balancing across variants
- Usage pattern analysis

## Development

### Local Testing

```bash
# Set environment variables
export DATABASE_URL="postgresql://..."
export OPENAI_API_KEY="sk-..."

# Run job
python main.py
```

### Testing with Mock Data

```python
# TODO: Add test script with mock agents
```

## Troubleshooting

### Common Issues

1. **No agents processed**
   - Check that agents exist in `assembly.agents`
   - Verify health monitor has run and populated health data

2. **LLM API errors**
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API quota and rate limits

3. **Database connection errors**
   - Verify `DATABASE_URL` is correct
   - Check network connectivity from Cloud Run

4. **Job timeout**
   - Increase `task-timeout` in deployment
   - Optimize query performance
   - Consider batch processing for large agent counts

## Support

For issues or questions:
- Check logs: `gcloud logging read ...`
- Review health monitor data: Query `assembly.agent_health_latest`
- Contact: NUCLEUS team
