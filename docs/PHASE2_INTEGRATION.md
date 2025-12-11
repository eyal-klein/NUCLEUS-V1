# NUCLEUS Phase 2: Integration Guide

**"The Living Organism" - Complete Integration Documentation**

## Overview

Phase 2 transforms NUCLEUS into a self-managing biological system with four core components working together to create an autonomous, self-evolving AI ecosystem.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NUCLEUS ECOSYSTEM                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Agent Health    │─────▶│  Agent Lifecycle │            │
│  │  Monitor         │      │  Manager         │            │
│  │  (Service)       │      │  (Daily Job)     │            │
│  └──────────────────┘      └──────────────────┘            │
│         │                           │                        │
│         │ Health Data               │ Lifecycle Events       │
│         ▼                           ▼                        │
│  ┌─────────────────────────────────────────────┐            │
│  │         Database (PostgreSQL)                │            │
│  │  - agent_health                              │            │
│  │  - agent_lifecycle_events                    │            │
│  │  - agent_needs                               │            │
│  └─────────────────────────────────────────────┘            │
│         ▲                           ▲                        │
│         │ Need Detection            │ Agent Creation         │
│         │                           │                        │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Intelligent     │─────▶│  New Agents      │            │
│  │  Agent Factory   │      │  (Spawned)       │            │
│  │  (Service)       │      │                  │            │
│  └──────────────────┘      └──────────────────┘            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Agent Health Monitor Service

**Purpose**: Continuously monitors and scores agent health

**Deployment**: Cloud Run Service
**URL**: `https://agent-health-monitor-xxx.run.app`

**Key Features**:
- 8-component health scoring system
- Real-time health calculation
- Trend analysis (improving/stable/declining)
- Risk level assessment (low/medium/high/critical)
- Automated recommendations

**API Endpoints**:
- `POST /calculate` - Calculate health for specific agent
- `GET /agents/{id}/health` - Get agent health history
- `GET /agents/health/summary` - Get system-wide health summary
- `GET /health` - Service health check

**Database Tables**:
- `assembly.agent_health` - Health records
- `assembly.agent_health_latest` - Latest health per agent (view)
- `assembly.agent_health_summary` - Aggregated statistics (view)

### 2. Agent Lifecycle Manager Job

**Purpose**: Daily job that manages agent lifecycles based on health

**Deployment**: Cloud Run Job (Scheduled)
**Schedule**: Daily at 3:00 AM UTC

**Key Features**:
- Apoptosis (shutdown weak agents)
- Evolution (improve mediocre agents)
- Mitosis (split successful agents)
- LLM-powered decision making
- Lifecycle event logging

**Decision Thresholds**:
- Shutdown: health < 0.3
- Improve: health < 0.6
- Split: health > 0.85

**Database Tables**:
- `assembly.agent_lifecycle_events` - All lifecycle events
- Uses `assembly.agent_health_latest` for decisions

### 3. Intelligent Agent Factory Service

**Purpose**: Detects needs and spawns new agents automatically

**Deployment**: Cloud Run Service
**URL**: `https://intelligent-agent-factory-xxx.run.app`

**Key Features**:
- 4 need detection engines
- LLM-powered agent specification
- Automatic agent creation
- Need fulfillment tracking

**Detection Engines**:
1. Coverage Gap Detection - Entities without agents
2. High Demand Pattern Detection - Usage patterns
3. Failure Pattern Detection - Systematic failures
4. Emerging Topic Detection - Growth trends

**API Endpoints**:
- `POST /detect-needs` - Detect needs for new agents
- `POST /spawn-agent` - Create new agent manually
- `POST /auto-spawn` - Auto-spawn high-priority agents
- `GET /needs` - List detected needs
- `GET /health` - Service health check

**Database Tables**:
- `assembly.agent_needs` - Detected needs
- `assembly.agents` - Created agents
- `assembly.agent_lifecycle_events` - Spawn events

## Data Flow

### Flow 1: Health Monitoring → Lifecycle Management

```
1. Agent Health Monitor calculates health scores
   ↓
2. Stores in agent_health table
   ↓
3. Agent Lifecycle Manager queries agent_health_latest (daily at 3 AM)
   ↓
4. Makes decisions: shutdown/improve/split/maintain
   ↓
5. Executes actions on agents
   ↓
6. Logs events to agent_lifecycle_events
```

### Flow 2: Need Detection → Agent Creation

```
1. Intelligent Agent Factory detects needs
   ↓
2. Analyzes with LLM for agent specification
   ↓
3. Stores in agent_needs table
   ↓
4. Auto-spawn or manual review
   ↓
5. Creates new agent in agents table
   ↓
6. Logs spawn event to agent_lifecycle_events
   ↓
7. Updates need status to 'fulfilled'
```

