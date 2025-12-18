"""
NUCLEUS V2.0 - Autonomy Manager

Manages the progression of autonomy levels (30% → 95%) based on:
1. Trust building through successful interactions
2. Performance metrics and consistency
3. User preferences and comfort level
4. Principle compliance history

Based on:
- Datasaur 2025: 5 Levels of Agentic AI Autonomy (like autonomous vehicles)
- NUCLEUS Agent Document: "מסלול אוטונומיה הדרגתי"
- GI X Document: Progressive trust building
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
from models.dna import Entity
from models.nucleus_core import (
    AutonomyLevel, AutonomyTransition,
    BehaviorLog, PrincipleViolation
)
from pubsub.publisher import get_publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Autonomy Manager",
    description="Manages progressive autonomy levels (30% → 95%)",
    version="2.0.0"
)

publisher = get_publisher()

# ============================================================================
# AUTONOMY LEVEL DEFINITIONS
# ============================================================================

AUTONOMY_LEVELS = {
    1: {
        "name": "Guided",
        "percentage": 30,
        "description": "NUCLEUS suggests, user decides everything",
        "capabilities": ["suggest", "remind", "inform"],
        "requires_approval": ["all_actions"],
        "min_trust_score": 0.0,
        "min_success_rate": 0.0,
        "min_interactions": 0
    },
    2: {
        "name": "Assisted",
        "percentage": 50,
        "description": "NUCLEUS can execute low-risk actions autonomously",
        "capabilities": ["suggest", "remind", "inform", "execute_low_risk"],
        "requires_approval": ["medium_risk", "high_risk"],
        "min_trust_score": 0.4,
        "min_success_rate": 0.7,
        "min_interactions": 50
    },
    3: {
        "name": "Collaborative",
        "percentage": 70,
        "description": "NUCLEUS handles routine tasks, consults on important ones",
        "capabilities": ["suggest", "remind", "inform", "execute_low_risk", "execute_medium_risk"],
        "requires_approval": ["high_risk"],
        "min_trust_score": 0.6,
        "min_success_rate": 0.8,
        "min_interactions": 200
    },
    4: {
        "name": "Autonomous",
        "percentage": 85,
        "description": "NUCLEUS acts independently with periodic check-ins",
        "capabilities": ["suggest", "remind", "inform", "execute_low_risk", "execute_medium_risk", "execute_high_risk"],
        "requires_approval": ["critical"],
        "min_trust_score": 0.8,
        "min_success_rate": 0.9,
        "min_interactions": 500
    },
    5: {
        "name": "Full Autonomy",
        "percentage": 95,
        "description": "NUCLEUS operates as a trusted partner with minimal oversight",
        "capabilities": ["all"],
        "requires_approval": ["user_requested"],
        "min_trust_score": 0.95,
        "min_success_rate": 0.95,
        "min_interactions": 1000
    }
}


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AutonomyStatusRequest(BaseModel):
    entity_id: str


class AutonomyStatusResponse(BaseModel):
    entity_id: str
    current_level: int
    level_name: str
    percentage: int
    trust_score: float
    success_rate: float
    total_interactions: int
    next_level_requirements: Optional[Dict[str, Any]]
    capabilities: List[str]
    requires_approval: List[str]


class LevelTransitionRequest(BaseModel):
    entity_id: str
    target_level: int
    reason: str
    force: bool = False


class TrustUpdateRequest(BaseModel):
    entity_id: str
    interaction_success: bool
    interaction_type: str
    principle_compliant: bool


# ============================================================================
# AUTONOMY CALCULATOR
# ============================================================================

class AutonomyCalculator:
    """Calculates trust scores and determines level eligibility"""
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    def calculate_trust_score(self, days: int = 30) -> float:
        """Calculate trust score based on recent interactions"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(BehaviorLog).filter(
            and_(
                BehaviorLog.entity_id == self.entity_id,
                BehaviorLog.created_at >= cutoff
            )
        ).all()
        
        if not logs:
            return 0.0
        
        # Factors: success rate, principle compliance, consistency
        success_count = sum(1 for l in logs if l.success)
        compliance_count = sum(1 for l in logs if l.principle_compliance)
        
        success_rate = success_count / len(logs)
        compliance_rate = compliance_count / len(logs)
        
        # Check for violations
        violations = self.db.query(PrincipleViolation).filter(
            and_(
                PrincipleViolation.entity_id == self.entity_id,
                PrincipleViolation.created_at >= cutoff
            )
        ).count()
        
        violation_penalty = min(violations * 0.05, 0.3)  # Max 30% penalty
        
        # Calculate trust score
        trust_score = (success_rate * 0.4 + compliance_rate * 0.6) - violation_penalty
        return max(0.0, min(1.0, trust_score))
    
    def calculate_success_rate(self, days: int = 30) -> float:
        """Calculate success rate of interactions"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(BehaviorLog).filter(
            and_(
                BehaviorLog.entity_id == self.entity_id,
                BehaviorLog.created_at >= cutoff
            )
        ).all()
        
        if not logs:
            return 0.0
        
        return sum(1 for l in logs if l.success) / len(logs)
    
    def get_total_interactions(self) -> int:
        """Get total interaction count"""
        return self.db.query(BehaviorLog).filter(
            BehaviorLog.entity_id == self.entity_id
        ).count()
    
    def check_level_eligibility(self, target_level: int) -> Dict[str, Any]:
        """Check if entity is eligible for a level"""
        requirements = AUTONOMY_LEVELS.get(target_level, {})
        
        trust_score = self.calculate_trust_score()
        success_rate = self.calculate_success_rate()
        total_interactions = self.get_total_interactions()
        
        return {
            "eligible": (
                trust_score >= requirements.get("min_trust_score", 0) and
                success_rate >= requirements.get("min_success_rate", 0) and
                total_interactions >= requirements.get("min_interactions", 0)
            ),
            "current_metrics": {
                "trust_score": trust_score,
                "success_rate": success_rate,
                "total_interactions": total_interactions
            },
            "requirements": {
                "min_trust_score": requirements.get("min_trust_score", 0),
                "min_success_rate": requirements.get("min_success_rate", 0),
                "min_interactions": requirements.get("min_interactions", 0)
            },
            "gaps": {
                "trust_score": max(0, requirements.get("min_trust_score", 0) - trust_score),
                "success_rate": max(0, requirements.get("min_success_rate", 0) - success_rate),
                "interactions": max(0, requirements.get("min_interactions", 0) - total_interactions)
            }
        }


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/status/{entity_id}", response_model=AutonomyStatusResponse)
async def get_autonomy_status(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get current autonomy status for an entity"""
    try:
        eid = UUID(entity_id)
        
        # Get or create autonomy level
        autonomy = db.query(AutonomyLevel).filter(
            AutonomyLevel.entity_id == eid
        ).first()
        
        if not autonomy:
            # Create default level 1
            autonomy = AutonomyLevel(
                entity_id=eid,
                current_level=1,
                trust_score=0.0,
                success_rate=0.0,
                total_interactions=0
            )
            db.add(autonomy)
            db.commit()
        
        # Calculate current metrics
        calculator = AutonomyCalculator(db, eid)
        trust_score = calculator.calculate_trust_score()
        success_rate = calculator.calculate_success_rate()
        total_interactions = calculator.get_total_interactions()
        
        # Update stored values
        autonomy.trust_score = trust_score
        autonomy.success_rate = success_rate
        autonomy.total_interactions = total_interactions
        autonomy.last_evaluated_at = datetime.utcnow()
        db.commit()
        
        level_info = AUTONOMY_LEVELS.get(autonomy.current_level, AUTONOMY_LEVELS[1])
        
        # Check next level requirements
        next_level = autonomy.current_level + 1
        next_requirements = None
        if next_level <= 5:
            eligibility = calculator.check_level_eligibility(next_level)
            next_requirements = {
                "level": next_level,
                "name": AUTONOMY_LEVELS[next_level]["name"],
                "eligible": eligibility["eligible"],
                "gaps": eligibility["gaps"]
            }
        
        return AutonomyStatusResponse(
            entity_id=entity_id,
            current_level=autonomy.current_level,
            level_name=level_info["name"],
            percentage=level_info["percentage"],
            trust_score=trust_score,
            success_rate=success_rate,
            total_interactions=total_interactions,
            next_level_requirements=next_requirements,
            capabilities=level_info["capabilities"],
            requires_approval=level_info["requires_approval"]
        )
        
    except Exception as e:
        logger.error(f"Error getting autonomy status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transition")
