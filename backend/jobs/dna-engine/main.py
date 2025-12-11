"""
NUCLEUS V2.0 - DNA Engine Job
Scheduled job that distills Memory into DNA profiles

Runs nightly to analyze entity interactions and update DNA tables.
"""

import os
import sys
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

# Add backend to path for imports
sys.path.append("/app/backend")

from sqlalchemy.orm import Session
from openai import OpenAI

from shared.models import (
    get_db, Entity, MemoryTier2, MemoryTier3, MemoryTier4,
    PersonalityTrait, CommunicationStyle, DecisionPattern, WorkHabit,
    Relationship, Skill, Preference, Constraint, Belief, Experience,
    Emotion, Routine, Context, EvolutionHistory
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client (using environment variables)
client = OpenAI()


class DNADistiller:
    """
    DNA Distillation Engine
    
    Analyzes entity memories and distills insights into DNA profile.
    """
    
    def __init__(self, db: Session, run_id: uuid.UUID):
        self.db = db
        self.run_id = run_id
        self.model = "gpt-4.1-mini"  # Using available model
        
    def get_recent_memories(
        self,
        entity_id: str,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent memories from Tier 2, 3, and 4
        
        Args:
            entity_id: UUID of the entity
            days_back: Number of days to look back
            
        Returns:
            List of memory dictionaries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        memories = []
        
        # Tier 2: Recent memories (30 days)
        tier2_memories = self.db.query(MemoryTier2).filter(
            MemoryTier2.entity_id == entity_id,
            MemoryTier2.timestamp >= cutoff_date
        ).order_by(MemoryTier2.timestamp.desc()).limit(100).all()
        
        for mem in tier2_memories:
            memories.append({
                "tier": 2,
                "timestamp": mem.timestamp.isoformat(),
                "interaction_type": mem.interaction_type,
                "interaction_data": mem.interaction_data,
                "memory_id": str(mem.id)
            })
        
        # Tier 3: Important memories with embeddings
        tier3_memories = self.db.query(MemoryTier3).filter(
            MemoryTier3.entity_id == entity_id,
            MemoryTier3.timestamp >= cutoff_date
        ).order_by(MemoryTier3.importance_score.desc()).limit(50).all()
        
        for mem in tier3_memories:
            memories.append({
                "tier": 3,
                "timestamp": mem.timestamp.isoformat(),
                "interaction_type": mem.interaction_type,
                "interaction_data": mem.interaction_data,
                "importance_score": mem.importance_score,
                "memory_id": str(mem.id)
            })
        
        # Tier 4: Long-term archived memories (sample)
        tier4_memories = self.db.query(MemoryTier4).filter(
            MemoryTier4.entity_id == entity_id
        ).order_by(MemoryTier4.access_count.desc()).limit(20).all()
        
        for mem in tier4_memories:
            memories.append({
                "tier": 4,
                "timestamp": mem.timestamp.isoformat(),
                "interaction_type": mem.interaction_type,
                "summary": mem.summary,
                "access_count": mem.access_count,
                "memory_id": str(mem.id)
            })
        
        logger.info(f"Fetched {len(memories)} memories for entity {entity_id}")
        return memories
    
    def analyze_personality_traits(
        self,
        entity_id: str,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze memories to extract personality traits
        
        Uses LLM to identify Big Five traits and other personality indicators.
        """
        logger.info(f"Analyzing personality traits for entity {entity_id}")
        
        # Prepare memory context
        memory_context = json.dumps(memories[:30], indent=2)  # Limit to avoid token overflow
        
        prompt = f"""Analyze the following entity interaction memories and extract personality traits.

Focus on the Big Five personality traits:
1. Openness to Experience (0.0 to 1.0)
2. Conscientiousness (0.0 to 1.0)
3. Extraversion (0.0 to 1.0)
4. Agreeableness (0.0 to 1.0)
5. Neuroticism (0.0 to 1.0)

Also identify any other notable personality characteristics.

Memories:
{memory_context}

Return a JSON object with a "traits" array in this format:
{{
  "traits": [
    {{
      "trait_name": "Openness",
      "trait_value": 0.75,
      "trait_description": "Shows high curiosity and willingness to try new things",
      "confidence_score": 0.8,
      "evidence_count": 5
    }}
  ]
}}

Only include traits with confidence_score >= 0.6.
"""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a psychological analyst specializing in personality assessment from behavioral data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            traits = result.get("traits", [])
            
            logger.info(f"Extracted {len(traits)} personality traits")
            return traits
            
        except Exception as e:
            logger.error(f"Failed to analyze personality traits: {e}")
            return []
    
    def analyze_communication_style(
        self,
        entity_id: str,
        memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze communication patterns"""
        logger.info(f"Analyzing communication style for entity {entity_id}")
        
        memory_context = json.dumps(memories[:30], indent=2)
        
        prompt = f"""Analyze the following entity interaction memories and extract communication style patterns.

Consider:
- Directness vs. indirectness
- Formality level
- Tone (professional, casual, friendly, etc.)
- Preferred communication channels
- Response patterns
- Use of humor, empathy, or technical language

Memories:
{memory_context}

Return a JSON object with a "styles" array:
{{
  "styles": [
    {{
      "style_name": "Direct and Concise",
      "style_description": "Prefers brief, to-the-point communication",
      "frequency_score": 0.8,
      "preferred_channels": ["email", "chat"],
      "tone_preferences": {{"formality": "professional", "brevity": "high"}}
    }}
  ]
}}
"""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a communication analyst specializing in identifying communication patterns."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            styles = result.get("styles", [])
            
            logger.info(f"Extracted {len(styles)} communication styles")
            return styles
            
        except Exception as e:
            logger.error(f"Failed to analyze communication style: {e}")
            return []
    
    def update_personality_traits(
        self,
        entity_id: str,
        traits: List[Dict[str, Any]],
        source_memory_ids: List[str]
    ):
        """Update or create personality trait records"""
        for trait_data in traits:
            # Check if trait already exists
            existing = self.db.query(PersonalityTrait).filter(
                PersonalityTrait.entity_id == entity_id,
                PersonalityTrait.trait_name == trait_data["trait_name"]
            ).first()
            
            if existing:
                # Update existing trait
                old_values = {
                    "trait_value": existing.trait_value,
                    "confidence_score": existing.confidence_score,
                    "evidence_count": existing.evidence_count
                }
                
                existing.trait_value = trait_data["trait_value"]
                existing.trait_description = trait_data.get("trait_description")
                existing.confidence_score = trait_data["confidence_score"]
                existing.evidence_count = existing.evidence_count + trait_data.get("evidence_count", 1)
                existing.last_updated_at = datetime.utcnow()
                
                # Log evolution
                self._log_evolution(
                    entity_id=entity_id,
                    table_name="personality_traits",
                    record_id=existing.id,
                    change_type="updated",
                    old_values=old_values,
                    new_values=trait_data,
                    confidence_delta=trait_data["confidence_score"] - old_values["confidence_score"],
                    source_memory_ids=source_memory_ids
                )
            else:
                # Create new trait
                new_trait = PersonalityTrait(
                    entity_id=entity_id,
                    trait_name=trait_data["trait_name"],
                    trait_value=trait_data["trait_value"],
                    trait_description=trait_data.get("trait_description"),
                    confidence_score=trait_data["confidence_score"],
                    evidence_count=trait_data.get("evidence_count", 1)
                )
                self.db.add(new_trait)
                self.db.flush()
                
                # Log evolution
                self._log_evolution(
                    entity_id=entity_id,
                    table_name="personality_traits",
                    record_id=new_trait.id,
                    change_type="created",
                    old_values=None,
                    new_values=trait_data,
                    confidence_delta=trait_data["confidence_score"],
                    source_memory_ids=source_memory_ids
                )
        
        self.db.commit()
        logger.info(f"Updated {len(traits)} personality traits for entity {entity_id}")
    
    def update_communication_styles(
        self,
        entity_id: str,
        styles: List[Dict[str, Any]],
        source_memory_ids: List[str]
    ):
        """Update or create communication style records"""
        for style_data in styles:
            # Check if style already exists
            existing = self.db.query(CommunicationStyle).filter(
                CommunicationStyle.entity_id == entity_id,
                CommunicationStyle.style_name == style_data["style_name"]
            ).first()
            
            if existing:
                # Update existing style
                old_values = {
                    "frequency_score": existing.frequency_score,
                    "preferred_channels": existing.preferred_channels
                }
                
                existing.style_description = style_data.get("style_description")
                existing.frequency_score = style_data["frequency_score"]
                existing.preferred_channels = style_data.get("preferred_channels", [])
                existing.tone_preferences = style_data.get("tone_preferences", {})
                existing.updated_at = datetime.utcnow()
                
                # Log evolution
                self._log_evolution(
                    entity_id=entity_id,
                    table_name="communication_styles",
                    record_id=existing.id,
                    change_type="updated",
                    old_values=old_values,
                    new_values=style_data,
                    confidence_delta=None,
                    source_memory_ids=source_memory_ids
                )
            else:
                # Create new style
                new_style = CommunicationStyle(
                    entity_id=entity_id,
                    style_name=style_data["style_name"],
                    style_description=style_data.get("style_description"),
                    frequency_score=style_data["frequency_score"],
                    preferred_channels=style_data.get("preferred_channels", []),
                    tone_preferences=style_data.get("tone_preferences", {})
                )
                self.db.add(new_style)
                self.db.flush()
                
                # Log evolution
                self._log_evolution(
                    entity_id=entity_id,
                    table_name="communication_styles",
                    record_id=new_style.id,
                    change_type="created",
                    old_values=None,
                    new_values=style_data,
                    confidence_delta=None,
                    source_memory_ids=source_memory_ids
                )
        
        self.db.commit()
        logger.info(f"Updated {len(styles)} communication styles for entity {entity_id}")
    
    def _log_evolution(
        self,
        entity_id: str,
        table_name: str,
        record_id: uuid.UUID,
        change_type: str,
        old_values: Optional[Dict],
        new_values: Dict,
        confidence_delta: Optional[float],
        source_memory_ids: List[str]
    ):
        """Log DNA evolution to history table"""
        evolution = EvolutionHistory(
            entity_id=entity_id,
            table_name=table_name,
            record_id=record_id,
            change_type=change_type,
            old_values=old_values,
            new_values=new_values,
            confidence_delta=confidence_delta,
            source_memory_ids=[uuid.UUID(mid) for mid in source_memory_ids],
            distillation_run_id=self.run_id
        )
        self.db.add(evolution)
    
    def distill_entity_dna(self, entity_id: str):
        """
        Main distillation process for a single entity
        
        Steps:
        1. Fetch recent memories
        2. Analyze with LLM
        3. Update DNA tables
        4. Log evolution
        """
        logger.info(f"Starting DNA distillation for entity {entity_id}")
        
        try:
            # Fetch memories
            memories = self.get_recent_memories(entity_id, days_back=7)
            
            if not memories:
                logger.warning(f"No memories found for entity {entity_id}")
                return
            
            # Extract memory IDs for tracking
            memory_ids = [m["memory_id"] for m in memories]
            
            # Analyze personality traits
            personality_traits = self.analyze_personality_traits(entity_id, memories)
            if personality_traits:
                self.update_personality_traits(entity_id, personality_traits, memory_ids)
            
            # Analyze communication style
            communication_styles = self.analyze_communication_style(entity_id, memories)
            if communication_styles:
                self.update_communication_styles(entity_id, communication_styles, memory_ids)
            
            # TODO: Add more analyzers for other DNA tables:
            # - Decision patterns
            # - Work habits
            # - Skills
            # - Preferences
            # - Emotions
            # - Routines
            # - Contexts
            # etc.
            
            logger.info(f"Completed DNA distillation for entity {entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to distill DNA for entity {entity_id}: {e}")
            self.db.rollback()
            raise


def main():
    """Main entry point for DNA Engine job"""
    logger.info("=" * 80)
    logger.info("NUCLEUS DNA Engine V2.0 - Starting distillation run")
    logger.info("=" * 80)
    
    # Generate run ID
    run_id = uuid.uuid4()
    logger.info(f"Run ID: {run_id}")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all active entities
        entities = db.query(Entity).all()
        logger.info(f"Found {len(entities)} entities to process")
        
        # Initialize distiller
        distiller = DNADistiller(db, run_id)
        
        # Process each entity
        success_count = 0
        error_count = 0
        
        for entity in entities:
            try:
                distiller.distill_entity_dna(str(entity.id))
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to process entity {entity.id}: {e}")
                error_count += 1
        
        logger.info("=" * 80)
        logger.info(f"DNA Engine run complete: {success_count} successful, {error_count} errors")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Fatal error in DNA Engine: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
