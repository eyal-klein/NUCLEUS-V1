"""
NUCLEUS V2.0 - Domain Management Engine

Manages "kingdoms" (domains) of the entity's life:
1. Detects and creates domains from entity data
2. Organizes information by domain
3. Maintains domain-specific knowledge libraries
4. Coordinates domain-specific agents

Based on:
- GI X Document: "ניהול ממלכות" - managing life domains
- NUCLEUS Agent Document: Domain-specific expertise
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, '/app/shared')

from models.base import get_db
from models.dna import Entity, Interest, Goal
from models.memory import CalendarEvent, EmailMessage
from models.nucleus_core import Domain, DomainKnowledge, BehaviorLog
from llm.gateway import get_llm_gateway
from pubsub.publisher import get_publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Domain Management Engine",
    description="Manages life domains (kingdoms) and domain-specific knowledge",
    version="2.0.0"
)

llm = get_llm_gateway()
publisher = get_publisher()

# ============================================================================
# DEFAULT DOMAINS
# ============================================================================

DEFAULT_DOMAINS = [
    {
        "name": "career",
        "display_name": "Career & Professional",
        "description": "Work, career growth, professional relationships",
        "keywords": ["work", "job", "career", "meeting", "project", "client", "colleague"]
    },
    {
        "name": "health",
        "display_name": "Health & Wellness",
        "description": "Physical health, mental wellness, fitness",
        "keywords": ["health", "fitness", "exercise", "sleep", "diet", "wellness", "doctor"]
    },
    {
        "name": "relationships",
        "display_name": "Relationships & Social",
        "description": "Family, friends, social connections",
        "keywords": ["family", "friend", "relationship", "social", "dinner", "party"]
    },
    {
        "name": "finance",
        "display_name": "Finance & Wealth",
        "description": "Money, investments, financial planning",
        "keywords": ["money", "finance", "investment", "budget", "savings", "expense"]
    },
    {
        "name": "growth",
        "display_name": "Personal Growth",
        "description": "Learning, skills, self-improvement",
        "keywords": ["learn", "course", "skill", "book", "study", "growth", "development"]
    },
    {
        "name": "leisure",
        "display_name": "Leisure & Recreation",
        "description": "Hobbies, entertainment, relaxation",
        "keywords": ["hobby", "fun", "vacation", "travel", "movie", "game", "relax"]
    }
]


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class DomainDetectionRequest(BaseModel):
    entity_id: str
    analyze_sources: List[str] = Field(default=["calendar", "email", "goals"])


class DomainResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    importance_score: float
    activity_score: float
    item_count: int


class KnowledgeAddRequest(BaseModel):
    entity_id: str
    domain_name: str
    knowledge_type: str  # principle, fact, preference, insight
    title: str
    content: str
    source: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0, le=1)


class DomainQueryRequest(BaseModel):
    entity_id: str
    domain_name: str
    query: str


# ============================================================================
# DOMAIN DETECTOR
# ============================================================================

class DomainDetector:
    """Detects and creates domains from entity data"""
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def detect_and_create_domains(
        self,
        sources: List[str]
    ) -> List[Domain]:
        """Detect domains from entity data and create them"""
        
        # Get existing domains
        existing = self.db.query(Domain).filter(
            Domain.entity_id == self.entity_id
        ).all()
        existing_names = {d.domain_name for d in existing}
        
        # Create default domains if none exist
        if not existing:
            for domain_def in DEFAULT_DOMAINS:
                domain = Domain(
                    entity_id=self.entity_id,
                    domain_name=domain_def["name"],
                    display_name=domain_def["display_name"],
                    description=domain_def["description"],
                    domain_keywords=domain_def["keywords"],
                    importance_score=0.5,
                    activity_score=0.0,
                    is_active=True
                )
                self.db.add(domain)
                existing.append(domain)
            self.db.commit()
        
        # Analyze activity in each domain
        await self._analyze_domain_activity(existing, sources)
        
        return existing
    
    async def _analyze_domain_activity(
        self,
        domains: List[Domain],
        sources: List[str]
    ):
        """Analyze activity levels for each domain"""
        
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        for domain in domains:
            activity_count = 0
            
            if "calendar" in sources:
                # Count calendar events matching domain keywords
                events = self.db.query(CalendarEvent).filter(
                    and_(
                        CalendarEvent.entity_id == self.entity_id,
                        CalendarEvent.start_time >= cutoff
                    )
                ).all()
                
                for event in events:
                    title_lower = (event.title or "").lower()
                    if any(kw in title_lower for kw in (domain.domain_keywords or [])):
                        activity_count += 1
            
            if "goals" in sources:
                # Count goals in this domain
                goals = self.db.query(Goal).filter(
                    and_(
                        Goal.entity_id == self.entity_id,
                        Goal.is_active == True
                    )
                ).all()
                
                for goal in goals:
                    if goal.goal_category == domain.domain_name:
                        activity_count += 2  # Goals are weighted higher
            
            # Update activity score
            domain.activity_score = min(activity_count / 20, 1.0)  # Normalize
            domain.item_count = activity_count
            domain.last_activity_at = datetime.utcnow() if activity_count > 0 else domain.last_activity_at
        
        self.db.commit()


# ============================================================================
# KNOWLEDGE MANAGER
# ============================================================================

class KnowledgeManager:
    """Manages domain-specific knowledge libraries"""
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def add_knowledge(
        self,
        domain_name: str,
        knowledge_type: str,
        title: str,
        content: str,
        source: Optional[str],
        confidence: float
    ) -> DomainKnowledge:
        """Add knowledge to a domain library"""
        
        # Get domain
        domain = self.db.query(Domain).filter(
            and_(
                Domain.entity_id == self.entity_id,
                Domain.domain_name == domain_name
            )
        ).first()
        
        if not domain:
            raise HTTPException(status_code=404, detail=f"Domain '{domain_name}' not found")
        
        knowledge = DomainKnowledge(
            entity_id=self.entity_id,
            domain_id=domain.id,
            knowledge_type=knowledge_type,
            title=title,
            content=content,
            source=source,
            confidence_score=confidence,
            is_validated=confidence >= 0.9,
            usage_count=0
        )
        self.db.add(knowledge)
        self.db.commit()
        
        return knowledge
    
    async def query_knowledge(
        self,
        domain_name: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Query knowledge from a domain"""
        
        # Get domain
        domain = self.db.query(Domain).filter(
            and_(
                Domain.entity_id == self.entity_id,
                Domain.domain_name == domain_name
            )
        ).first()
        
        if not domain:
            raise HTTPException(status_code=404, detail=f"Domain '{domain_name}' not found")
        
        # Get all knowledge for domain
        knowledge_items = self.db.query(DomainKnowledge).filter(
            and_(
                DomainKnowledge.domain_id == domain.id,
                DomainKnowledge.is_active == True
            )
        ).all()
        
        if not knowledge_items:
            return []
        
        # Use LLM to find relevant knowledge
        knowledge_texts = [
            f"[{k.knowledge_type}] {k.title}: {k.content}"
            for k in knowledge_items
        ]
        
        search_prompt = f"""Given this query: "{query}"

Find the most relevant knowledge items from this list:
{chr(10).join(knowledge_texts)}

Return the indices (0-based) of the top 3 most relevant items as JSON:
{{"relevant_indices": [0, 1, 2], "relevance_scores": [0.9, 0.8, 0.7]}}"""

        try:
            response = await llm.complete([
                {"role": "system", "content": "You are a knowledge retrieval assistant."},
                {"role": "user", "content": search_prompt}
            ])
            
            result = json.loads(response.strip().replace("```json", "").replace("```", ""))
            indices = result.get("relevant_indices", [])
            scores = result.get("relevance_scores", [])
            
            relevant = []
            for i, idx in enumerate(indices):
                if idx < len(knowledge_items):
                    k = knowledge_items[idx]
                    k.usage_count = (k.usage_count or 0) + 1
                    relevant.append({
                        "id": str(k.id),
                        "type": k.knowledge_type,
                        "title": k.title,
                        "content": k.content,
                        "relevance": scores[i] if i < len(scores) else 0.5
                    })
            
            self.db.commit()
            return relevant
            
        except Exception as e:
            logger.error(f"Error querying knowledge: {e}")
            return []


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/detect-domains")
async def detect_domains(
    request: DomainDetectionRequest,
    db: Session = Depends(get_db)
):
    """Detect and create domains for an entity"""
    try:
        eid = UUID(request.entity_id)
        
        detector = DomainDetector(db, eid)
        domains = await detector.detect_and_create_domains(request.analyze_sources)
        
        return {
            "entity_id": request.entity_id,
            "domains_count": len(domains),
            "domains": [
                DomainResponse(
                    id=str(d.id),
                    name=d.domain_name,
                    display_name=d.display_name,
                    description=d.description,
                    importance_score=d.importance_score or 0.5,
                    activity_score=d.activity_score or 0.0,
                    item_count=d.item_count or 0
                ).dict()
                for d in domains
            ]
        }
        
    except Exception as e:
        logger.error(f"Error detecting domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/domains/{entity_id}")