async def transition_level(
    request: LevelTransitionRequest,
    db: Session = Depends(get_db)
):
    """Transition to a new autonomy level"""
    try:
        eid = UUID(request.entity_id)
        
        autonomy = db.query(AutonomyLevel).filter(
            AutonomyLevel.entity_id == eid
        ).first()
        
        if not autonomy:
            raise HTTPException(status_code=404, detail="Autonomy record not found")
        
        # Check eligibility unless forced
        if not request.force:
            calculator = AutonomyCalculator(db, eid)
            eligibility = calculator.check_level_eligibility(request.target_level)
            
            if not eligibility["eligible"]:
                return {
                    "status": "rejected",
                    "reason": "Requirements not met",
                    "gaps": eligibility["gaps"]
                }
        
        # Record transition
        transition = AutonomyTransition(
            entity_id=eid,
            from_level=autonomy.current_level,
            to_level=request.target_level,
            transition_reason=request.reason,
            triggered_by="user" if request.force else "system",
            trust_score_at_transition=autonomy.trust_score,
            success_rate_at_transition=autonomy.success_rate
        )
        db.add(transition)
        
        # Update level
        old_level = autonomy.current_level
        autonomy.current_level = request.target_level
        autonomy.level_changed_at = datetime.utcnow()
        
        db.commit()
        
        # Publish event
        publisher.publish_event(
            "digital",
            "autonomy.level.changed",
            request.entity_id,
            {
                "from_level": old_level,
                "to_level": request.target_level,
                "reason": request.reason
            }
        )
        
        return {
            "status": "success",
            "from_level": old_level,
            "to_level": request.target_level,
            "new_capabilities": AUTONOMY_LEVELS[request.target_level]["capabilities"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transitioning level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-trust")
async def update_trust(
    request: TrustUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update trust score based on an interaction"""
    try:
        eid = UUID(request.entity_id)
        
        # Log the behavior
        log = BehaviorLog(
            entity_id=eid,
            action_type=request.interaction_type,
            action_description=f"Interaction: {request.interaction_type}",
            success=request.interaction_success,
            principle_compliance=request.principle_compliant
        )
        db.add(log)
        
        # Recalculate trust
        calculator = AutonomyCalculator(db, eid)
        new_trust = calculator.calculate_trust_score()
        new_success_rate = calculator.calculate_success_rate()
        
        # Update autonomy record
        autonomy = db.query(AutonomyLevel).filter(
            AutonomyLevel.entity_id == eid
        ).first()
        
        if autonomy:
            autonomy.trust_score = new_trust
            autonomy.success_rate = new_success_rate
            autonomy.total_interactions = calculator.get_total_interactions()
            
            # Check for automatic level up
            next_level = autonomy.current_level + 1
            if next_level <= 5:
                eligibility = calculator.check_level_eligibility(next_level)
                if eligibility["eligible"]:
                    # Auto-transition
                    transition = AutonomyTransition(
                        entity_id=eid,
                        from_level=autonomy.current_level,
                        to_level=next_level,
                        transition_reason="Automatic: Requirements met",
                        triggered_by="system",
                        trust_score_at_transition=new_trust,
                        success_rate_at_transition=new_success_rate
                    )
                    db.add(transition)
                    autonomy.current_level = next_level
                    autonomy.level_changed_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "success",
            "new_trust_score": new_trust,
            "new_success_rate": new_success_rate,
            "current_level": autonomy.current_level if autonomy else 1
        }
        
    except Exception as e:
        logger.error(f"Error updating trust: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{entity_id}")
async def get_transition_history(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get autonomy transition history"""
    try:
        transitions = db.query(AutonomyTransition).filter(
            AutonomyTransition.entity_id == UUID(entity_id)
        ).order_by(AutonomyTransition.created_at.desc()).limit(20).all()
        
        return {
            "entity_id": entity_id,
            "transitions": [
                {
                    "from": t.from_level,
                    "to": t.to_level,
                    "reason": t.transition_reason,
                    "triggered_by": t.triggered_by,
                    "trust_score": t.trust_score_at_transition,
                    "date": t.created_at.isoformat() if t.created_at else None
                }
                for t in transitions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "autonomy-manager", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
