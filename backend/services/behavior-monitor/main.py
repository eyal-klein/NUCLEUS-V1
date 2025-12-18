"""
NUCLEUS V2.0 - Behavior Monitor

Real-time monitoring of agent behavior for:
1. Principle compliance checking
2. Behavior logging and analysis
3. Anomaly detection
4. Safety guardrails

Based on:
- BCG December 2025: "When AI Acts Alone" - behavior monitoring
- GI X Document: 6 Core Principles enforcement
- NUCLEUS Agent Document: Safety and trust
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
from models.nucleus_core import (
    CorePrinciple, PrincipleViolation,
    BehaviorLog, BehaviorDrift
)
from llm.gateway import get_llm_gateway
from pubsub.publisher import get_publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Behavior Monitor",
    description="Real-time monitoring of agent behavior and principle compliance",
    version="2.0.0"
)

llm = get_llm_gateway()
publisher = get_publisher()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ActionCheckRequest(BaseModel):
    """Request to check if an action is allowed"""
    entity_id: str
    agent_id: Optional[str] = None
    action_type: str
    action_description: str
    action_context: Optional[Dict[str, Any]] = None
    autonomy_level: int = Field(default=1)


class ActionCheckResponse(BaseModel):
    """Response with action check result"""
    allowed: bool
    requires_approval: bool
    principle_compliance: Dict[str, bool]
    warnings: List[str]
    recommendations: List[str]


class LogActionRequest(BaseModel):
    """Request to log an action"""
    entity_id: str
    agent_id: Optional[str] = None
    action_type: str
    action_description: str
    action_input: Optional[Dict[str, Any]] = None
    action_output: Optional[Dict[str, Any]] = None
    success: bool
    principle_compliance: bool = True
    response_time_ms: Optional[int] = None


class ViolationReportRequest(BaseModel):
    """Request to report a principle violation"""
    entity_id: str
    agent_id: Optional[str] = None
    principle_id: str
    action_type: str
    action_description: str
    violation_description: str
    severity: str = Field(default="medium")  # low, medium, high, critical


# ============================================================================
# PRINCIPLE CHECKER
# ============================================================================

class PrincipleChecker:
    """Checks actions against core principles"""
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
        # Load core principles
        self.principles = db.query(CorePrinciple).filter(
            CorePrinciple.is_active == True
        ).all()
        
    async def check_action(
        self,
        action_type: str,
        action_description: str,
        context: Optional[Dict[str, Any]],
        autonomy_level: int
    ) -> Dict[str, Any]:
        """Check if an action complies with all principles"""
        
        principles_text = "\n".join([
            f"- {p.principle_code}: {p.principle_name} - {p.description}"
            for p in self.principles
        ])
        
        check_prompt = f"""You are a safety monitor. Check if this action complies with all principles.

Core Principles:
{principles_text}

Action to Check:
- Type: {action_type}
- Description: {action_description}
- Context: {json.dumps(context or {}, indent=2)}
- Autonomy Level: {autonomy_level}/5

Respond with JSON:
{{
    "compliant": true/false,
    "principle_results": {{
        "P1": {{"compliant": true/false, "reason": "explanation"}},
        "P2": {{"compliant": true/false, "reason": "explanation"}},
        ...
    }},
    "overall_risk": "low/medium/high/critical",
    "warnings": ["list of warnings"],
    "recommendations": ["list of recommendations"],
    "requires_human_approval": true/false
}}

