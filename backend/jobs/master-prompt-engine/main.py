"""
NUCLEUS V2.0 - Master Prompt Engine (Cloud Run Job)
Generates the core Entity identity prompt from complete DNA profile

This is the bridge between DNA and Micro-Prompts:
- Input: Complete DNA profile (19 tables) + Strategic & Tactical interpretations
- Output: Entity.master_prompt - The foundational identity that all agents share
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, List
import uuid
from datetime import datetime

# Add backend to path
sys.path.append("/app/backend")

from shared.models import (
    get_db, Entity, Summary,
    PersonalityTrait, CommunicationStyle, DecisionPattern, WorkHabit,
    Relationship, Skill, Preference, Constraint, Belief, Experience,
    Emotion, Routine, Context, Interest, Goal, Value
)
from shared.llm import get_llm_gateway
from shared.pubsub import get_pubsub_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MasterPromptEngine:
    """
    Master Prompt Engine - Synthesizes complete DNA into core Entity identity.
    
    Process:
    1. Collect ALL DNA data (19 tables)
    2. Read strategic and tactical interpretations
    3. Generate comprehensive Master Prompt using LLM
    4. Store in Entity.master_prompt
    5. Publish event for downstream processing
    """
    
    def __init__(self):
        self.llm = get_llm_gateway()
        self.project_id = os.getenv("PROJECT_ID", "thrive-system1")
        self.pubsub = get_pubsub_client(self.project_id)
        
    async def generate_master_prompt(self, entity_id: str) -> Dict[str, Any]:
        """
        Generate Master Prompt for an entity.
        
        Args:
            entity_id: UUID of the entity
            
        Returns:
            Generation results
        """
        logger.info(f"Starting Master Prompt generation for entity: {entity_id}")
        
        db = next(get_db())
        
        try:
            # Get entity
            entity = db.query(Entity).filter(Entity.id == uuid.UUID(entity_id)).first()
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")
            
            # Collect complete DNA
            dna_profile = self._collect_complete_dna(db, entity_id)
            
            # Get interpretations
            interpretations = self._get_interpretations(db, entity_id)
            
            # Generate Master Prompt
            master_prompt = await self._generate_prompt(entity, dna_profile, interpretations)
            
            # Update entity
            entity.master_prompt = master_prompt
            entity.master_prompt_version = (entity.master_prompt_version or 0) + 1
            entity.master_prompt_updated_at = datetime.utcnow()
            db.add(entity)
            db.commit()
            
            # Publish event
            await self.pubsub.publish(
                topic_name="evolution-events",
                message_data={
                    "event_type": "master_prompt_updated",
                    "entity_id": entity_id,
                    "version": entity.master_prompt_version,
                    "timestamp": entity.master_prompt_updated_at.isoformat()
                }
            )
            
            logger.info(f"Master Prompt generated for entity: {entity_id} (version {entity.master_prompt_version})")
            
            return {
                "status": "success",
                "entity_id": entity_id,
                "version": entity.master_prompt_version,
                "prompt_length": len(master_prompt)
            }
            
        except Exception as e:
            logger.error(f"Master Prompt generation failed: {e}")
            raise
        finally:
            db.close()
    
    def _collect_complete_dna(self, db, entity_id: str) -> Dict[str, Any]:
        """
        Collect ALL DNA data from 19 tables.
        
        This is the complete identity profile of the Entity.
        """
        entity_uuid = uuid.UUID(entity_id)
        
        # Core DNA (Phase 1)
        interests = db.query(Interest).filter(Interest.entity_id == entity_uuid, Interest.is_active == True).all()
        goals = db.query(Goal).filter(Goal.entity_id == entity_uuid, Goal.status == "active").order_by(Goal.priority.desc()).all()
        values = db.query(Value).filter(Value.entity_id == entity_uuid).order_by(Value.importance_score.desc()).all()
        
        # Extended DNA (Phase 2)
        personality_traits = db.query(PersonalityTrait).filter(PersonalityTrait.entity_id == entity_uuid).all()
        communication_styles = db.query(CommunicationStyle).filter(CommunicationStyle.entity_id == entity_uuid).all()
        decision_patterns = db.query(DecisionPattern).filter(DecisionPattern.entity_id == entity_uuid).all()
        work_habits = db.query(WorkHabit).filter(WorkHabit.entity_id == entity_uuid).all()
        relationships = db.query(Relationship).filter(Relationship.entity_id == entity_uuid).all()
        skills = db.query(Skill).filter(Skill.entity_id == entity_uuid).order_by(Skill.proficiency_level.desc()).all()
        preferences = db.query(Preference).filter(Preference.entity_id == entity_uuid).all()
        constraints = db.query(Constraint).filter(Constraint.entity_id == entity_uuid, Constraint.is_active == True).all()
        beliefs = db.query(Belief).filter(Belief.entity_id == entity_uuid).all()
        experiences = db.query(Experience).filter(Experience.entity_id == entity_uuid).order_by(Experience.impact_score.desc()).limit(10).all()
        emotions = db.query(Emotion).filter(Emotion.entity_id == entity_uuid).order_by(Emotion.timestamp.desc()).limit(20).all()
        routines = db.query(Routine).filter(Routine.entity_id == entity_uuid, Routine.is_active == True).all()
        contexts = db.query(Context).filter(Context.entity_id == entity_uuid, Context.is_active == True).all()
        
        return {
            "interests": [{"name": i.interest_name, "description": i.interest_description, "confidence": i.confidence_score} for i in interests],
            "goals": [{"title": g.goal_title, "description": g.goal_description, "priority": g.priority} for g in goals],
            "values": [{"name": v.value_name, "description": v.value_description, "importance": v.importance_score} for v in values],
            "personality_traits": [{"trait": p.trait_name, "value": p.trait_value, "description": p.trait_description} for p in personality_traits],
            "communication_styles": [{"style": c.style_name, "description": c.style_description, "frequency": c.frequency_score} for c in communication_styles],
            "decision_patterns": [{"pattern": d.pattern_name, "description": d.pattern_description, "frequency": d.frequency_score} for d in decision_patterns],
            "work_habits": [{"habit": w.habit_name, "description": w.habit_description, "frequency": w.frequency_score} for w in work_habits],
            "relationships": [{"person": r.person_name, "relationship": r.relationship_type, "strength": r.relationship_strength} for r in relationships],
            "skills": [{"skill": s.skill_name, "proficiency": s.proficiency_level, "category": s.skill_category} for s in skills],
            "preferences": [{"preference": p.preference_name, "value": p.preference_value, "strength": p.preference_strength} for p in preferences],
            "constraints": [{"constraint": c.constraint_name, "description": c.constraint_description, "severity": c.severity_level} for c in constraints],
            "beliefs": [{"belief": b.belief_statement, "strength": b.belief_strength, "category": b.belief_category} for b in beliefs],
            "experiences": [{"experience": e.experience_description, "impact": e.impact_score, "category": e.experience_category} for e in experiences],
            "emotions": [{"emotion": em.emotion_name, "intensity": em.intensity, "context": em.context_description} for em in emotions],
            "routines": [{"routine": r.routine_name, "description": r.routine_description, "frequency": r.frequency} for r in routines],
            "contexts": [{"context": c.context_name, "description": c.context_description, "relevance": c.relevance_score} for c in contexts]
        }
    
    def _get_interpretations(self, db, entity_id: str) -> Dict[str, str]:
        """Get strategic and tactical interpretations"""
        first_interp = db.query(Summary).filter(
            Summary.entity_id == uuid.UUID(entity_id),
            Summary.summary_type == "first_interpretation"
        ).order_by(Summary.created_at.desc()).first()
        
        second_interp = db.query(Summary).filter(
            Summary.entity_id == uuid.UUID(entity_id),
            Summary.summary_type == "second_interpretation"
        ).order_by(Summary.created_at.desc()).first()
        
        return {
            "strategic": first_interp.summary_text if first_interp else "Not available",
            "tactical": second_interp.summary_text if second_interp else "Not available"
        }
    
    async def _generate_prompt(
        self,
        entity: Entity,
        dna_profile: Dict[str, Any],
        interpretations: Dict[str, str]
    ) -> str:
        """
        Generate the Master Prompt using LLM.
        
        This prompt will serve as the foundational identity for ALL agents.
        """
        
        # Build comprehensive DNA summary
        dna_summary = self._build_dna_summary(dna_profile)
        
        prompt = f"""You are creating the MASTER PROMPT for an AI system called NUCLEUS.

