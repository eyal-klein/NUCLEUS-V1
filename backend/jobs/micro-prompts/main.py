"""
NUCLEUS V2.0 - Micro-Prompts Engine (Cloud Run Job)
Generates customized system prompts for each agent based on Entity Master Prompt

UPDATED: Now uses Entity.master_prompt as foundation instead of reading DNA directly
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, List
import uuid

# Add backend to path
sys.path.append("/app/backend")

from shared.models import get_db, Entity, Agent
from shared.llm import get_llm_gateway
from shared.pubsub import get_pubsub_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MicroPromptsEngine:
    """
    Micro-Prompts Engine - Generates personalized prompts for agents.
    
    UPDATED Process (V2.0):
    1. Read Entity.master_prompt (the core identity)
    2. For each active agent, adapt the Master Prompt to the agent's specific role
    3. Update agent's system_prompt field
    4. Publish prompt updated events
    
    This ensures all agents share the same foundational identity while maintaining
    role-specific customization.
    """
    
    def __init__(self):
        self.llm = get_llm_gateway()
        self.project_id = os.getenv("PROJECT_ID")

        if not self.project_id:

            raise ValueError("PROJECT_ID environment variable is required for proper GCP project isolation")
        self.pubsub = get_pubsub_client(self.project_id)
        
    async def generate_prompts(self, entity_id: str) -> Dict[str, Any]:
        """
        Generate micro-prompts for all agents of an entity.
        
        Args:
            entity_id: UUID of the entity
            
        Returns:
            Generation results
        """
        logger.info(f"Starting micro-prompts generation for entity: {entity_id}")
        
        db = next(get_db())
        
        try:
            # Get entity
            entity = db.query(Entity).filter(Entity.id == uuid.UUID(entity_id)).first()
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")
            
            # Check if Master Prompt exists
            if not entity.master_prompt:
                raise ValueError(f"Master Prompt not found for entity {entity_id}. Run Master Prompt Engine first.")
            
            logger.info(f"Using Master Prompt version {entity.master_prompt_version} for entity {entity_id}")
            
            # Get all active agents
            agents = db.query(Agent).filter(Agent.is_active == True).all()
            
            updated_agents = []
            
            for agent in agents:
                # Generate customized prompt based on Master Prompt
                new_prompt = await self._generate_prompt(entity, agent)
                
                # Update agent
                agent.system_prompt = new_prompt
                agent.version += 1
                db.add(agent)
                
                updated_agents.append({
                    "agent_id": str(agent.id),
                    "agent_name": agent.agent_name,
                    "version": agent.version
                })
            
            db.commit()
            
            # Publish events
            for agent_info in updated_agents:
                await self.pubsub.publish(
                    topic_name="evolution-events",
                    message_data={
                        "event_type": "agent_prompt_updated",
                        "entity_id": entity_id,
                        "agent_id": agent_info["agent_id"],
                        "agent_name": agent_info["agent_name"],
                        "version": agent_info["version"],
                        "master_prompt_version": entity.master_prompt_version
                    }
                )
            
            logger.info(f"Micro-prompts generated for {len(updated_agents)} agents")
            
            return {
                "status": "success",
                "entity_id": entity_id,
                "master_prompt_version": entity.master_prompt_version,
                "updated_agents": updated_agents
            }
            
        except Exception as e:
            logger.error(f"Micro-prompts generation failed: {e}")
            raise
        finally:
            db.close()
    
    async def _generate_prompt(
        self,
        entity: Entity,
        agent: Agent
    ) -> str:
        """
        Generate customized prompt for an agent based on Master Prompt.
        
        This adapts the Entity's core identity (Master Prompt) to the specific
        role and purpose of this agent.
        """
        
        prompt = f"""You are adapting the MASTER PROMPT of an Entity to create a specialized system prompt for a specific AI agent.

=== ENTITY MASTER PROMPT ===

{entity.master_prompt}

=== AGENT TO CUSTOMIZE ===

- **Agent Name**: {agent.agent_name}
- **Agent Type**: {agent.agent_type}
- **Agent Description**: {agent.description or "N/A"}
- **Current Prompt**: {agent.system_prompt[:300] if agent.system_prompt else "None"}

=== YOUR TASK ===

Create a NEW system prompt for this agent that:

1. **Inherits the Entity's core identity** from the Master Prompt above
   - Maintains the same personality, values, and communication style
   - Follows the same decision-making patterns
   - Aligns with the same goals and principles

2. **Specializes for the agent's specific role**
   - Strategic agents: Focus on big-picture thinking, long-term planning
   - Tactical agents: Focus on execution, short-term actions
   - Specialized agents: Focus on domain-specific tasks

3. **Is clear and actionable**
   - Specific instructions for this agent's function
   - Clear boundaries and responsibilities
   - Concrete examples when helpful

The agent prompt should be:
- **Consistent** with the Master Prompt (same identity)
- **Specialized** for the agent's role (different focus)
- **Actionable** (clear instructions)
- **Concise** (3-5 paragraphs)

Write the system prompt that this agent will use to guide its behavior.
"""
        
        messages = [
            {"role": "system", "content": "You are an expert prompt engineer for NUCLEUS agents. You specialize in adapting a core Entity identity to specific agent roles while maintaining perfect consistency."},
            {"role": "user", "content": prompt}
        ]
        
        new_prompt = await self.llm.complete(messages, temperature=0.4, max_tokens=800)
        
        return new_prompt.strip()


async def main():
    """Main entry point"""
    logger.info("Micro-Prompts Engine starting...")
    
    entity_id = os.getenv("ENTITY_ID")
    if not entity_id:
        logger.error("ENTITY_ID environment variable not set")
        return
    
    engine = MicroPromptsEngine()
    await engine.pubsub.initialize()
    
    try:
        result = await engine.generate_prompts(entity_id)
        logger.info(f"Micro-Prompts generation complete: {result}")
    except Exception as e:
        logger.error(f"Micro-Prompts generation failed: {e}")
        raise
    finally:
        await engine.pubsub.close()


if __name__ == "__main__":
    asyncio.run(main())