### Flow 3: Complete Evolution Loop

```
1. System runs with agents
   ↓
2. Health Monitor tracks performance
   ↓
3. Lifecycle Manager improves/removes weak agents
   ↓
4. Factory detects gaps and needs
   ↓
5. New agents spawned to fill gaps
   ↓
6. Loop continues autonomously
```

## Database Schema

### Migration 006: Agent Health Tables

```sql
-- Core health tracking
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

-- Lifecycle event tracking
CREATE TABLE assembly.agent_lifecycle_events (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES assembly.agents(id),
    event_type VARCHAR(50),
    reason TEXT,
    before_state JSONB,
    after_state JSONB,
    triggered_by VARCHAR(100),
    triggered_by_id UUID,
    metadata JSONB,
    occurred_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Need detection and fulfillment
CREATE TABLE assembly.agent_needs (
    id UUID PRIMARY KEY,
    need_type VARCHAR(50),
    description TEXT,
    priority VARCHAR(20),
    confidence DECIMAL(3,2),
    evidence JSONB,
    metadata JSONB,
    suggested_agent_spec JSONB,
    status VARCHAR(20),
    detected_at TIMESTAMP,
    fulfilled_at TIMESTAMP,
    created_agent_id UUID REFERENCES assembly.agents(id),
    created_at TIMESTAMP
);

-- Views for easy querying
CREATE VIEW assembly.agent_health_latest AS ...
CREATE VIEW assembly.agent_health_summary AS ...
```

## Deployment Status

### Services Deployed

| Service | Status | URL | Version |
|---------|--------|-----|---------|
| Agent Health Monitor | ✅ Deployed | `agent-health-monitor-xxx.run.app` | Commit 1567e17 |
| Intelligent Agent Factory | ✅ Deployed | `intelligent-agent-factory-xxx.run.app` | Commit e27cacf |

### Jobs Deployed

| Job | Status | Schedule | Version |
|-----|--------|----------|---------|
| Agent Lifecycle Manager | ✅ Deployed | Daily 3:00 AM UTC | Commit 285ef3d |

### Database Migrations

| Migration | Status | Applied |
|-----------|--------|---------|
| 006_add_agent_health_tables.sql | ✅ Applied | Yes |

## Configuration

### Environment Variables

All services require:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# OpenAI API
OPENAI_API_KEY=sk-...

# Service-specific
PROJECT_ID=thrive-system1
```

### Lifecycle Manager Thresholds

```bash
SHUTDOWN_THRESHOLD=0.3
IMPROVE_THRESHOLD=0.6
SPLIT_THRESHOLD=0.85
CRITICAL_RISK_ACTION=shutdown
```

## Testing

### 1. Test Health Monitor

```bash
# Health check
curl https://agent-health-monitor-xxx.run.app/health

# Calculate health for an agent
curl -X POST https://agent-health-monitor-xxx.run.app/calculate \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "uuid"}'

# Get health summary
curl https://agent-health-monitor-xxx.run.app/agents/health/summary
```

### 2. Test Lifecycle Manager

```bash
# Manual execution
gcloud run jobs execute agent-lifecycle-manager --region=us-central1

# Check logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=agent-lifecycle-manager" --limit=50

# Verify lifecycle events
psql $DATABASE_URL -c "SELECT * FROM assembly.agent_lifecycle_events ORDER BY occurred_at DESC LIMIT 10;"
```

### 3. Test Agent Factory

```bash
# Health check
curl https://intelligent-agent-factory-xxx.run.app/health

# Detect needs
curl -X POST https://intelligent-agent-factory-xxx.run.app/detect-needs \
  -H "Content-Type: application/json" \
  -d '{"lookback_days": 7, "min_confidence": 0.7}'

# Get needs
curl https://intelligent-agent-factory-xxx.run.app/needs?status=pending

# Auto-spawn agents
curl -X POST https://intelligent-agent-factory-xxx.run.app/auto-spawn
```

## Monitoring

### Key Metrics to Track

**Health Monitor**:
- Health calculation requests per day
- Average health score across system
- Distribution of risk levels
- Trend patterns (improving vs declining)

**Lifecycle Manager**:
- Decisions per execution (shutdown/improve/split/maintain)
- Agent survival rate after decisions
- Execution time and success rate
- LLM API usage and costs

**Agent Factory**:
- Needs detected per week
- Confidence distribution
- Spawn success rate
- Agent survival rate (spawned agents still active after 30 days)

### Logging

All services use structured logging:

```bash
# View all Phase 2 logs
gcloud logging read "resource.type=cloud_run_revision AND (
  resource.labels.service_name=agent-health-monitor OR
  resource.labels.service_name=intelligent-agent-factory
)" --limit=100

