# Intelligent Agent Factory Service

**Part of NUCLEUS Phase 2: "The Living Organism"**

## Overview

The Intelligent Agent Factory is an autonomous service that continuously monitors the NUCLEUS ecosystem to detect needs for new AI agents and automatically spawns them. It closes the evolution loop by ensuring the system can grow and adapt to new demands without human intervention.

## Architecture

### Need Detection Engine

The factory uses four detection mechanisms to identify opportunities for new agents:

#### 1. Coverage Gap Detection
- **What it detects**: Entities without dedicated agents
- **How it works**: Analyzes entity relationships and identifies high-connectivity entities lacking agent coverage
- **Priority**: High for entities with >10 relationships
- **Confidence**: Based on relationship count and entity importance

#### 2. High Demand Pattern Detection
- **What it detects**: Usage patterns indicating need for specialized agents
- **How it works**: Analyzes request logs and metrics to find frequently accessed areas
- **Priority**: Medium to High
- **Confidence**: Based on request frequency and growth rate

#### 3. Failure Pattern Detection
- **What it detects**: Systematic failures suggesting need for specialized support
- **How it works**: Analyzes agent health data to find common failure patterns
- **Priority**: High
- **Confidence**: Based on failure frequency and impact

#### 4. Emerging Topic Detection
- **What it detects**: New topics gaining traction
- **How it works**: Analyzes entity creation velocity and growth patterns
- **Priority**: Medium
- **Confidence**: Based on growth velocity and consistency

### LLM-Powered Analysis

Each detected need is analyzed by GPT-4.1-mini to generate:
- Agent name and type
- Detailed purpose statement
- Required capabilities
- Specialization strategy
- Expected impact
- Priority justification
- Configuration parameters

### Agent Factory

Creates new agents with:
- Unique ID generation
- Database record creation
- Lifecycle event logging
- Need fulfillment tracking
- Entity linking

## API Endpoints

### POST /detect-needs

Detect needs for new agents based on system analysis.

**Request Body:**
```json
{
  "lookback_days": 7,
  "min_confidence": 0.7
}
```

**Response:**
```json
[
  {
    "need_id": "uuid",
    "need_type": "coverage_gap",
    "description": "Entity 'X' has 15 relationships but no dedicated agent",
    "priority": "high",
    "confidence": 0.85,
    "evidence": [
      "Entity has 15 relationships",
      "No active agent for entity type: company",
      "High connectivity suggests importance"
    ],
    "suggested_agent": {
      "agent_name": "Company X Intelligence Agent",
      "agent_type": "entity_specialist",
      "purpose": "Monitor and analyze Company X",
      "capabilities": ["research", "analysis", "monitoring"],
      "specialization": "Deep knowledge of Company X ecosystem",
      "expected_impact": "Improved coverage of Company X queries",
      "priority_justification": "High relationship count indicates importance",
      "configuration": {}
    },
    "detected_at": "2025-12-11T16:00:00Z"
  }
]
```

### POST /spawn-agent

Manually spawn a new agent.

**Request Body:**
```json
{
  "need_id": "uuid",
  "agent_type": "entity_specialist",
  "agent_name": "Company X Agent",
  "description": "Specialized agent for Company X",
  "capabilities": {
    "research": true,
    "analysis": true
  },
  "configuration": {
    "focus_area": "technology"
  }
}
```

**Response:**
```json
{
  "agent_id": "uuid",
  "agent_name": "Company X Agent",
  "agent_type": "entity_specialist",
  "status": "created",
  "message": "Agent created successfully"
}
```

### POST /auto-spawn

Automatically spawn agents for high-priority pending needs.

**Response:**
```json
{
  "spawned_count": 3,
  "agents": [
    {
      "agent_id": "uuid",
      "agent_name": "Agent Name",
      "agent_type": "type",
      "status": "created",
      "message": "Agent created successfully"
    }
  ]
}
```

### GET /needs

Get detected needs with optional filtering.

**Query Parameters:**
- `status`: Filter by status (pending, fulfilled, rejected)
- `limit`: Maximum number of results (default: 50)

**Response:**
```json
[
  {
    "need_id": "uuid",
    "need_type": "coverage_gap",
    "description": "...",
    "priority": "high",
    "confidence": 0.85,
    "status": "pending",
    "suggested_agent": {...},
    "detected_at": "2025-12-11T16:00:00Z"
  }
]
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "intelligent-agent-factory",
  "timestamp": "2025-12-11T16:00:00Z"
}
```

## Database Schema

### Tables Used

#### `assembly.agent_needs`
- Stores detected needs
- Tracks fulfillment status
- Links to created agents

