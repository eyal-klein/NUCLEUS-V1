"""
NUCLEUS V2.0 - Proactive Engagement Engine

This engine transforms NUCLEUS from reactive to proactive by:
1. Detecting triggers that warrant proactive engagement
2. Analyzing context to determine the best approach
3. Generating initiatives with 4 options (GI X Protocol)
4. Scheduling delivery at optimal times
5. Learning from responses to improve future engagement

Based on:
- GI X Document: "יוזמה ופרואקטיביות" requirement
- CrewAI Best Practices: Deterministic backbone + LLM intelligence
- BCG 2025: Behavior monitoring and testbed validation
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field

# Shared imports
import sys
sys.path.insert(0, '/app/shared')

from models.base import get_db
from models.dna import Entity, Interest, Goal
from models.memory import CalendarEvent, HealthMetric, EmailMessage
from models.nucleus_core import (
    ProactiveTrigger, ProactiveInitiative,
    AutonomyLevel, CorePrinciple, BehaviorLog
)
from llm.gateway import get_llm_gateway
from pubsub.publisher import get_publisher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Proactive Engagement Engine",
    description="Transforms NUCLEUS from reactive to proactive",
    version="2.0.0"
)

# Initialize LLM Gateway
llm = get_llm_gateway()

# Initialize Pub/Sub Publisher
publisher = get_publisher()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TriggerDetectionRequest(BaseModel):
    """Request to detect triggers for an entity"""
    entity_id: str
    trigger_sources: List[str] = Field(
        default=["calendar", "health", "social", "goals"],
        description="Sources to check for triggers"
    )


class TriggerDetectionResponse(BaseModel):
    """Response with detected triggers"""
    entity_id: str
    triggers_detected: int
    triggers: List[Dict[str, Any]]


class InitiativeGenerationRequest(BaseModel):
    """Request to generate an initiative from a trigger"""
    trigger_id: str
    entity_id: str


class InitiativeResponse(BaseModel):
    """Response with generated initiative"""
    initiative_id: str
    title: str
    message: str
    options: List[Dict[str, str]]
    optimal_delivery_time: Optional[str]


class InitiativeResponseRequest(BaseModel):
    """User response to an initiative"""
    initiative_id: str
    selected_option_id: str
    feedback: Optional[str] = None


# ============================================================================
# TRIGGER DETECTION
# ============================================================================

class TriggerDetector:
    """
    Detects situations that warrant proactive engagement.
    
    Trigger Types:
    - meeting_approaching: Upcoming meeting needs preparation
    - health_change: Significant health metric change
    - relationship_decay: Important relationship losing strength
    - goal_stall: Goal not progressing
    - opportunity_detected: New opportunity aligned with interests
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        self.entity = db.query(Entity).filter(Entity.id == entity_id).first()
        
    async def detect_all_triggers(self, sources: List[str]) -> List[ProactiveTrigger]:
        """Detect triggers from all specified sources"""
        triggers = []
        
        if "calendar" in sources:
            triggers.extend(await self._detect_calendar_triggers())
        if "health" in sources:
            triggers.extend(await self._detect_health_triggers())
        if "goals" in sources:
            triggers.extend(await self._detect_goal_triggers())
        if "social" in sources:
            triggers.extend(await self._detect_social_triggers())
            
        return triggers
    
    async def _detect_calendar_triggers(self) -> List[ProactiveTrigger]:
        """Detect triggers from upcoming calendar events"""
        triggers = []
        
        # Find meetings in the next 24 hours
        now = datetime.utcnow()
        tomorrow = now + timedelta(hours=24)
        
        upcoming_events = self.db.query(CalendarEvent).filter(
            and_(
                CalendarEvent.entity_id == self.entity_id,
                CalendarEvent.start_time >= now,
                CalendarEvent.start_time <= tomorrow
            )
        ).all()
        
        for event in upcoming_events:
            # Check if this event needs preparation
            hours_until = (event.start_time - now).total_seconds() / 3600
            
            # High-priority meetings need more prep time
            if hours_until <= 4 and event.importance_score and event.importance_score > 0.7:
                trigger = ProactiveTrigger(
                    entity_id=self.entity_id,
                    trigger_type="meeting_approaching",
                    trigger_source="calendar",
                    trigger_data={
                        "event_id": str(event.id),
                        "event_title": event.title,
                        "start_time": event.start_time.isoformat(),
                        "hours_until": round(hours_until, 1),
                        "attendees": event.attendees or []
                    },
                    priority="high" if hours_until <= 2 else "medium",
                    confidence_score=0.9,
                    context_summary=f"Important meeting '{event.title}' in {round(hours_until, 1)} hours",
                    expires_at=event.start_time
                )
                self.db.add(trigger)
                triggers.append(trigger)
        
        self.db.commit()
        return triggers
    
    async def _detect_health_triggers(self) -> List[ProactiveTrigger]:
        """Detect triggers from health metric changes"""
        triggers = []
        
        # Get recent health metrics
        recent_metrics = self.db.query(HealthMetric).filter(
            and_(
                HealthMetric.entity_id == self.entity_id,
                HealthMetric.recorded_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).order_by(HealthMetric.recorded_at.desc()).limit(10).all()
        
        if not recent_metrics:
            return triggers
        
        # Analyze for significant changes using LLM
        metrics_summary = [
            {
                "type": m.metric_type,
                "value": m.value,
                "time": m.recorded_at.isoformat()
            }
            for m in recent_metrics
        ]
        
        analysis_prompt = f"""Analyze these health metrics for significant changes that warrant attention:

Metrics: {json.dumps(metrics_summary, indent=2)}

Respond with JSON:
{{
    "significant_change": true/false,
    "change_type": "improvement" or "decline" or "anomaly",
    "affected_metrics": ["list of metric types"],
    "severity": "low" or "medium" or "high",
    "summary": "brief description"
}}

Only flag as significant if there's a notable pattern or change."""

        try:
            response = await llm.complete([
                {"role": "system", "content": "You are a health data analyst. Be conservative - only flag truly significant changes."},
                {"role": "user", "content": analysis_prompt}
            ])
            
            # Parse response
            analysis = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            if analysis.get("significant_change"):
                trigger = ProactiveTrigger(
                    entity_id=self.entity_id,
                    trigger_type="health_change",
                    trigger_source="health",
                    trigger_data={
                        "change_type": analysis.get("change_type"),
                        "affected_metrics": analysis.get("affected_metrics", []),
                        "metrics_analyzed": len(recent_metrics)
                    },
                    priority=analysis.get("severity", "medium"),
                    confidence_score=0.8,
                    context_summary=analysis.get("summary", "Health metrics show significant change")
                )
                self.db.add(trigger)
                triggers.append(trigger)
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Error analyzing health metrics: {e}")
        
        return triggers
    
    async def _detect_goal_triggers(self) -> List[ProactiveTrigger]:
        """Detect goals that are stalling"""
        triggers = []
        
        # Get active goals
        goals = self.db.query(Goal).filter(
            and_(
                Goal.entity_id == self.entity_id,
                Goal.is_active == True
            )
        ).all()
        
        for goal in goals:
            # Check if goal hasn't been updated recently
            if goal.updated_at:
                days_since_update = (datetime.utcnow() - goal.updated_at.replace(tzinfo=None)).days
                
                if days_since_update >= 7 and goal.progress and goal.progress < 0.9:
                    trigger = ProactiveTrigger(
                        entity_id=self.entity_id,
                        trigger_type="goal_stall",
                        trigger_source="goals",
                        trigger_data={
                            "goal_id": str(goal.id),
                            "goal_title": goal.goal_title,
                            "current_progress": goal.progress,
                            "days_since_update": days_since_update
                        },
                        priority="medium" if days_since_update < 14 else "high",
                        confidence_score=0.85,
                        context_summary=f"Goal '{goal.goal_title}' hasn't progressed in {days_since_update} days"
                    )
                    self.db.add(trigger)
                    triggers.append(trigger)
        
        self.db.commit()
        return triggers
    
    async def _detect_social_triggers(self) -> List[ProactiveTrigger]:
        """Detect relationship decay or opportunities"""
        # This would analyze LinkedIn connections, email frequency, etc.
        # For now, returning empty - will be enhanced with social-context-engine
        return []


# ============================================================================
# INITIATIVE GENERATOR
# ============================================================================

class InitiativeGenerator:
    """
    Generates proactive initiatives with 4 options (GI X Protocol).
    
    Each initiative presents:
    - Option 1: Full action (NUCLEUS handles everything)
    - Option 2: Collaborative action (NUCLEUS prepares, user executes)
    - Option 3: Minimal action (Quick acknowledgment)
    - Option 4: Dismiss (Not relevant/not now)
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        self.entity = db.query(Entity).filter(Entity.id == entity_id).first()
        
        # Get entity's autonomy level
        self.autonomy = db.query(AutonomyLevel).filter(
            AutonomyLevel.entity_id == entity_id
        ).first()
        
    async def generate_initiative(self, trigger: ProactiveTrigger) -> ProactiveInitiative:
        """Generate an initiative from a trigger"""
        
        # Get entity context for personalization
        interests = self.db.query(Interest).filter(
            Interest.entity_id == self.entity_id
        ).limit(5).all()
        
        goals = self.db.query(Goal).filter(
            and_(
                Goal.entity_id == self.entity_id,
                Goal.is_active == True
            )
        ).limit(5).all()
        
        # Build context
        context = {
            "entity_name": self.entity.name if self.entity else "User",
            "interests": [i.interest_name for i in interests],
            "active_goals": [g.goal_title for g in goals],
            "autonomy_level": self.autonomy.current_level if self.autonomy else 2,
            "trigger": {
                "type": trigger.trigger_type,
                "source": trigger.trigger_source,
                "data": trigger.trigger_data,
                "summary": trigger.context_summary
            }
        }
        
        # Generate initiative using LLM
        generation_prompt = f"""Generate a proactive initiative for this situation.

Context:
- Entity: {context['entity_name']}
- Interests: {', '.join(context['interests']) or 'Not specified'}
- Active Goals: {', '.join(context['active_goals']) or 'Not specified'}
- Autonomy Level: {context['autonomy_level']}/5

Trigger:
- Type: {context['trigger']['type']}
- Source: {context['trigger']['source']}
- Summary: {context['trigger']['summary']}
- Data: {json.dumps(context['trigger']['data'], indent=2)}

Generate a helpful, proactive initiative with exactly 4 options following the GI X Protocol.

Respond with JSON:
{{
    "title": "Brief, action-oriented title",
    "message": "Personalized message explaining the situation and why you're reaching out",
    "options": [
        {{"id": "full", "text": "Full action option - NUCLEUS handles everything", "action_type": "autonomous"}},
        {{"id": "collab", "text": "Collaborative option - NUCLEUS prepares, user executes", "action_type": "collaborative"}},
        {{"id": "minimal", "text": "Minimal option - Quick acknowledgment", "action_type": "minimal"}},
        {{"id": "dismiss", "text": "Not relevant right now", "action_type": "dismiss"}}
    ],
    "optimal_time": "morning/afternoon/evening/now"
}}

Guidelines:
- Be warm but professional
- Reference specific context from the trigger
- Make options progressively less involved
- The full option should be genuinely helpful
- Respect the user's autonomy"""

        try:
            response = await llm.complete([
                {"role": "system", "content": "You are NUCLEUS, a proactive AI assistant. Generate helpful, personalized initiatives."},
                {"role": "user", "content": generation_prompt}
            ])
            
            # Parse response
            initiative_data = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            # Calculate optimal delivery time
            optimal_time = self._calculate_optimal_time(initiative_data.get("optimal_time", "now"))
            
            # Create initiative
            initiative = ProactiveInitiative(
                entity_id=self.entity_id,
                trigger_id=trigger.id,
                initiative_type=self._get_initiative_type(trigger.trigger_type),
                title=initiative_data["title"],
                message=initiative_data["message"],
                options=initiative_data["options"],
                optimal_delivery_time=optimal_time,
                delivery_channel="app",
                status="pending",
                meta_data={
                    "generation_context": context,
                    "llm_response": initiative_data
                }
            )
            
            self.db.add(initiative)
            
            # Update trigger status
            trigger.status = "processed"
            trigger.processed_at = datetime.utcnow()
            
            self.db.commit()
            
            return initiative
            
        except Exception as e:
            logger.error(f"Error generating initiative: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate initiative: {str(e)}")
    
    def _get_initiative_type(self, trigger_type: str) -> str:
        """Map trigger type to initiative type"""
        mapping = {
            "meeting_approaching": "reminder",
            "health_change": "alert",
            "goal_stall": "suggestion",
            "relationship_decay": "suggestion",
            "opportunity_detected": "suggestion"
        }
        return mapping.get(trigger_type, "suggestion")
    
    def _calculate_optimal_time(self, time_preference: str) -> datetime:
        """Calculate optimal delivery time"""
        now = datetime.utcnow()
        
        if time_preference == "now":
            return now
        elif time_preference == "morning":
            # Next morning at 9 AM
            target = now.replace(hour=9, minute=0, second=0)
            if now.hour >= 9:
                target += timedelta(days=1)
            return target
        elif time_preference == "afternoon":
            # Next afternoon at 2 PM
            target = now.replace(hour=14, minute=0, second=0)
            if now.hour >= 14:
                target += timedelta(days=1)
            return target
        elif time_preference == "evening":
            # Next evening at 6 PM
            target = now.replace(hour=18, minute=0, second=0)
            if now.hour >= 18:
                target += timedelta(days=1)
            return target
        else:
            return now


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/detect-triggers", response_model=TriggerDetectionResponse)
async def detect_triggers(
    request: TriggerDetectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Detect triggers that warrant proactive engagement.
    
    This endpoint scans various sources (calendar, health, goals, social)
    to identify situations where NUCLEUS should proactively reach out.
    """
    try:
        entity_id = UUID(request.entity_id)
        
        # Verify entity exists
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Detect triggers
        detector = TriggerDetector(db, entity_id)
        triggers = await detector.detect_all_triggers(request.trigger_sources)
        
        # Log behavior
        behavior_log = BehaviorLog(
            entity_id=entity_id,
            action_type="trigger_detection",
            action_description=f"Detected {len(triggers)} triggers from {request.trigger_sources}",
            action_input={"sources": request.trigger_sources},
            action_output={"trigger_count": len(triggers)},
            success=True,
            principle_compliance=True
        )
        db.add(behavior_log)
        db.commit()
        
        return TriggerDetectionResponse(
            entity_id=request.entity_id,
            triggers_detected=len(triggers),
            triggers=[
                {
                    "id": str(t.id),
                    "type": t.trigger_type,
                    "source": t.trigger_source,
                    "priority": t.priority,
                    "summary": t.context_summary
                }
                for t in triggers
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting triggers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-initiative", response_model=InitiativeResponse)
async def generate_initiative(
    request: InitiativeGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a proactive initiative from a trigger.
    
    Creates an initiative with 4 options following the GI X Protocol:
    1. Full action (autonomous)
    2. Collaborative action
    3. Minimal action
    4. Dismiss
    """
    try:
        trigger_id = UUID(request.trigger_id)
        entity_id = UUID(request.entity_id)
        
        # Get trigger
        trigger = db.query(ProactiveTrigger).filter(
            ProactiveTrigger.id == trigger_id
        ).first()
        
        if not trigger:
            raise HTTPException(status_code=404, detail="Trigger not found")
        
        # Generate initiative
        generator = InitiativeGenerator(db, entity_id)
        initiative = await generator.generate_initiative(trigger)
        
        # Publish event
        publisher.publish_event(
            "digital",
            "proactive.initiative.created",
            str(entity_id),
            {
                "initiative_id": str(initiative.id),
                "trigger_id": str(trigger_id),
                "title": initiative.title
            }
        )
        
        return InitiativeResponse(
            initiative_id=str(initiative.id),
            title=initiative.title,
            message=initiative.message,
            options=initiative.options,
            optimal_delivery_time=initiative.optimal_delivery_time.isoformat() if initiative.optimal_delivery_time else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating initiative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/respond-to-initiative")
async def respond_to_initiative(
    request: InitiativeResponseRequest,
    db: Session = Depends(get_db)
):
    """
    Record user response to an initiative.
    
    This feedback is used to improve future initiatives through
    the Self-Evolution Engine.
    """
    try:
        initiative_id = UUID(request.initiative_id)
        
        # Get initiative
        initiative = db.query(ProactiveInitiative).filter(
            ProactiveInitiative.id == initiative_id
        ).first()
        
        if not initiative:
            raise HTTPException(status_code=404, detail="Initiative not found")
        
        # Update initiative
        initiative.selected_option_id = request.selected_option_id
        initiative.status = "responded"
        initiative.responded_at = datetime.utcnow()
        initiative.user_response = {
            "option_id": request.selected_option_id,
            "feedback": request.feedback,
            "response_time_seconds": (datetime.utcnow() - initiative.delivered_at).total_seconds() if initiative.delivered_at else None
        }
        
        # Calculate response quality score
        # Higher score for engaged responses (full/collab), lower for dismissals
        quality_scores = {
            "full": 1.0,
            "collab": 0.8,
            "minimal": 0.5,
            "dismiss": 0.2
        }
        initiative.response_quality_score = quality_scores.get(request.selected_option_id, 0.5)
        
        db.commit()
        
        # Publish event for learning
        publisher.publish_event(
            "digital",
            "proactive.initiative.responded",
            str(initiative.entity_id),
            {
                "initiative_id": str(initiative_id),
                "selected_option": request.selected_option_id,
                "quality_score": initiative.response_quality_score
            }
        )
        
        return {
            "status": "success",
            "message": "Response recorded",
            "quality_score": initiative.response_quality_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pending-initiatives/{entity_id}")
async def get_pending_initiatives(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get all pending initiatives for an entity"""
    try:
        initiatives = db.query(ProactiveInitiative).filter(
            and_(
                ProactiveInitiative.entity_id == UUID(entity_id),
                ProactiveInitiative.status == "pending"
            )
        ).order_by(ProactiveInitiative.optimal_delivery_time).all()
        
        return {
            "entity_id": entity_id,
            "count": len(initiatives),
            "initiatives": [
                {
                    "id": str(i.id),
                    "title": i.title,
                    "message": i.message,
                    "options": i.options,
                    "optimal_delivery_time": i.optimal_delivery_time.isoformat() if i.optimal_delivery_time else None
                }
                for i in initiatives
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting pending initiatives: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "proactive-engagement-engine", "version": "2.0.0"}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