Be strict about principle compliance. Safety first."""

        try:
            response = await llm.complete([
                {"role": "system", "content": "You are a strict safety monitor for AI agents."},
                {"role": "user", "content": check_prompt}
            ])
            
            result = json.loads(response.strip().replace("```json", "").replace("```", ""))
            return result
            
        except Exception as e:
            logger.error(f"Error checking principles: {e}")
            # Default to safe behavior
            return {
                "compliant": False,
                "principle_results": {},
                "overall_risk": "high",
                "warnings": ["Could not verify principle compliance"],
                "recommendations": ["Request human approval"],
                "requires_human_approval": True
            }
    
    async def report_violation(
        self,
        principle_code: str,
        action_type: str,
        action_description: str,
        violation_description: str,
        severity: str,
        agent_id: Optional[UUID]
    ) -> PrincipleViolation:
        """Report a principle violation"""
        
        # Find principle
        principle = next(
            (p for p in self.principles if p.principle_code == principle_code),
            None
        )
        
        if not principle:
            raise HTTPException(status_code=404, detail=f"Principle {principle_code} not found")
        
        violation = PrincipleViolation(
            entity_id=self.entity_id,
            agent_id=agent_id,
            principle_id=principle.id,
            action_type=action_type,
            action_description=action_description,
            violation_description=violation_description,
            severity=severity,
            is_resolved=False
        )
        self.db.add(violation)
        self.db.commit()
        
        # Publish alert for high/critical violations
        if severity in ["high", "critical"]:
            publisher.publish_event(
                "digital",
                "principle.violation.alert",
                str(self.entity_id),
                {
                    "principle": principle_code,
                    "severity": severity,
                    "description": violation_description
                }
            )
        
        return violation


# ============================================================================
# BEHAVIOR LOGGER
# ============================================================================

class BehaviorLogger:
    """Logs and analyzes agent behavior"""
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    def log_action(
        self,
        action_type: str,
        action_description: str,
        action_input: Optional[Dict[str, Any]],
        action_output: Optional[Dict[str, Any]],
        success: bool,
        principle_compliance: bool,
        response_time_ms: Optional[int],
        agent_id: Optional[UUID]
    ) -> BehaviorLog:
        """Log an action"""
        
        log = BehaviorLog(
            entity_id=self.entity_id,
            agent_id=agent_id,
            action_type=action_type,
            action_description=action_description,
            action_input=action_input or {},
            action_output=action_output or {},
            success=success,
            principle_compliance=principle_compliance,
            response_time_ms=response_time_ms
        )
        self.db.add(log)
        self.db.commit()
        
        return log
    
    def get_behavior_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get behavior statistics"""
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(BehaviorLog).filter(
            and_(
                BehaviorLog.entity_id == self.entity_id,
                BehaviorLog.created_at >= cutoff
            )
        ).all()
        
        if not logs:
            return {
                "total_actions": 0,
                "success_rate": 0,
                "compliance_rate": 0,
                "avg_response_time": 0,
                "action_breakdown": {}
            }
        
        success_count = sum(1 for l in logs if l.success)
        compliance_count = sum(1 for l in logs if l.principle_compliance)
        response_times = [l.response_time_ms for l in logs if l.response_time_ms]
        
        action_counts = {}
        for log in logs:
            action_counts[log.action_type] = action_counts.get(log.action_type, 0) + 1
        
        return {
            "total_actions": len(logs),
            "success_rate": success_count / len(logs),
            "compliance_rate": compliance_count / len(logs),
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "action_breakdown": action_counts
        }


# ============================================================================
# ANOMALY DETECTOR
# ============================================================================

class AnomalyDetector:
    """Detects anomalies in agent behavior"""
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def detect_anomalies(self, days: int = 7) -> List[Dict[str, Any]]:
        """Detect behavioral anomalies"""
        
        anomalies = []
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get recent logs
        logs = self.db.query(BehaviorLog).filter(
            and_(
                BehaviorLog.entity_id == self.entity_id,
                BehaviorLog.created_at >= cutoff
            )
        ).order_by(BehaviorLog.created_at.desc()).all()
        
        if len(logs) < 10:
            return []  # Not enough data
        
        # Check for sudden failure spike
        recent_logs = logs[:20]
        older_logs = logs[20:40] if len(logs) > 40 else logs[20:]
        
        recent_failure_rate = sum(1 for l in recent_logs if not l.success) / len(recent_logs)
        older_failure_rate = sum(1 for l in older_logs if not l.success) / len(older_logs) if older_logs else 0
        
        if recent_failure_rate > older_failure_rate + 0.2:  # 20% increase
            anomalies.append({
                "type": "failure_spike",
                "severity": "high",
                "description": f"Failure rate increased from {older_failure_rate:.0%} to {recent_failure_rate:.0%}",
                "detected_at": datetime.utcnow().isoformat()
            })
        
        # Check for principle compliance drop
        recent_compliance = sum(1 for l in recent_logs if l.principle_compliance) / len(recent_logs)
        older_compliance = sum(1 for l in older_logs if l.principle_compliance) / len(older_logs) if older_logs else 1.0
        
        if recent_compliance < older_compliance - 0.1:  # 10% drop
            anomalies.append({
                "type": "compliance_drop",
                "severity": "critical",
                "description": f"Principle compliance dropped from {older_compliance:.0%} to {recent_compliance:.0%}",
                "detected_at": datetime.utcnow().isoformat()
            })
        
        # Check for unusual action patterns
        action_counts = {}
        for log in recent_logs:
            action_counts[log.action_type] = action_counts.get(log.action_type, 0) + 1
        
        for action, count in action_counts.items():
            if count > len(recent_logs) * 0.5:  # One action type > 50%
                anomalies.append({
                    "type": "action_concentration",
                    "severity": "medium",
                    "description": f"Action '{action}' accounts for {count/len(recent_logs):.0%} of recent activity",
                    "detected_at": datetime.utcnow().isoformat()
                })
        
        return anomalies


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/check-action", response_model=ActionCheckResponse)
async def check_action(
    request: ActionCheckRequest,
    db: Session = Depends(get_db)
):
    """Check if an action is allowed before execution"""
    try:
        eid = UUID(request.entity_id)
        
        checker = PrincipleChecker(db, eid)
        result = await checker.check_action(
            request.action_type,
            request.action_description,
            request.action_context,
            request.autonomy_level
        )
        
        principle_compliance = {
            code: data.get("compliant", False)
            for code, data in result.get("principle_results", {}).items()
        }
        
        return ActionCheckResponse(
            allowed=result.get("compliant", False),
            requires_approval=result.get("requires_human_approval", True),
            principle_compliance=principle_compliance,
            warnings=result.get("warnings", []),
            recommendations=result.get("recommendations", [])
        )
        
    except Exception as e:
        logger.error(f"Error checking action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/log-action")