#### `assembly.agents`
- Stores created agents
- Links to entities
- Tracks configuration

#### `assembly.agent_lifecycle_events`
- Logs agent creation events
- Tracks spawn triggers
- Stores metadata

#### `dna.entities`
- Source for coverage analysis
- Entity relationship data
- Creation patterns

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...

# Optional
PORT=8080
```

## Deployment

### Manual Deployment

```bash
# Build and push Docker image
docker build -t gcr.io/PROJECT_ID/intelligent-agent-factory .
docker push gcr.io/PROJECT_ID/intelligent-agent-factory

# Deploy to Cloud Run
gcloud run deploy intelligent-agent-factory \
  --image=gcr.io/PROJECT_ID/intelligent-agent-factory \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-secrets="DATABASE_URL=DATABASE_URL:latest" \
  --set-secrets="OPENAI_API_KEY=OPENAI_API_KEY:latest" \
  --memory=1Gi \
  --cpu=1
```

### Automatic Deployment (GitHub Actions)

Triggered automatically on push to `main` branch when files in:
- `backend/services/intelligent-agent-factory/**`
- `backend/shared/**`
- `.github/workflows/deploy-intelligent-agent-factory.yml`

## Usage Patterns

### Pattern 1: Periodic Need Detection

Run need detection daily or weekly to identify new opportunities:

```bash
curl -X POST https://intelligent-agent-factory-xxx.run.app/detect-needs \
  -H "Content-Type: application/json" \
  -d '{"lookback_days": 7, "min_confidence": 0.7}'
```

### Pattern 2: Automatic Spawning

Let the system automatically spawn high-priority agents:

```bash
curl -X POST https://intelligent-agent-factory-xxx.run.app/auto-spawn
```

### Pattern 3: Manual Review and Spawn

1. Detect needs
2. Review suggestions
3. Manually spawn selected agents

```bash
# 1. Detect needs
curl -X POST https://intelligent-agent-factory-xxx.run.app/detect-needs

# 2. Review needs
curl https://intelligent-agent-factory-xxx.run.app/needs?status=pending

# 3. Spawn specific agent
curl -X POST https://intelligent-agent-factory-xxx.run.app/spawn-agent \
  -H "Content-Type: application/json" \
  -d '{
    "need_id": "uuid",
    "agent_type": "entity_specialist",
    "agent_name": "New Agent",
    "description": "Purpose",
    "capabilities": {},
    "configuration": {}
  }'
```

## Integration with Other Services

### Agent Health Monitor
- Provides health data for failure pattern detection
- Triggers need detection when agents consistently fail

### Agent Lifecycle Manager
- Consumes needs to decide on agent improvements
- Triggers factory when split decisions are made

### Agent Evolution Service
- Uses factory suggestions for agent improvements
- Provides feedback on agent effectiveness

## Monitoring

### Key Metrics

- **Needs detected per day**: Track detection rate
- **Confidence distribution**: Monitor quality of detections
- **Spawn success rate**: Track agent creation success
- **Need fulfillment time**: Time from detection to spawn
- **Agent survival rate**: How many spawned agents remain active

### Logs

View service logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=intelligent-agent-factory" --limit=50
```

## Future Enhancements

### Phase 3: Advanced Detection
- Machine learning-based pattern detection
- Predictive need detection
- Cross-agent collaboration analysis

### Phase 4: Autonomous Evolution
- Self-improving detection algorithms
- Automatic agent template generation
- Dynamic capability assignment

### Phase 5: Ecosystem Optimization
- Load balancing across agents
- Automatic agent consolidation
- Performance-based agent pruning

## Development

### Local Testing

```bash
# Set environment variables
export DATABASE_URL="postgresql://..."
export OPENAI_API_KEY="sk-..."

# Run service
python main.py
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Detect needs
curl -X POST http://localhost:8080/detect-needs \
  -H "Content-Type: application/json" \
  -d '{"lookback_days": 7}'

# Get needs
curl http://localhost:8080/needs
```

## Troubleshooting

### Common Issues

1. **No needs detected**
   - Check database has entities and agents
   - Verify lookback period has activity
   - Lower min_confidence threshold

2. **LLM API errors**
   - Verify OPENAI_API_KEY is correct
   - Check API quota and rate limits
   - Review prompt formatting

3. **Agent creation fails**
   - Check database schema is up to date
   - Verify required fields are provided
   - Review database logs for errors

4. **Low confidence scores**
   - Increase lookback period
   - Ensure sufficient data exists
   - Review detection logic thresholds

## Support

For issues or questions:
- Check logs: `gcloud logging read ...`
- Review needs table: Query `assembly.agent_needs`
- Contact: NUCLEUS team