async def get_domains(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get all domains for an entity"""
    try:
        domains = db.query(Domain).filter(
            and_(
                Domain.entity_id == UUID(entity_id),
                Domain.is_active == True
            )
        ).order_by(Domain.importance_score.desc()).all()
        
        return {
            "entity_id": entity_id,
            "domains": [
                {
                    "id": str(d.id),
                    "name": d.domain_name,
                    "display_name": d.display_name,
                    "description": d.description,
                    "importance": d.importance_score,
                    "activity": d.activity_score,
                    "items": d.item_count
                }
                for d in domains
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add-knowledge")
async def add_knowledge(
    request: KnowledgeAddRequest,
    db: Session = Depends(get_db)
):
    """Add knowledge to a domain library"""
    try:
        eid = UUID(request.entity_id)
        
        manager = KnowledgeManager(db, eid)
        knowledge = await manager.add_knowledge(
            request.domain_name,
            request.knowledge_type,
            request.title,
            request.content,
            request.source,
            request.confidence
        )
        
        return {
            "status": "success",
            "knowledge_id": str(knowledge.id),
            "domain": request.domain_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query-knowledge")
async def query_knowledge(
    request: DomainQueryRequest,
    db: Session = Depends(get_db)
):
    """Query knowledge from a domain"""
    try:
        eid = UUID(request.entity_id)
        
        manager = KnowledgeManager(db, eid)
        results = await manager.query_knowledge(
            request.domain_name,
            request.query
        )
        
        return {
            "entity_id": request.entity_id,
            "domain": request.domain_name,
            "query": request.query,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge/{entity_id}/{domain_name}")
async def get_domain_knowledge(
    entity_id: str,
    domain_name: str,
    db: Session = Depends(get_db)
):
    """Get all knowledge for a domain"""
    try:
        domain = db.query(Domain).filter(
            and_(
                Domain.entity_id == UUID(entity_id),
                Domain.domain_name == domain_name
            )
        ).first()
        
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        knowledge = db.query(DomainKnowledge).filter(
            and_(
                DomainKnowledge.domain_id == domain.id,
                DomainKnowledge.is_active == True
            )
        ).order_by(DomainKnowledge.usage_count.desc()).all()
        
        return {
            "entity_id": entity_id,
            "domain": domain_name,
            "knowledge_count": len(knowledge),
            "items": [
                {
                    "id": str(k.id),
                    "type": k.knowledge_type,
                    "title": k.title,
                    "content": k.content,
                    "confidence": k.confidence_score,
                    "validated": k.is_validated,
                    "usage_count": k.usage_count
                }
                for k in knowledge
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "domain-management-engine", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