# View job logs
gcloud logging read "resource.type=cloud_run_job AND 
  resource.labels.job_name=agent-lifecycle-manager" --limit=100
```

### Alerts

Recommended Cloud Monitoring alerts:

1. **Health Monitor**: Response time > 5s
2. **Lifecycle Manager**: Job execution failure
3. **Agent Factory**: Spawn failure rate > 10%
4. **Database**: Connection pool exhaustion
5. **System**: Average health score < 0.5

## Integration Patterns

### Pattern 1: Continuous Health Monitoring

```
Every request to any agent
  ↓
Health Monitor tracks metrics
  ↓
Calculates health score
  ↓
Stores in database
  ↓
Available for Lifecycle Manager
```

### Pattern 2: Daily Lifecycle Management

```
3:00 AM UTC daily
  ↓
Lifecycle Manager wakes up
  ↓
Queries latest health data
  ↓
Makes LLM-powered decisions
  ↓
Executes actions
  ↓
Logs events
```

### Pattern 3: On-Demand Need Detection

```
Triggered by:
- Manual API call
- Scheduled job (future)
- Event (agent shutdown, low health)
  ↓
Factory detects needs
  ↓
LLM analyzes and suggests specs
  ↓
Stores needs
  ↓
Auto-spawn or manual review
```

### Pattern 4: Event-Driven Spawning

```
High-priority need detected
  ↓
Confidence > 0.8
  ↓
Auto-spawn triggered
  ↓
Agent created
  ↓
Lifecycle event logged
  ↓
Need marked fulfilled
```

## Operational Procedures

### Daily Operations

1. **Morning Check** (9:00 AM)
   - Review Lifecycle Manager execution logs
   - Check any shutdown decisions
   - Verify no critical errors

2. **Weekly Review** (Monday)
   - Review health trends
   - Analyze spawned agents
   - Check need detection patterns

3. **Monthly Analysis**
   - Agent survival rates
   - System health trends
   - Cost analysis
   - Optimization opportunities

### Incident Response

**Scenario 1: Mass Agent Shutdowns**
```
1. Check Lifecycle Manager logs
2. Review health scores leading to shutdowns
3. Identify root cause (data issue, bug, actual poor performance)
4. Adjust thresholds if needed
5. Manually reactivate agents if false positive
```

**Scenario 2: No Needs Detected**
```
1. Verify Factory is running
2. Check database has sufficient data
3. Review detection logic thresholds
4. Manually trigger detection with lower confidence
```

**Scenario 3: Spawn Failures**
```
1. Check Factory logs for errors
2. Verify database connectivity
3. Check LLM API status
4. Review agent specifications
5. Manually retry failed spawns
```

## Future Enhancements

### Phase 2.1: Enhanced Intelligence
- Machine learning-based health prediction
- Anomaly detection in agent behavior
- Automated threshold optimization
- Cross-agent collaboration analysis

### Phase 2.2: Advanced Lifecycle
- Gradual shutdown with migration
- A/B testing for improvements
- Automatic rollback on degradation
- Agent versioning and history

### Phase 2.3: Smart Factory
- Predictive need detection
- Template-based agent generation
- Automatic capability discovery
- Load-based scaling

### Phase 2.4: Ecosystem Optimization
- Multi-agent coordination
- Resource optimization
- Cost-performance balancing
- Self-healing capabilities

## Troubleshooting

### Common Issues

**Issue**: Health scores not updating
- Check Health Monitor is running
- Verify database connectivity
- Review calculation logic
- Check for errors in logs

**Issue**: Lifecycle Manager not executing
- Verify Cloud Scheduler is enabled
- Check job permissions
- Review execution logs
- Manually trigger for testing

**Issue**: Factory not detecting needs
- Ensure sufficient data exists
- Lower confidence threshold
- Check detection queries
- Review LLM API status

**Issue**: Spawned agents not working
- Verify agent configuration
- Check entity linking
- Review capabilities
- Test agent manually

## Support

For issues or questions:
- **Logs**: Use `gcloud logging read` commands above
- **Database**: Query health, lifecycle, and needs tables
- **Monitoring**: Check Cloud Monitoring dashboards
- **Team**: Contact NUCLEUS development team

## Summary

Phase 2 "The Living Organism" successfully transforms NUCLEUS into an autonomous, self-evolving system:

✅ **Agent Health Monitor** - Continuous health tracking
✅ **Agent Lifecycle Manager** - Automatic lifecycle management
✅ **Intelligent Agent Factory** - Autonomous agent creation
✅ **Database Schema** - Complete data model
✅ **Integration** - All components working together
✅ **Deployment** - Production-ready on Cloud Run
✅ **Documentation** - Comprehensive guides

**The system is now alive and can manage itself! 🎉**
