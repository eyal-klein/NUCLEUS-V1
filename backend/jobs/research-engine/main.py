"""
NUCLEUS V1.2 - Research Engine (Cloud Run Job)
Conducts research to expand knowledge base and identify new opportunities
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
import uuid
import json

# Add backend to path
sys.path.append("/app/backend")

from shared.models import get_db, Entity, DNAProfile, KnowledgeItem
from shared.llm import get_llm_gateway
from shared.pubsub import get_pubsub_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResearchEngine:
    """
    Research Engine - Conducts autonomous research.
    
    Process:
    1. Identify research topics from DNA (interests, goals)
    2. Conduct research using LLM
    3. Extract key insights
    4. Store in knowledge base
    5. Publish research events
    """
    
    def __init__(self):
        self.llm = get_llm_gateway()
        self.project_id = os.getenv("PROJECT_ID")

        if not self.project_id:

            raise ValueError("PROJECT_ID environment variable is required for proper GCP project isolation")
        self.pubsub = get_pubsub_client(self.project_id)
        
    async def conduct_research(self, entity_id: str) -> Dict[str, Any]:
        """
        Conduct research for an entity.
        
        Args:
            entity_id: UUID of the entity
            
        Returns:
            Research results
        """
        logger.info(f"Starting research for entity: {entity_id}")
        
        db = next(get_db())
        
        try:
            # Get entity
            entity = db.query(Entity).filter(Entity.id == uuid.UUID(entity_id)).first()
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")
            
            # Get DNA profile
            dna_profile = db.query(DNAProfile).filter(
                DNAProfile.entity_id == uuid.UUID(entity_id)
            ).order_by(DNAProfile.created_at.desc()).first()
            
            if not dna_profile:
                logger.warning(f"No DNA profile found for entity {entity_id}")
                return {
                    "status": "skipped",
                    "reason": "No DNA profile available"
                }
            
            logger.info(f"Researching for entity: {entity.entity_name}")
            
            # Identify research topics
            research_topics = await self._identify_research_topics(dna_profile)
            
            if not research_topics:
                logger.info("No research topics identified")
                return {
                    "status": "success",
                    "topics_researched": 0,
                    "message": "No research topics identified"
                }
            
            logger.info(f"Identified {len(research_topics)} research topics")
            
            # Conduct research on each topic
            research_results = []
            for topic in research_topics:
                logger.info(f"Researching topic: {topic['title']}")
                
                result = await self._research_topic(topic)
                research_results.append(result)
                
                # Store in knowledge base
                knowledge_item = KnowledgeItem(
                    entity_id=uuid.UUID(entity_id),
                    category="research",
                    title=topic['title'],
                    content=result['insights'],
                    source="research-engine",
                    metadata={
                        "topic": topic,
                        "research_date": datetime.utcnow().isoformat()
                    }
                )
                db.add(knowledge_item)
            
            db.commit()
            
            # Publish research event
            await self.pubsub.publish(
                topic_name="dna-events",
                message_data={
                    "event_type": "research_completed",
                    "entity_id": entity_id,
                    "topics_researched": len(research_topics),
                    "insights_generated": sum(len(r.get('insights', '').split('\n')) for r in research_results)
                }
            )
            
            logger.info(f"Research complete: {len(research_topics)} topics researched")
            
            return {
                "status": "success",
                "entity_id": entity_id,
                "topics_researched": len(research_topics),
                "research_results": research_results
            }
            
        except Exception as e:
            logger.error(f"Research failed for entity {entity_id}: {e}")
            raise
        finally:
            db.close()
    
    async def _identify_research_topics(self, dna_profile: DNAProfile) -> List[Dict[str, Any]]:
        """Identify research topics based on DNA"""
        
        interests = dna_profile.interests or []
        goals = dna_profile.goals or []
        
        prompt = f"""Based on this entity's DNA, identify 3 research topics that would be valuable to explore.

Interests: {', '.join(interests[:10])}
Goals: {', '.join(goals[:5])}

For each topic, provide:
1. title: Short topic title
2. description: Why this research is valuable
3. questions: 2-3 key questions to answer

Return as JSON array of topics.
"""
        
        messages = [
            {"role": "system", "content": "You are a research strategist for NUCLEUS."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm.complete(messages, temperature=0.7, max_tokens=800)
        
        try:
            topics = json.loads(response.strip())
            return topics if isinstance(topics, list) else []
        except json.JSONDecodeError:
            logger.warning("Failed to parse research topics as JSON")
            return []
    
    async def _research_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct research on a specific topic"""
        
        questions = topic.get('questions', [])
        
        prompt = f"""Research topic: {topic['title']}

Description: {topic['description']}

Key questions:
{chr(10).join(f"- {q}" for q in questions)}

Provide comprehensive insights on this topic, addressing the key questions.
Focus on actionable information and practical applications.

Format your response as clear, structured insights.
"""
        
        messages = [
            {"role": "system", "content": "You are a research assistant conducting in-depth research."},
            {"role": "user", "content": prompt}
        ]
        
        insights = await self.llm.complete(messages, temperature=0.6, max_tokens=1500)
        
        return {
            "topic": topic['title'],
            "insights": insights,
            "questions_addressed": len(questions)
        }


async def main():
    """Main entry point"""
    logger.info("Research Engine starting...")
    
    entity_id = os.getenv("ENTITY_ID")
    if not entity_id:
        logger.error("ENTITY_ID environment variable not set")
        return
    
    engine = ResearchEngine()
    await engine.pubsub.initialize()
    
    try:
        result = await engine.conduct_research(entity_id)
        logger.info(f"Research complete: {result}")
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise
    finally:
        await engine.pubsub.close()


if __name__ == "__main__":
    asyncio.run(main())
