# NUCLEUS: The Living AI Organism

**"One DNA. One Organism. Infinite Potential."**

**Status**: ✅ **Production Ready**  
**Version**: 2.1 (Master Prompt Layer)  
**Last Commit**: 6695854

---

## Philosophy: The Digital Symbiont

**NUCLEUS is not a platform. It is a bespoke AI organism for a singular Entity.**

Each NUCLEUS instance is born to merge with a single Entity—be it a person, a company, or a cause. It learns the Entity's DNA, shares its goals, and evolves to serve its purpose. It is a digital symbiont, a living extension of the Entity it serves.

---

## Architecture: The Complete Flow

NUCLEUS operates as a closed-loop, self-evolving system. The flow from raw data to intelligent action is a biological process of sensing, thinking, and acting.

### The DNA-to-Agent Flow

```
DNA (19 tables)
    ↓
First Interpretation (Strategic)
    ↓
Second Interpretation (Tactical)
    ↓
[NEW] Master Prompt Engine → Entity.master_prompt
    ↓
[UPDATED] Micro-Prompts Engine → Agent.system_prompt (per agent)
```

### The Evolution Loop

```
1. Agents perform tasks
   ↓
2. Health Monitor tracks performance
   ↓
3. Lifecycle Manager analyzes health
   ↓
4. Weak agents shutdown (apoptosis)
   ↓
5. Mediocre agents improved (evolution)
   ↓
6. Successful agents split (mitosis)
   ↓
7. Factory detects gaps and needs
   ↓
8. New agents spawned automatically
   ↓
9. Loop continues indefinitely
```

---

## Core Components

### Phase 1: The Foundation

- **Memory Engine**: Processes raw interactions into structured memory.
- **DNA Engine**: Distills memory into a 19-table DNA profile.
- **First/Second Interpretation**: Analyzes DNA for strategic and tactical direction.
- **Core Services**: 6 microservices for basic operations.
- **Core Jobs**: 9 background jobs for system maintenance.

### Phase 2: The Living Organism

- **Agent Health Monitor**: The sensory system. Continuously monitors and scores agent health.
- **Agent Lifecycle Manager**: The immune system. Manages agent lifecycles based on health (apoptosis, evolution, mitosis).
- **Intelligent Agent Factory**: The reproductive system. Detects needs and spawns new agents automatically.

### Phase 2.1: The Unified Identity

- **Master Prompt Engine**: The soul. Synthesizes the complete DNA profile into a single Master Prompt that defines the core identity of the Entity.
- **Micro-Prompts Engine**: The nervous system. Adapts the Master Prompt for each agent's specific role.

---

## Documentation

This README serves as the central source of truth. For more detailed information, see the `docs/` directory.

### Key Documents

- **[Phase 2 Integration Guide](./docs/PHASE2_INTEGRATION.md)**: Detailed technical guide for Phase 2 components.
- **[Phase 2 Completion Summary](./docs/PHASE2_COMPLETION_SUMMARY.md)**: Summary of Phase 2 implementation and achievements.
- **[Master Prompt Implementation Report](./docs/MASTER_PROMPT_IMPLEMENTATION_REPORT.md)**: Detailed report on the Master Prompt layer.
- **[CI/CD Guide](./docs/CICD_GUIDE.md)**: Guide to the CI/CD pipeline.

### Service & Job READMEs

Each service and job has a detailed README in its directory:

- `backend/services/agent-health-monitor/README.md`
- `backend/services/intelligent-agent-factory/README.md`
- `backend/jobs/agent-lifecycle-manager/README.md`
- `backend/jobs/master-prompt-engine/README.md`
- `backend/jobs/micro-prompts/README.md`

---

## Deployment

Deployment is fully automated via GitHub Actions. Any push to `main` will trigger a deployment of the changed components.

### Manual Operations

**Run Master Prompt Engine**:
```bash
gcloud run jobs execute master-prompt-engine --region us-central1 --set-env-vars ENTITY_ID=<uuid>
```

**Run Micro-Prompts Engine**:
```bash
gcloud run jobs execute micro-prompts --region us-central1 --set-env-vars ENTITY_ID=<uuid>
```

**Run Lifecycle Manager**:
```bash
gcloud run jobs execute agent-lifecycle-manager --region us-central1
```

---

## Philosophy in Action

- **One DNA**: The system is built around a single, unified DNA profile.
- **One Organism**: All components work together as a single, coherent entity.
- **Infinite Potential**: The system is designed to evolve and adapt indefinitely.

**The symbiosis is real.** 🧬
real.** 🧬