This Master Prompt defines the CORE IDENTITY of the Entity and will be used as the foundation for all AI agents serving this Entity.

ENTITY: {entity.name}

=== COMPLETE DNA PROFILE ===

{dna_summary}

=== STRATEGIC DIRECTION ===
{interpretations['strategic']}

=== TACTICAL PLAN ===
{interpretations['tactical']}

=== YOUR TASK ===

Generate a comprehensive MASTER PROMPT that captures the complete identity of this Entity.

The Master Prompt MUST include these sections:

1. **IDENTITY** (2-3 paragraphs)
   - Who is this Entity?
   - Core personality traits and characteristics
   - Fundamental values and beliefs
   - What makes this Entity unique?

2. **COMMUNICATION STYLE** (1-2 paragraphs)
   - How does this Entity communicate?
   - Preferred tone, formality, and approach
   - Communication patterns and preferences

3. **DECISION-MAKING** (1-2 paragraphs)
   - How does this Entity make decisions?
   - Decision patterns and constraints
   - What factors are most important?

4. **GOALS & DIRECTION** (2-3 paragraphs)
   - What does this Entity want to achieve?
   - Strategic priorities and tactical focus
   - Long-term vision and short-term objectives

5. **CONTEXT & RELATIONSHIPS** (1-2 paragraphs)
   - Important relationships and social context
   - Key skills and experiences
   - Relevant routines and environments

