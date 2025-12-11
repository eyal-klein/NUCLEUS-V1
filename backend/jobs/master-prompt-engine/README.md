# Master Prompt Engine

**NUCLEUS V2.0 - Phase 2 Enhancement**

## Purpose

The Master Prompt Engine is the bridge between DNA and Micro-Prompts. It synthesizes the complete DNA profile (all 19 tables) into a single, comprehensive **Master Prompt** that defines the core identity of the Entity.

## Architecture Position

```
DNA (19 tables)
    ↓
First Interpretation (Strategic)
    ↓
Second Interpretation (Tactical)
    ↓
[Master Prompt Engine] ← YOU ARE HERE
    ↓
Entity.master_prompt
    ↓
Micro-Prompts Engine
    ↓
Agent.system_prompt (per agent)
```

## What It Does

### Input
- **Complete DNA Profile**: All 19 DNA tables
  - Interests, Goals, Values
  - Personality Traits, Communication Styles
  - Decision Patterns, Work Habits
  - Relationships, Skills, Preferences
  - Constraints, Beliefs, Experiences
  - Emotions, Routines, Contexts
  - Evolution History
- **Strategic Interpretation**: From First Interpretation
- **Tactical Interpretation**: From Second Interpretation

### Process
1. Collects ALL DNA data from database
2. Reads both interpretations
3. Uses LLM (GPT-4.1-mini) to generate comprehensive Master Prompt
4. Stores in `Entity.master_prompt`
5. Publishes event for downstream processing

### Output
- **Entity.master_prompt**: 800-1200 word comprehensive identity prompt
- **Entity.master_prompt_version**: Version number
- **Entity.master_prompt_updated_at**: Timestamp

## Master Prompt Structure

The generated Master Prompt includes:

1. **IDENTITY** - Who is this Entity?
2. **COMMUNICATION STYLE** - How does this Entity communicate?
3. **DECISION-MAKING** - How does this Entity make decisions?
4. **GOALS & DIRECTION** - What does this Entity want to achieve?
5. **CONTEXT & RELATIONSHIPS** - Important context and relationships
6. **GUIDING PRINCIPLES** - 5-7 core non-negotiable principles

## Why This Matters

### Before (Without Master Prompt)
- Each agent gets a prompt generated directly from DNA
- No shared foundation across agents
- Inconsistent behavior between agents
- Hard to update all agents at once

### After (With Master Prompt)
- All agents share the same core identity
- Consistency across the entire agent ecosystem
- Easy to update: change Master Prompt → all agents inherit
- Clear separation: Entity identity vs. Agent role

## Deployment

### Environment Variables
- `ENTITY_ID`: UUID of the entity to process
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key
- `PROJECT_ID`: GCP project ID

### Cloud Run Job
```bash
gcloud run jobs create master-prompt-engine \
  --image gcr.io/thrive-system1/master-prompt-engine:latest \
  --region us-central1 \
  --set-env-vars DATABASE_URL=... \
  --service-account admin-master@thrive-system1.iam.gserviceaccount.com
```

### Execution
```bash
gcloud run jobs execute master-prompt-engine \
  --region us-central1 \
  --set-env-vars ENTITY_ID=<uuid>
```

## Integration

### Trigger
- Runs after Second Interpretation completes
- Can be triggered manually for updates
- Publishes `master_prompt_updated` event

### Downstream
- Micro-Prompts Engine listens for `master_prompt_updated` event
- Regenerates all agent prompts based on new Master Prompt

## Example Master Prompt Output

```
IDENTITY

This Entity is a strategic thinker with a strong analytical mindset...
[comprehensive identity description]

COMMUNICATION STYLE

Communication is direct, data-driven, and focused on outcomes...
[communication preferences]

DECISION-MAKING

Decisions are made through systematic analysis...
[decision patterns]

GOALS & DIRECTION

The primary goal is to...
[strategic and tactical objectives]

CONTEXT & RELATIONSHIPS

Key relationships include...
[important context]

GUIDING PRINCIPLES

1. Always prioritize data-driven decisions
2. Maintain transparency in all communications
3. ...
```

## Benefits

1. **Consistency**: All agents share the same foundational identity
2. **Efficiency**: Update once, propagate to all agents
3. **Clarity**: Clear separation between Entity identity and Agent role
4. **Scalability**: Easy to add new agents with consistent behavior
5. **Evolution**: Master Prompt evolves with DNA, agents stay aligned

## Technical Details

- **Language**: Python 3.11
- **LLM**: GPT-4.1-mini (via OpenAI API)
- **Database**: PostgreSQL (via SQLAlchemy)
- **Event Bus**: Google Cloud Pub/Sub
- **Deployment**: Google Cloud Run (Job)

## Monitoring

- Logs to Google Cloud Logging
- Publishes events to `evolution-events` topic
- Tracks version numbers for audit trail
