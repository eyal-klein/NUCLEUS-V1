"""
Intelligent Agent Factory Service
Detects needs and automatically spawns new agents based on patterns, gaps, and opportunities
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, and_, or_, func, text
from sqlalchemy.orm import sessionmaker, Session
from openai import OpenAI

from backend.shared.models.assembly import Agent, AgentNeed, AgentLifecycleEvent
from backend.shared.models.dna import Entity, EntityRelationship

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

# OpenAI client
client = OpenAI()

# FastAPI app
app = FastAPI(
    title="Intelligent Agent Factory",
    description="Automatically detects needs and spawns new AI agents",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Models
# ============================================================================

class NeedDetectionRequest(BaseModel):
    """Request to detect agent needs"""
    lookback_days: int = Field(default=7, description="Days to look back for pattern analysis")
    min_confidence: float = Field(default=0.7, description="Minimum confidence threshold")


class AgentSpawnRequest(BaseModel):
    """Request to spawn a new agent"""
    need_id: Optional[str] = Field(None, description="Need ID that triggered this spawn")
    agent_type: str = Field(..., description="Type of agent to create")
    agent_name: str = Field(..., description="Name for the new agent")
    description: str = Field(..., description="Description of agent purpose")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Agent capabilities")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")


class NeedResponse(BaseModel):
    """Response with detected need"""
    need_id: str
    need_type: str
    description: str
    priority: str
    confidence: float
    evidence: List[str]
    suggested_agent: Dict[str, Any]
    detected_at: datetime


class AgentCreationResponse(BaseModel):
    """Response after creating an agent"""
    agent_id: str
    agent_name: str
    agent_type: str
    status: str
    message: str


# ============================================================================
# Need Detection Engine
# ============================================================================

class NeedDetector:
    """Detects needs for new agents based on system patterns"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_needs(self, lookback_days: int = 7, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """Detect needs for new agents"""
        
        logger.info(f"Detecting needs (lookback: {lookback_days} days, min_confidence: {min_confidence})")
        
        needs = []
        
        # 1. Detect gaps in entity coverage
        coverage_needs = self._detect_coverage_gaps()
        needs.extend(coverage_needs)
        
        # 2. Detect high-demand patterns
        demand_needs = self._detect_high_demand_patterns(lookback_days)
        needs.extend(demand_needs)
        
        # 3. Detect failed request patterns
        failure_needs = self._detect_failure_patterns(lookback_days)
        needs.extend(failure_needs)
        
        # 4. Detect emerging topics
        topic_needs = self._detect_emerging_topics(lookback_days)
        needs.extend(topic_needs)
        
        # Filter by confidence
        filtered_needs = [n for n in needs if n['confidence'] >= min_confidence]
        
        logger.info(f"Detected {len(filtered_needs)} needs (from {len(needs)} total)")
        
        return filtered_needs
    
    def _detect_coverage_gaps(self) -> List[Dict[str, Any]]:
        """Detect entities without dedicated agents"""
        
        needs = []
        
        try:
            # Find entities with high importance but no agents
            query = text("""
                SELECT 
                    e.id,
                    e.entity_name,
                    e.entity_type,
                    COUNT(DISTINCT er.related_entity_id) as relationship_count
                FROM dna.entities e
                LEFT JOIN assembly.agents a ON a.entity_id = e.id AND a.is_active = true
                LEFT JOIN dna.entity_relationships er ON e.id = er.entity_id
                WHERE a.id IS NULL
                GROUP BY e.id, e.entity_name, e.entity_type
                HAVING COUNT(DISTINCT er.related_entity_id) > 5
                ORDER BY relationship_count DESC
                LIMIT 10
            """)
            
            result = self.db.execute(query)
            rows = result.fetchall()
            
            for row in rows:
                entity_id, entity_name, entity_type, rel_count = row
                
                needs.append({
                    'need_type': 'coverage_gap',
                    'description': f"Entity '{entity_name}' has {rel_count} relationships but no dedicated agent",
                    'priority': 'high' if rel_count > 10 else 'medium',
                    'confidence': min(0.9, 0.6 + (rel_count / 50)),
                    'evidence': [
                        f"Entity has {rel_count} relationships",
                        f"No active agent for entity type: {entity_type}",
                        "High connectivity suggests importance"
                    ],
                    'metadata': {
                        'entity_id': str(entity_id),
                        'entity_name': entity_name,
                        'entity_type': entity_type,
                        'relationship_count': rel_count
                    }
                })
        
        except Exception as e:
            logger.error(f"Error detecting coverage gaps: {e}")
        
        return needs
    
    def _detect_high_demand_patterns(self, lookback_days: int) -> List[Dict[str, Any]]:
        """Detect patterns of high demand that could benefit from new agents"""
        
        needs = []
        
        try:
            # This would analyze request logs, but for now we'll use a placeholder
            # In a real implementation, this would query request logs or metrics
            
            # Example: Detect if certain entity types are being queried frequently
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            # Placeholder for demand analysis
            # TODO: Implement actual demand pattern analysis from logs
            
        except Exception as e:
            logger.error(f"Error detecting demand patterns: {e}")
        
        return needs
    
    def _detect_failure_patterns(self, lookback_days: int) -> List[Dict[str, Any]]:
        """Detect patterns of failures that suggest need for specialized agents"""
        
        needs = []
        
        try:
            # Analyze agent health to find common failure patterns
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            query = text("""
                SELECT 
                    a.agent_type,
                    COUNT(*) as failure_count,
                    AVG(h.success_rate) as avg_success_rate
                FROM assembly.agents a
                JOIN assembly.agent_health h ON a.id = h.agent_id
                WHERE h.calculated_at >= :cutoff_date
                AND h.success_rate < 0.7
                GROUP BY a.agent_type
                HAVING COUNT(*) > 3
            """)
            
            result = self.db.execute(query, {"cutoff_date": cutoff_date})
            rows = result.fetchall()
            
            for row in rows:
                agent_type, failure_count, avg_success = row
                
                needs.append({
                    'need_type': 'failure_pattern',
                    'description': f"Multiple {agent_type} agents showing low success rates",
                    'priority': 'high',
                    'confidence': 0.75,
                    'evidence': [
                        f"{failure_count} agents with low success rate",
                        f"Average success rate: {avg_success:.2%}",
                        "May need specialized variant or support agent"
                    ],
                    'metadata': {
                        'agent_type': agent_type,
                        'failure_count': failure_count,
                        'avg_success_rate': float(avg_success)
                    }
                })
        
        except Exception as e:
            logger.error(f"Error detecting failure patterns: {e}")
        
        return needs
    
    def _detect_emerging_topics(self, lookback_days: int) -> List[Dict[str, Any]]:
        """Detect emerging topics that might need dedicated agents"""
        
        needs = []
        
        try:
            # Analyze recent entity creation patterns
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            query = text("""
                SELECT 
                    entity_type,
                    COUNT(*) as new_entities,
                    COUNT(DISTINCT DATE(created_at)) as active_days
                FROM dna.entities
                WHERE created_at >= :cutoff_date
                GROUP BY entity_type
                HAVING COUNT(*) > 5
                ORDER BY new_entities DESC
            """)
            
            result = self.db.execute(query, {"cutoff_date": cutoff_date})
            rows = result.fetchall()
            
            for row in rows:
                entity_type, new_count, active_days = row
                
                # Calculate velocity (entities per day)
                velocity = new_count / max(active_days, 1)
                
                if velocity > 1:  # More than 1 entity per day
                    needs.append({
                        'need_type': 'emerging_topic',
                        'description': f"Rapid growth in {entity_type} entities",
                        'priority': 'medium',
                        'confidence': min(0.85, 0.6 + (velocity / 10)),
                        'evidence': [
                            f"{new_count} new entities in {lookback_days} days",
                            f"Velocity: {velocity:.1f} entities/day",
                            "Suggests growing interest in topic"
                        ],
                        'metadata': {
                            'entity_type': entity_type,
                            'new_entities': new_count,
                            'velocity': velocity
                        }
                    })
        
        except Exception as e:
            logger.error(f"Error detecting emerging topics: {e}")
        
        return needs
    
    async def analyze_need_with_llm(self, need: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze a need and suggest agent specification"""
        
        try:
            prompt = f"""Analyze this detected need for a new AI agent and provide a detailed agent specification.

Need Information:
- Type: {need['need_type']}
- Description: {need['description']}
- Priority: {need['priority']}
- Evidence: {json.dumps(need['evidence'], indent=2)}
- Metadata: {json.dumps(need['metadata'], indent=2)}

Provide a detailed agent specification in JSON format:
{{
    "agent_name": "Suggested name for the agent",
    "agent_type": "Type classification",
    "purpose": "Clear purpose statement",
    "capabilities": ["capability1", "capability2"],
    "specialization": "What makes this agent unique",
    "expected_impact": "Expected improvement to the system",
    "priority_justification": "Why this agent should be created",
    "configuration": {{
        "key1": "value1"
    }}
}}"""

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in AI agent architecture and system design. Provide detailed, actionable agent specifications in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            suggestion = json.loads(content)
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error analyzing need with LLM: {e}")
            return {
                "agent_name": f"Agent for {need['need_type']}",
                "agent_type": "general",
                "purpose": need['description'],
                "capabilities": [],
                "specialization": "Auto-generated",
                "expected_impact": "Unknown",
                "priority_justification": need['description'],
                "configuration": {}
            }