6. **GUIDING PRINCIPLES** (bullet points)
   - 5-7 core principles that should guide ALL actions
   - These are non-negotiable rules derived from values and constraints

The Master Prompt should be:
- Comprehensive (covering all aspects of identity)
- Authoritative (this IS the Entity)
- Actionable (agents can use this to make decisions)
- Consistent (all agents will share this foundation)

Write in a clear, professional style. This is the DNA of the Entity expressed as instructions for AI agents.

Total length: 800-1200 words.
"""
        
        messages = [
            {"role": "system", "content": "You are an expert in AI system design and identity modeling. You create comprehensive, nuanced identity prompts that capture the essence of an entity."},
            {"role": "user", "content": prompt}
        ]
        
        master_prompt = await self.llm.complete(messages, temperature=0.3, max_tokens=2000)
        
        return master_prompt.strip()
    
    def _build_dna_summary(self, dna: Dict[str, Any]) -> str:
        """Build a readable summary of DNA profile"""
        sections = []
        
        # Interests
        if dna['interests']:
            interests_text = ", ".join([f"{i['name']} ({i['confidence']:.2f})" for i in dna['interests'][:10]])
            sections.append(f"**Interests**: {interests_text}")
        
        # Goals
        if dna['goals']:
            goals_text = "\n".join([f"  - {g['title']} (Priority: {g['priority']})" for g in dna['goals'][:5]])
            sections.append(f"**Goals**:\n{goals_text}")
        
        # Values
        if dna['values']:
            values_text = ", ".join([f"{v['name']} ({v['importance']:.2f})" for v in dna['values'][:5]])
            sections.append(f"**Values**: {values_text}")
        
        # Personality
        if dna['personality_traits']:
            personality_text = "\n".join([f"  - {p['trait']}: {p['value']:.2f} - {p['description']}" for p in dna['personality_traits'][:5]])
            sections.append(f"**Personality Traits**:\n{personality_text}")
        
        # Communication
        if dna['communication_styles']:
            comm_text = "\n".join([f"  - {c['style']}: {c['description']}" for c in dna['communication_styles'][:3]])
            sections.append(f"**Communication Styles**:\n{comm_text}")
        
        # Decision Patterns
        if dna['decision_patterns']:
            decision_text = "\n".join([f"  - {d['pattern']}: {d['description']}" for d in dna['decision_patterns'][:3]])
            sections.append(f"**Decision Patterns**:\n{decision_text}")
        
        # Skills
        if dna['skills']:
            skills_text = ", ".join([f"{s['skill']} ({s['proficiency']:.2f})" for s in dna['skills'][:10]])
            sections.append(f"**Skills**: {skills_text}")
        
        # Constraints
        if dna['constraints']:
            constraints_text = "\n".join([f"  - {c['constraint']}: {c['description']}" for c in dna['constraints'][:5]])
            sections.append(f"**Constraints**:\n{constraints_text}")
        
        # Beliefs
        if dna['beliefs']:
            beliefs_text = "\n".join([f"  - {b['belief']} (Strength: {b['strength']:.2f})" for b in dna['beliefs'][:5]])
            sections.append(f"**Beliefs**:\n{beliefs_text}")
        
        return "\n\n".join(sections)


async def main():
    """Main entry point"""
    logger.info("Master Prompt Engine starting...")
    
    entity_id = os.getenv("ENTITY_ID")
    if not entity_id:
        logger.error("ENTITY_ID environment variable not set")
        return
    
    engine = MasterPromptEngine()
    await engine.pubsub.initialize()
    
    try:
        result = await engine.generate_master_prompt(entity_id)
        logger.info(f"Master Prompt generation complete: {result}")
    except Exception as e:
        logger.error(f"Master Prompt generation failed: {e}")
        raise
    finally:
        await engine.pubsub.close()


if __name__ == "__main__":
    asyncio.run(main())