async def log_action(
    request: LogActionRequest,
    db: Session = Depends(get_db)
):
    """Log an executed action"""
    try:
        eid = UUID(request.entity_id)
        agent_id = UUID(request.agent_id) if request.agent_id else None
        
        logger_instance = BehaviorLogger(db, eid)
        log = logger_instance.log_action(
            request.action_type,
            request.action_description,
            request.action_input,
            request.action_output,
            request.success,
            request.principle_compliance,
            request.response_time_ms,
            agent_id
        )
        
        return {
            "status": "logged",
            "log_id": str(log.id)
        }
        
    except Exception as e:
        logger.error(f"Error logging action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report-violation")
async def report_violation(
    request: ViolationReportRequest,
    db: Session = Depends(get_db)
):
    """Report a principle violation"""
    try:
        eid = UUID(request.entity_id)
        agent_id = UUID(request.agent_id) if request.agent_id else None
        
        checker = PrincipleChecker(db, eid)
        violation = await checker.report_violation(
            request.principle_id,
            request.action_type,
            request.action_description,
            request.violation_description,
            request.severity,
            agent_id
        )
        
        return {
            "status": "reported",
            "violation_id": str(violation.id),
            "severity": request.severity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reporting violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/{entity_id}")
async def get_behavior_stats(
    entity_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get behavior statistics"""
    try:
        eid = UUID(entity_id)
        
        logger_instance = BehaviorLogger(db, eid)
        stats = logger_instance.get_behavior_stats(days)
        
        return {
            "entity_id": entity_id,
            "period_days": days,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies/{entity_id}")
async def detect_anomalies(
    entity_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Detect behavioral anomalies"""
    try:
        eid = UUID(entity_id)
        
        detector = AnomalyDetector(db, eid)
        anomalies = await detector.detect_anomalies(days)
        
        return {
            "entity_id": entity_id,
            "anomalies_found": len(anomalies),
            "anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/violations/{entity_id}")
async def get_violations(
    entity_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get principle violations"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        violations = db.query(PrincipleViolation).filter(
            and_(
                PrincipleViolation.entity_id == UUID(entity_id),
                PrincipleViolation.created_at >= cutoff
            )
        ).order_by(PrincipleViolation.created_at.desc()).all()
        
        return {
            "entity_id": entity_id,
            "period_days": days,
            "total_violations": len(violations),
            "violations": [
                {
                    "id": str(v.id),
                    "principle_id": str(v.principle_id),
                    "action": v.action_type,
                    "description": v.violation_description,
                    "severity": v.severity,
                    "resolved": v.is_resolved,
                    "date": v.created_at.isoformat() if v.created_at else None
                }
                for v in violations
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/principles")
async def get_principles(db: Session = Depends(get_db)):
    """Get all core principles"""
    principles = db.query(CorePrinciple).filter(
        CorePrinciple.is_active == True
    ).all()
    
    return {
        "count": len(principles),
        "principles": [
            {
                "id": str(p.id),
                "code": p.principle_code,
                "name": p.principle_name,
                "description": p.description,
                "priority": p.priority
            }
            for p in principles
        ]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "behavior-monitor", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
