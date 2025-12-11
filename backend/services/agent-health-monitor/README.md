# Agent Health Monitor Service

**The Sensory System of NUCLEUS**

**Type**: Cloud Run Service  
**Deployment**: Automated via GitHub Actions  
**Status**: ✅ Production Ready

---

## Overview

The Agent Health Monitor is the sensory system of NUCLEUS. It continuously monitors and scores the health of all agents in the system, providing real-time insights into agent performance, trends, and risks.

## Purpose

In a living organism, the sensory system detects changes in the environment and internal state. Similarly, the Agent Health Monitor tracks agent performance and provides the data needed for the Lifecycle Manager to make informed decisions about agent evolution.

## Architecture

```
Agent Performance Data
    ↓
Health Monitor (this service)
    ↓
Health Score Calculation (8 metrics)
    ↓
Database (agent_health table)
    ↓
Lifecycle Manager (consumes health data)
```

## Health Scoring System

The health score is a composite of **8 metrics**, each weighted to reflect its importance:

1. **Usage Frequency** (20%): How often the agent is used
2. **Success Rate** (30%): Percentage of successful requests
3. **User Satisfaction** (25%): Feedback scores from users
4. **Cost Efficiency** (15%): Value delivered per dollar spent
5. **Response Time** (10%): How quickly the agent responds
6. **Knowledge Freshness**: How up-to-date the agent's knowledge is
7. **Collaboration Score**: How well the agent works with other agents
8. **Total Requests**: Overall usage volume

**Formula**:
```
health_score = (usage * 0.2) + (success * 0.3) + (satisfaction * 0.25) + 
               (cost * 0.15) + (response_time * 0.1)
```

**Range**: 0.0 to 1.0 (higher is better)

## Features

### Real-Time Health Calculation

- Calculate health scores on-demand via API
- Store historical health data for trend analysis
- Identify improving, stable, or declining agents

### Risk Assessment

- **Low Risk**: health > 0.7
- **Medium Risk**: 0.5 < health ≤ 0.7
- **High Risk**: 0.3 < health ≤ 0.5
- **Critical Risk**: health ≤ 0.3

### Automated Recommendations

The service provides actionable recommendations based on health scores:

- **High health + high usage**: "Consider splitting this agent"
- **Low health**: "Review agent configuration and performance"
- **Declining trend**: "Investigate recent changes"

## API Endpoints

### POST /calculate

Calculate health for a specific agent.

**Request**:
```json
{
  "agent_id": "uuid"
}
```

**Response**:
```json
{
  "agent_id": "uuid",
  "health_score": 0.85,
  "trend": "improving",
  "risk_level": "low",
  "recommendations": ["Consider splitting this agent"],
  "metrics": {
    "usage_frequency": 0.9,
    "success_rate": 0.95,
    "user_satisfaction": 0.8,
    "cost_efficiency": 0.7,
    "response_time_score": 0.85
  }
}
```

### GET /agents/{id}/health

Get health history for a specific agent.

**Response**:
```json
{
  "agent_id": "uuid",
  "health_records": [
    {
      "health_score": 0.85,
      "calculated_at": "2025-12-11T10:00:00Z"
    }
  ]
}
```

### GET /agents/health/summary

Get system-wide health summary.

**Response**:
```json
{
  "total_agents": 100,
  "average_health": 0.75,
  "risk_distribution": {
    "low": 60,
    "medium": 30,
    "high": 8,
    "critical": 2
  },
  "trend_distribution": {
    "improving": 40,
    "stable": 50,
    "declining": 10
  }
}
```

### GET /health

Service health check.

**Response**:
```json
{
  "status": "healthy",
  "service": "agent-health-monitor",
  "timestamp": "2025-12-11T10:00:00Z"
}
```

## Database Schema

### agent_health Table

```sql
CREATE TABLE assembly.agent_health (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES assembly.agents(id),
    health_score DECIMAL(3,2),
    usage_frequency DECIMAL(3,2),
    success_rate DECIMAL(3,2),
    user_satisfaction DECIMAL(3,2),
    cost_efficiency DECIMAL(3,2),
    response_time_score DECIMAL(3,2),
    knowledge_freshness DECIMAL(3,2),
    collaboration_score DECIMAL(3,2),
    total_requests INTEGER,
    successful_requests INTEGER,
    failed_requests INTEGER,
    avg_response_time_ms DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    trend VARCHAR(20),
    risk_level VARCHAR(20),
    recommendations JSONB,
    calculated_at TIMESTAMP,
    created_at TIMESTAMP
);
```

### agent_health_latest View

```sql
CREATE VIEW assembly.agent_health_latest AS
SELECT DISTINCT ON (agent_id) *
FROM assembly.agent_health
ORDER BY agent_id, calculated_at DESC;
```

## Deployment

### Automated Deployment

Every push to `main` that changes files in `backend/services/agent-health-monitor/` triggers an automatic deployment via GitHub Actions.

**Workflow**: `.github/workflows/deploy-agent-health-monitor.yml`

### Manual Deployment

```bash
gcloud run deploy agent-health-monitor \
  --source backend/services/agent-health-monitor \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DATABASE_URL,OPENAI_API_KEY=$OPENAI_API_KEY
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key (for future LLM integration)
- `PROJECT_ID`: GCP project ID

### Resource Limits

- **Memory**: 512Mi
- **CPU**: 1
- **Timeout**: 60s
- **Concurrency**: 80

## Monitoring

### Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent-health-monitor" --limit=100
```

### Metrics

- **Request Count**: Number of health calculations per day
- **Response Time**: Average time to calculate health
- **Error Rate**: Percentage of failed calculations
- **Database Queries**: Number of database queries per request

## Integration

### With Lifecycle Manager

The Lifecycle Manager queries the `agent_health_latest` view to make decisions about agent lifecycles:

```python
# Lifecycle Manager queries this view
SELECT * FROM assembly.agent_health_latest WHERE health_score < 0.3;
```

### With Agent Factory

The Agent Factory uses health data to detect patterns of failure:

```python
# Factory detects systematic failures
SELECT agent_id, COUNT(*) as failure_count
FROM assembly.agent_health
WHERE health_score < 0.5
GROUP BY agent_id
HAVING COUNT(*) > 3;
```

## Troubleshooting

### Issue: Health scores are all 0

**Cause**: No performance data in the database.

**Solution**: Ensure agents are logging performance metrics to the database.

### Issue: Service returns 500 errors

**Cause**: Database connection failure.

**Solution**: Check `DATABASE_URL` environment variable and database connectivity.

### Issue: Health calculations are slow

**Cause**: Missing database indexes.

**Solution**: Run the migration to create indexes on `agent_health` table.

## Future Enhancements

- **Machine Learning**: Predict future health scores based on trends.
- **Anomaly Detection**: Automatically detect unusual patterns in health data.
- **Custom Metrics**: Allow users to define custom health metrics.
- **Real-Time Alerts**: Send notifications when health drops below thresholds.

---

**The sensory system is operational. The organism can feel.** 🧬