# ============================================================================
# Agent Factory
# ============================================================================

class AgentFactory:
    """Creates new agents based on specifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_agent(
        self,
        agent_type: str,
        agent_name: str,
        description: str,
        capabilities: Dict[str, Any],
        configuration: Dict[str, Any],
        need_id: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new agent"""
        
        logger.info(f"Creating new agent: {agent_name} (type: {agent_type})")
        
        try:
            # Create agent record
            agent = Agent(
                id=uuid4(),
                agent_name=agent_name,
                agent_type=agent_type,
                description=description,
                entity_id=entity_id,
                capabilities=capabilities,
                configuration=configuration,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(agent)
            
            # Log lifecycle event
            event = AgentLifecycleEvent(
                agent_id=agent.id,
                event_type='spawn',
                reason=f"Created by Intelligent Agent Factory based on detected need",
                before_state=None,
                after_state={'status': 'created', 'active': True},
                triggered_by='agent_factory',
                triggered_by_id=need_id,
                metadata={
                    'capabilities': capabilities,
                    'configuration': configuration
                },
                occurred_at=datetime.utcnow()
            )
            
            self.db.add(event)
            
            # Update need status if provided
            if need_id:
                need = self.db.query(AgentNeed).filter(AgentNeed.id == need_id).first()
                if need:
                    need.status = 'fulfilled'
                    need.fulfilled_at = datetime.utcnow()
                    need.created_agent_id = agent.id
            
            self.db.commit()
            
            logger.info(f"Agent created successfully: {agent.id}")
            
            return {
                'agent_id': str(agent.id),
                'agent_name': agent.agent_name,
                'agent_type': agent.agent_type,
                'status': 'created',
                'message': 'Agent created successfully'
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating agent: {e}")
            raise


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "intelligent-agent-factory",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/detect-needs", response_model=List[NeedResponse])
async def detect_needs(request: NeedDetectionRequest, background_tasks: BackgroundTasks):
    """Detect needs for new agents"""
    
    db = SessionLocal()
    try:
        detector = NeedDetector(db)
        needs = detector.detect_needs(
            lookback_days=request.lookback_days,
            min_confidence=request.min_confidence
        )
        
        # Store needs in database
        stored_needs = []
        for need in needs:
            # Analyze with LLM
            suggestion = await detector.analyze_need_with_llm(need)
            
            # Store in database
            need_record = AgentNeed(
                id=uuid4(),
                need_type=need['need_type'],
                description=need['description'],
                priority=need['priority'],
                confidence=need['confidence'],
                evidence=need['evidence'],
                metadata=need.get('metadata', {}),
                suggested_agent_spec=suggestion,
                status='pending',
                detected_at=datetime.utcnow()
            )
            
            db.add(need_record)
            
            stored_needs.append(NeedResponse(
                need_id=str(need_record.id),
                need_type=need_record.need_type,
                description=need_record.description,
                priority=need_record.priority,
                confidence=need_record.confidence,
                evidence=need_record.evidence,
                suggested_agent=suggestion,
                detected_at=need_record.detected_at
            ))
        
        db.commit()
        
        return stored_needs
        
    finally:
        db.close()


@app.post("/spawn-agent", response_model=AgentCreationResponse)
async def spawn_agent(request: AgentSpawnRequest):
    """Spawn a new agent"""
    
    db = SessionLocal()
    try:
        factory = AgentFactory(db)
        
        result = factory.create_agent(
            agent_type=request.agent_type,
            agent_name=request.agent_name,
            description=request.description,
            capabilities=request.capabilities,
            configuration=request.configuration,
            need_id=request.need_id
        )
        
        return AgentCreationResponse(**result)
        
    finally:
        db.close()


@app.get("/needs")
async def get_needs(status: Optional[str] = None, limit: int = 50):
    """Get detected needs"""
    
    db = SessionLocal()
    try:
        query = db.query(AgentNeed)
        
        if status:
            query = query.filter(AgentNeed.status == status)
        
        needs = query.order_by(AgentNeed.detected_at.desc()).limit(limit).all()
        
        return [
            {
                'need_id': str(n.id),
                'need_type': n.need_type,
                'description': n.description,
                'priority': n.priority,
                'confidence': n.confidence,
                'status': n.status,
                'suggested_agent': n.suggested_agent_spec,
                'detected_at': n.detected_at.isoformat()
            }
            for n in needs
        ]
        
    finally:
        db.close()


@app.post("/auto-spawn")
async def auto_spawn():
    """Automatically spawn agents for high-priority pending needs"""
    
    db = SessionLocal()
    try:
        # Get high-priority pending needs
        needs = db.query(AgentNeed).filter(
            and_(
                AgentNeed.status == 'pending',
                AgentNeed.priority == 'high',
                AgentNeed.confidence >= 0.8
            )
        ).limit(5).all()
        
        factory = AgentFactory(db)
        spawned = []
        
        for need in needs:
            spec = need.suggested_agent_spec
            
            try:
                result = factory.create_agent(
                    agent_type=spec.get('agent_type', 'general'),
                    agent_name=spec.get('agent_name', f'Agent-{need.need_type}'),
                    description=spec.get('purpose', need.description),
                    capabilities=spec.get('capabilities', {}),
                    configuration=spec.get('configuration', {}),
                    need_id=str(need.id)
                )
                
                spawned.append(result)
                
            except Exception as e:
                logger.error(f"Error spawning agent for need {need.id}: {e}")
        
        return {
            'spawned_count': len(spawned),
            'agents': spawned
        }
        
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
