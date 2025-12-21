"""
NUCLEUS V2.0 - Agent Health Monitor Service
Calculates and tracks agent health scores for lifecycle management
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import os
import uuid

# Import shared modules
import sys
sys.path.append("/app/backend")

from shared.models import (
    get_db, Agent, AgentPerformance
)
from shared.pubsub import get_pubsub_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NUCLEUS Agent Health Monitor",
    description="Calculates and tracks agent health scores",
    version="1.0.0"
)

# Initialize Pub/Sub client
project_id = os.getenv("PROJECT_ID")

if not project_id:

    raise ValueError("PROJECT_ID environment variable is required for proper GCP project isolation")
pubsub = get_pubsub_client(project_id)


# ============================================================================
# Pydantic Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class AgentHealthScore(BaseModel):
    agent_id: str
    agent_name: str
    health_score: float
    usage_frequency: float
    success_rate: float
    user_satisfaction: float
    cost_efficiency: float
    response_time_score: float
    trend: str
    risk_level: str
    recommendations: List[str]
    total_requests: int
    successful_requests: int
    failed_requests: int
    calculated_at: datetime


class HealthCalculationRequest(BaseModel):
    agent_id: Optional[str] = None  # If None, calculate for all agents
    days_back: int = 7


# ============================================================================
# Health Calculation Logic
# ============================================================================

class HealthCalculator:
    """
    Calculates agent health scores based on performance metrics
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def calculate_health(
        self,
        agent_id: uuid.UUID,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive health score for an agent
        
        Args:
            agent_id: UUID of the agent
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with health metrics
        """
        logger.info(f"Calculating health for agent {agent_id}")
        
        # Get agent info
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Get performance data
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        performance_records = self.db.query(AgentPerformance).filter(
            and_(
                AgentPerformance.agent_id == agent_id,
                AgentPerformance.recorded_at >= cutoff_date
            )
        ).all()
        
        if not performance_records:
            logger.warning(f"No performance data for agent {agent_id}")
            return self._default_health_score(agent)
        
        # Calculate component scores
        usage_frequency = self._calculate_usage_frequency(performance_records, days_back)
        success_rate = self._calculate_success_rate(performance_records)
        user_satisfaction = self._calculate_user_satisfaction(performance_records)
        cost_efficiency = self._calculate_cost_efficiency(performance_records)
        response_time_score = self._calculate_response_time_score(performance_records)
        
        # Calculate overall health score (weighted average)
        health_score = (
            usage_frequency * 0.20 +
            success_rate * 0.30 +
            user_satisfaction * 0.25 +
            cost_efficiency * 0.15 +
            response_time_score * 0.10
        )
        
        # Calculate trend
        trend = self._calculate_trend(agent_id, health_score)
        
        # Assess risk level
        risk_level = self._assess_risk_level(health_score, trend, success_rate)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            health_score, usage_frequency, success_rate,
            user_satisfaction, cost_efficiency, response_time_score
        )
        
        # Count requests
        total_requests = len(performance_records)
        successful_requests = sum(1 for r in performance_records if r.success)
        failed_requests = total_requests - successful_requests
        
        return {
            "agent_id": str(agent_id),
            "agent_name": agent.agent_name,
            "health_score": round(health_score, 3),
            "usage_frequency": round(usage_frequency, 3),
            "success_rate": round(success_rate, 3),
            "user_satisfaction": round(user_satisfaction, 3),
            "cost_efficiency": round(cost_efficiency, 3),
            "response_time_score": round(response_time_score, 3),
            "trend": trend,
            "risk_level": risk_level,
            "recommendations": recommendations,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "avg_response_time_ms": self._avg_response_time(performance_records),
            "calculated_at": datetime.utcnow()
        }
    
    def _calculate_usage_frequency(
        self,
        records: List[AgentPerformance],
        days_back: int
    ) -> float:
        """
        Calculate usage frequency score (0.0 to 1.0)
        
        Logic:
        - 0 requests/day = 0.0
        - 1 request/day = 0.3
        - 5 requests/day = 0.6
        - 10+ requests/day = 1.0
        """
        requests_per_day = len(records) / max(days_back, 1)
        
        if requests_per_day >= 10:
            return 1.0
        elif requests_per_day >= 5:
            return 0.6 + (requests_per_day - 5) * 0.08
        elif requests_per_day >= 1:
            return 0.3 + (requests_per_day - 1) * 0.075
        else:
            return requests_per_day * 0.3
    
    def _calculate_success_rate(self, records: List[AgentPerformance]) -> float:
        """
        Calculate success rate (0.0 to 1.0)
        """
        if not records:
            return 0.5  # Neutral if no data
        
        successful = sum(1 for r in records if r.success)
        return successful / len(records)
    
    def _calculate_user_satisfaction(self, records: List[AgentPerformance]) -> float:
        """
        Calculate user satisfaction score (0.0 to 1.0)
        
        Based on feedback_score if available, otherwise infer from success rate
        """
        feedback_scores = [r.feedback_score for r in records if r.feedback_score is not None]
        
        if feedback_scores:
            # Average feedback score (assuming 0-5 scale)
            avg_feedback = sum(feedback_scores) / len(feedback_scores)
            return min(avg_feedback / 5.0, 1.0)
        else:
            # Fallback: use success rate as proxy
            return self._calculate_success_rate(records)
    
    def _calculate_cost_efficiency(self, records: List[AgentPerformance]) -> float:
        """
        Calculate cost efficiency score (0.0 to 1.0)
        
        Logic: Lower cost per successful request = higher score
        """
        # TODO: Implement actual cost tracking
        # For now, return neutral score
        return 0.7
    
    def _calculate_response_time_score(self, records: List[AgentPerformance]) -> float:
        """
        Calculate response time score (0.0 to 1.0)
        
        Logic:
        - < 100ms = 1.0
        - 100-500ms = 0.8
        - 500-1000ms = 0.6
        - 1000-3000ms = 0.4
        - > 3000ms = 0.2
        """
        execution_times = [r.execution_time_ms for r in records if r.execution_time_ms is not None]
        
        if not execution_times:
            return 0.7  # Neutral if no data
        
        avg_time = sum(execution_times) / len(execution_times)
        
        if avg_time < 100:
            return 1.0
        elif avg_time < 500:
            return 0.8
        elif avg_time < 1000:
            return 0.6
        elif avg_time < 3000:
            return 0.4
        else:
            return 0.2
    
    def _calculate_trend(self, agent_id: uuid.UUID, current_score: float) -> str:
        """
        Calculate health trend by comparing with previous score
        """
        # Get previous health score (if exists)
        from sqlalchemy import text
        
        query = text("""
            SELECT health_score, calculated_at
            FROM assembly.agent_health
            WHERE agent_id = :agent_id
            ORDER BY calculated_at DESC
            LIMIT 2
        """)
        
        previous_scores = self.db.execute(query, {"agent_id": str(agent_id)}).fetchall()
        
        if len(previous_scores) < 1:
            return "unknown"
        
        previous_score = previous_scores[0][0]
        
        diff = current_score - previous_score
        
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"
    
    def _assess_risk_level(
        self,
        health_score: float,
        trend: str,
        success_rate: float
    ) -> str:
        """
        Assess risk level based on health score and trend
        """
        if health_score < 0.3 or success_rate < 0.5:
            return "critical"
        elif health_score < 0.5 or (trend == "declining" and health_score < 0.7):
            return "high"
        elif health_score < 0.7 or trend == "declining":
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(
        self,
        health_score: float,
        usage_frequency: float,
        success_rate: float,
        user_satisfaction: float,
        cost_efficiency: float,
        response_time_score: float
    ) -> List[str]:
        """
        Generate actionable recommendations based on scores
        """
        recommendations = []
        
        if health_score < 0.3:
            recommendations.append("URGENT: Consider shutting down this agent")
        elif health_score < 0.5:
            recommendations.append("Agent needs immediate improvement")
        
        if usage_frequency < 0.3:
            recommendations.append("Low usage - consider if agent is still needed")
        
        if success_rate < 0.6:
            recommendations.append("High failure rate - review agent logic and tools")
        
        if user_satisfaction < 0.6:
            recommendations.append("Low user satisfaction - gather feedback and improve")
        
        if cost_efficiency < 0.5:
            recommendations.append("High cost - optimize resource usage")
        
        if response_time_score < 0.5:
            recommendations.append("Slow response time - optimize performance")
        
        if not recommendations:
            recommendations.append("Agent is healthy - continue monitoring")
        
        return recommendations
    
    def _avg_response_time(self, records: List[AgentPerformance]) -> Optional[float]:
        """Calculate average response time"""
        times = [r.execution_time_ms for r in records if r.execution_time_ms is not None]
        return round(sum(times) / len(times), 2) if times else None
    
    def _default_health_score(self, agent: Agent) -> Dict[str, Any]:
        """Return default health score for agents with no data"""
        return {
            "agent_id": str(agent.id),
            "agent_name": agent.agent_name,
            "health_score": 0.5,
            "usage_frequency": 0.0,
            "success_rate": 0.5,
            "user_satisfaction": 0.5,
            "cost_efficiency": 0.5,
            "response_time_score": 0.5,
            "trend": "unknown",
            "risk_level": "medium",
            "recommendations": ["No performance data available yet"],
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time_ms": None,
            "calculated_at": datetime.utcnow()
        }
    
    def save_health_score(self, health_data: Dict[str, Any]):
        """
        Save health score to database
        """
        from sqlalchemy import text
        
        query = text("""
            INSERT INTO assembly.agent_health (
                agent_id, health_score, usage_frequency, success_rate,
                user_satisfaction, cost_efficiency, response_time_score,
                total_requests, successful_requests, failed_requests,
                avg_response_time_ms, trend, risk_level, recommendations,
                calculated_at
            ) VALUES (
                :agent_id, :health_score, :usage_frequency, :success_rate,
                :user_satisfaction, :cost_efficiency, :response_time_score,
                :total_requests, :successful_requests, :failed_requests,
                :avg_response_time_ms, :trend, :risk_level, :recommendations::jsonb,
                :calculated_at
            )
        """)
        
        self.db.execute(query, {
            "agent_id": health_data["agent_id"],
            "health_score": health_data["health_score"],
            "usage_frequency": health_data["usage_frequency"],
            "success_rate": health_data["success_rate"],
            "user_satisfaction": health_data["user_satisfaction"],
            "cost_efficiency": health_data["cost_efficiency"],
            "response_time_score": health_data["response_time_score"],
            "total_requests": health_data["total_requests"],
            "successful_requests": health_data["successful_requests"],
            "failed_requests": health_data["failed_requests"],
            "avg_response_time_ms": health_data["avg_response_time_ms"],
            "trend": health_data["trend"],
            "risk_level": health_data["risk_level"],
            "recommendations": str(health_data["recommendations"]).replace("'", '"'),
            "calculated_at": health_data["calculated_at"]
        })
        
        self.db.commit()
        logger.info(f"Saved health score for agent {health_data['agent_id']}")


# ============================================================================
# API Routes
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent-health-monitor",
        "version": "1.0.0"
    }


@app.post("/calculate", response_model=List[AgentHealthScore])
async def calculate_health(
    request: HealthCalculationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Calculate health scores for agents
    
    If agent_id is provided, calculate for that agent only.
    Otherwise, calculate for all active agents.
    """
    logger.info(f"Health calculation request: {request}")
    
    calculator = HealthCalculator(db)
    results = []
    
    if request.agent_id:
        # Calculate for specific agent
        try:
            health_data = calculator.calculate_health(
                uuid.UUID(request.agent_id),
                request.days_back
            )
            calculator.save_health_score(health_data)
            results.append(AgentHealthScore(**health_data))
            
            # Publish health event if critical
            if health_data["risk_level"] == "critical":
                background_tasks.add_task(
                    publish_health_alert,
                    health_data
                )
        except Exception as e:
            logger.error(f"Error calculating health for agent {request.agent_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Calculate for all active agents
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        
        for agent in agents:
            try:
                health_data = calculator.calculate_health(agent.id, request.days_back)
                calculator.save_health_score(health_data)
                results.append(AgentHealthScore(**health_data))
                
                # Publish health event if critical
                if health_data["risk_level"] == "critical":
                    background_tasks.add_task(
                        publish_health_alert,
                        health_data
                    )
            except Exception as e:
                logger.error(f"Error calculating health for agent {agent.id}: {e}")
                continue
    
    logger.info(f"Calculated health for {len(results)} agents")
    return results


@app.get("/agents/{agent_id}/health", response_model=AgentHealthScore)
async def get_agent_health(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """
    Get latest health score for an agent
    """
    from sqlalchemy import text
    
    query = text("""
        SELECT * FROM assembly.agent_health_latest
        WHERE agent_id = :agent_id
    """)
    
    result = db.execute(query, {"agent_id": agent_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="No health data found for this agent")
    
    # Get agent name
    agent = db.query(Agent).filter(Agent.id == uuid.UUID(agent_id)).first()
    
    return AgentHealthScore(
        agent_id=str(result[0]),
        agent_name=agent.agent_name if agent else "Unknown",
        health_score=result[1],
        usage_frequency=result[2],
        success_rate=result[3],
        user_satisfaction=result[4],
        cost_efficiency=result[5],
        response_time_score=result[6],
        trend=result[7],
        risk_level=result[8],
        recommendations=result[9] if result[9] else [],
        total_requests=0,  # Not in view
        successful_requests=0,
        failed_requests=0,
        calculated_at=result[10]
    )


@app.get("/agents/health/summary")
async def get_health_summary(db: Session = Depends(get_db)):
    """
    Get health summary for all agents
    """
    from sqlalchemy import text
    
    query = text("""
        SELECT * FROM assembly.agent_health_summary
        ORDER BY health_score ASC NULLS LAST
    """)
    
    results = db.execute(query).fetchall()
    
    return [
        {
            "agent_id": str(row[0]),
            "agent_name": row[1],
            "agent_type": row[2],
            "is_active": row[3],
            "health_score": row[4],
            "trend": row[5],
            "risk_level": row[6],
            "total_requests": row[7],
            "successful_requests": row[8],
            "failed_requests": row[9],
            "success_rate": row[10],
            "last_health_check": row[11]
        }
        for row in results
    ]


# ============================================================================
# Background Tasks
# ============================================================================

async def publish_health_alert(health_data: Dict[str, Any]):
    """
    Publish health alert to Pub/Sub for critical agents
    """
    try:
        await pubsub.publish(
            topic_name="agent-health-alerts",
            message_data={
                "event_type": "health_alert",
                "agent_id": health_data["agent_id"],
                "agent_name": health_data["agent_name"],
                "health_score": health_data["health_score"],
                "risk_level": health_data["risk_level"],
                "recommendations": health_data["recommendations"],
                "calculated_at": health_data["calculated_at"].isoformat()
            }
        )
        logger.info(f"Published health alert for agent {health_data['agent_id']}")
    except Exception as e:
        logger.error(f"Failed to publish health alert: {e}")


# ============================================================================
# Startup & Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Agent Health Monitor service starting up...")
    logger.info("Agent Health Monitor service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Agent Health Monitor service shutting down...")
    await pubsub.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
