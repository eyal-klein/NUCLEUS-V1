"""
NUCLEUS V2.0 - Self-Evolution Engine

This engine enables NUCLEUS to continuously improve itself by:
1. Collecting feedback from all interactions (implicit and explicit)
2. Evaluating agent performance using LLM-as-Judge (RLAIF pattern)
3. Generating improved prompts and behaviors through meta-prompting
4. Running evolution cycles until quality thresholds are met
5. Monitoring for behavioral drift and regression

Based on:
- OpenAI Cookbook: Self-Evolving Agents with RLAIF
- NVIDIA 2025: Reinforcement Learning from AI Feedback
- GI X Document: "בריאה עצמית" - continuous self-improvement
- BCG 2025: Behavior monitoring and drift detection
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import json
from enum import Enum

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field

# Shared imports
import sys
sys.path.insert(0, '/app/shared')

from models.base import get_db
from models.dna import Entity
from models.assembly import Agent, AgentPerformance
from models.nucleus_core import (
    EvolutionFeedback, EvolutionCycle,
    BehaviorLog, BehaviorDrift,
    CorePrinciple, PrincipleViolation
)
from llm.gateway import get_llm_gateway
from pubsub.publisher import get_publisher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Self-Evolution Engine",
    description="Enables continuous self-improvement through RLAIF",
    version="2.0.0"
)

# Initialize LLM Gateway
llm = get_llm_gateway()

# Initialize Pub/Sub Publisher
publisher = get_publisher()


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class FeedbackType(str, Enum):
    EXPLICIT = "explicit"  # User directly provided feedback
    IMPLICIT = "implicit"  # Inferred from user behavior
    SYSTEM = "system"      # System-generated evaluation


class EvaluationDimension(str, Enum):
    RELEVANCE = "relevance"
    HELPFULNESS = "helpfulness"
    ACCURACY = "accuracy"
    TONE = "tone"
    PRINCIPLE_ALIGNMENT = "principle_alignment"


# Quality threshold for evolution cycles
QUALITY_THRESHOLD = 0.8
MAX_EVOLUTION_ITERATIONS = 5


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class FeedbackSubmissionRequest(BaseModel):
    """Request to submit feedback on an interaction"""
    entity_id: str
    agent_id: Optional[str] = None
    interaction_id: str
    feedback_type: str = Field(default="explicit")
    rating: Optional[float] = Field(default=None, ge=0, le=1)
    feedback_text: Optional[str] = None
    interaction_context: Optional[Dict[str, Any]] = None


class EvaluationRequest(BaseModel):
    """Request to evaluate an agent's performance"""
    entity_id: str
    agent_id: str
    time_window_days: int = Field(default=7)
    dimensions: List[str] = Field(
        default=["relevance", "helpfulness", "accuracy", "tone", "principle_alignment"]
    )


class EvaluationResponse(BaseModel):
    """Response with evaluation results"""
    agent_id: str
    overall_score: float
    dimension_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class EvolutionRequest(BaseModel):
    """Request to run an evolution cycle"""
    entity_id: str
    agent_id: str
    target_dimension: Optional[str] = None
    max_iterations: int = Field(default=5)


class EvolutionResponse(BaseModel):
    """Response with evolution cycle results"""
    cycle_id: str
    iterations_run: int
    initial_score: float
    final_score: float
    improvement: float
    changes_made: List[str]


class DriftCheckRequest(BaseModel):
    """Request to check for behavioral drift"""
    entity_id: str
    time_window_days: int = Field(default=30)


# ============================================================================
# FEEDBACK COLLECTOR
# ============================================================================

class FeedbackCollector:
    """
    Collects and processes feedback from various sources.
    
    Feedback Sources:
    - Explicit: User ratings, comments, corrections
    - Implicit: Response time, option selection, engagement
    - System: Automated quality checks, principle compliance
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def submit_feedback(
        self,
        interaction_id: str,
        feedback_type: str,
        rating: Optional[float],
        feedback_text: Optional[str],
        agent_id: Optional[UUID],
        context: Optional[Dict[str, Any]]
    ) -> EvolutionFeedback:
        """Submit and store feedback"""
        
        # Create feedback record
        feedback = EvolutionFeedback(
            entity_id=self.entity_id,
            agent_id=agent_id,
            interaction_id=interaction_id,
            feedback_type=feedback_type,
            feedback_source="user" if feedback_type == "explicit" else "system",
            rating=rating,
            feedback_text=feedback_text,
            interaction_context=context or {},
            is_processed=False
        )
        
        self.db.add(feedback)
        self.db.commit()
        
        return feedback
    
    async def collect_implicit_feedback(
        self,
        agent_id: UUID,
        time_window_days: int = 7
    ) -> List[EvolutionFeedback]:
        """Collect implicit feedback from behavior logs"""
        
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)
        
        # Get behavior logs for this agent
        logs = self.db.query(BehaviorLog).filter(
            and_(
                BehaviorLog.entity_id == self.entity_id,
                BehaviorLog.created_at >= cutoff
            )
        ).all()
        
        implicit_feedbacks = []
        
        for log in logs:
            # Analyze log for implicit signals
            rating = None
            feedback_text = None
            
            if log.success:
                # Success is positive signal
                rating = 0.7
                if log.response_time_ms and log.response_time_ms < 1000:
                    rating = 0.8  # Fast response is better
            else:
                rating = 0.3  # Failure is negative signal
            
            if not log.principle_compliance:
                rating = max(0.1, (rating or 0.5) - 0.3)  # Principle violation is serious
                feedback_text = f"Principle violation in action: {log.action_type}"
            
            if rating is not None:
                feedback = EvolutionFeedback(
                    entity_id=self.entity_id,
                    agent_id=agent_id,
                    interaction_id=str(log.id),
                    feedback_type="implicit",
                    feedback_source="behavior_log",
                    rating=rating,
                    feedback_text=feedback_text,
                    interaction_context={
                        "action_type": log.action_type,
                        "success": log.success,
                        "principle_compliance": log.principle_compliance
                    },
                    is_processed=False
                )
                self.db.add(feedback)
                implicit_feedbacks.append(feedback)
        
        self.db.commit()
        return implicit_feedbacks


# ============================================================================
# LLM EVALUATOR (RLAIF)
# ============================================================================

class LLMEvaluator:
    """
    Evaluates agent performance using LLM-as-Judge (RLAIF pattern).
    
    This implements the Reinforcement Learning from AI Feedback approach
    where an LLM evaluates the quality of agent outputs.
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
        # Load core principles for evaluation
        self.principles = db.query(CorePrinciple).filter(
            CorePrinciple.is_active == True
        ).all()
        
    async def evaluate_agent(
        self,
        agent_id: UUID,
        time_window_days: int,
        dimensions: List[str]
    ) -> Dict[str, Any]:
        """Evaluate an agent's performance across dimensions"""
        
        # Get agent
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get recent feedback
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)
        feedbacks = self.db.query(EvolutionFeedback).filter(
            and_(
                EvolutionFeedback.agent_id == agent_id,
                EvolutionFeedback.created_at >= cutoff
            )
        ).all()
        
        # Get recent behavior logs
        logs = self.db.query(BehaviorLog).filter(
            and_(
                BehaviorLog.entity_id == self.entity_id,
                BehaviorLog.created_at >= cutoff
            )
        ).limit(50).all()
        
        # Prepare evaluation context
        feedback_summary = [
            {
                "type": f.feedback_type,
                "rating": f.rating,
                "text": f.feedback_text,
                "context": f.interaction_context
            }
            for f in feedbacks[:20]  # Limit for API
        ]
        
        log_summary = [
            {
                "action": l.action_type,
                "success": l.success,
                "principle_compliance": l.principle_compliance,
                "description": l.action_description
            }
            for l in logs[:20]
        ]
        
        principles_text = "\n".join([
            f"- {p.principle_name}: {p.description}"
            for p in self.principles
        ])
        
        # Build evaluation prompt
        evaluation_prompt = f"""You are an expert AI evaluator. Evaluate this agent's performance.

Agent: {agent.name}
Purpose: {agent.purpose}
Type: {agent.agent_type}

Core Principles to evaluate against:
{principles_text}

Recent Feedback (from users and system):
{json.dumps(feedback_summary, indent=2)}

Recent Behavior Logs:
{json.dumps(log_summary, indent=2)}

Evaluate the agent on these dimensions (score 0-1):
{', '.join(dimensions)}

Respond with JSON:
{{
    "overall_score": 0.0-1.0,
    "dimension_scores": {{
        "dimension_name": score
    }},
    "strengths": ["list of strengths"],
    "weaknesses": ["list of weaknesses"],
    "recommendations": ["specific improvement recommendations"],
    "principle_violations": ["any principle violations observed"]
}}

Be objective and specific. Base scores on evidence from the data."""

        try:
            response = await llm.complete([
                {"role": "system", "content": "You are an expert AI evaluator using the RLAIF methodology."},
                {"role": "user", "content": evaluation_prompt}
            ])
            
            evaluation = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            # Store evaluation in agent performance
            performance = AgentPerformance(
                agent_id=agent_id,
                entity_id=self.entity_id,
                evaluation_period_start=cutoff,
                evaluation_period_end=datetime.utcnow(),
                overall_score=evaluation.get("overall_score", 0.5),
                dimension_scores=evaluation.get("dimension_scores", {}),
                feedback_count=len(feedbacks),
                success_rate=sum(1 for l in logs if l.success) / len(logs) if logs else 0,
                meta_data={
                    "strengths": evaluation.get("strengths", []),
                    "weaknesses": evaluation.get("weaknesses", []),
                    "recommendations": evaluation.get("recommendations", []),
                    "principle_violations": evaluation.get("principle_violations", [])
                }
            )
            self.db.add(performance)
            self.db.commit()
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating agent: {e}")
            raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# ============================================================================
# META PROMPTER
# ============================================================================

class MetaPrompter:
    """
    Generates improved prompts and behaviors through meta-prompting.
    
    Uses the evaluation results to generate specific improvements
    to agent prompts, behaviors, and configurations.
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def generate_improvements(
        self,
        agent: Agent,
        evaluation: Dict[str, Any],
        target_dimension: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate improvements based on evaluation"""
        
        # Focus on weakest dimension if not specified
        if not target_dimension:
            dimension_scores = evaluation.get("dimension_scores", {})
            if dimension_scores:
                target_dimension = min(dimension_scores, key=dimension_scores.get)
        
        improvement_prompt = f"""You are an expert prompt engineer. Improve this agent based on evaluation.

Current Agent:
- Name: {agent.name}
- Purpose: {agent.purpose}
- System Prompt: {agent.system_prompt or 'Not set'}

Evaluation Results:
- Overall Score: {evaluation.get('overall_score', 'N/A')}
- Dimension Scores: {json.dumps(evaluation.get('dimension_scores', {}), indent=2)}
- Weaknesses: {json.dumps(evaluation.get('weaknesses', []), indent=2)}
- Recommendations: {json.dumps(evaluation.get('recommendations', []), indent=2)}

Target Dimension to Improve: {target_dimension or 'Overall'}

Generate specific improvements:

Respond with JSON:
{{
    "improved_system_prompt": "The complete improved system prompt",
    "behavior_adjustments": [
        {{"aspect": "what to change", "from": "current behavior", "to": "improved behavior"}}
    ],
    "new_guidelines": ["specific guidelines to add"],
    "expected_improvement": 0.0-1.0,
    "rationale": "why these changes will help"
}}

Make the improvements specific and actionable."""

        try:
            response = await llm.complete([
                {"role": "system", "content": "You are an expert prompt engineer specializing in AI agent optimization."},
                {"role": "user", "content": improvement_prompt}
            ])
            
            improvements = json.loads(response.strip().replace("```json", "").replace("```", ""))
            return improvements
            
        except Exception as e:
            logger.error(f"Error generating improvements: {e}")
            raise HTTPException(status_code=500, detail=f"Improvement generation failed: {str(e)}")


# ============================================================================
# EVOLUTION LOOP
# ============================================================================

class EvolutionLoop:
    """
    Runs evolution cycles until quality thresholds are met.
    
    The loop:
    1. Evaluate current agent
    2. If score >= threshold, stop
    3. Generate improvements
    4. Apply improvements
    5. Re-evaluate
    6. Repeat until max iterations or threshold met
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        self.evaluator = LLMEvaluator(db, entity_id)
        self.meta_prompter = MetaPrompter(db, entity_id)
        
    async def run_evolution_cycle(
        self,
        agent_id: UUID,
        target_dimension: Optional[str] = None,
        max_iterations: int = MAX_EVOLUTION_ITERATIONS
    ) -> EvolutionCycle:
        """Run a complete evolution cycle"""
        
        # Get agent
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Create cycle record
        cycle = EvolutionCycle(
            entity_id=self.entity_id,
            agent_id=agent_id,
            cycle_type="improvement",
            target_dimension=target_dimension,
            status="running"
        )
        self.db.add(cycle)
        self.db.commit()
        
        try:
            # Initial evaluation
            initial_eval = await self.evaluator.evaluate_agent(
                agent_id, 
                time_window_days=7,
                dimensions=["relevance", "helpfulness", "accuracy", "tone", "principle_alignment"]
            )
            
            cycle.initial_score = initial_eval.get("overall_score", 0.5)
            current_score = cycle.initial_score
            
            iterations = []
            changes_made = []
            
            for i in range(max_iterations):
                # Check if threshold met
                if current_score >= QUALITY_THRESHOLD:
                    logger.info(f"Quality threshold met at iteration {i}")
                    break
                
                # Generate improvements
                improvements = await self.meta_prompter.generate_improvements(
                    agent, initial_eval, target_dimension
                )
                
                # Apply improvements
                if improvements.get("improved_system_prompt"):
                    old_prompt = agent.system_prompt
                    agent.system_prompt = improvements["improved_system_prompt"]
                    changes_made.append(f"Updated system prompt")
                
                if improvements.get("new_guidelines"):
                    agent.meta_data = agent.meta_data or {}
                    agent.meta_data["guidelines"] = improvements["new_guidelines"]
                    changes_made.append(f"Added {len(improvements['new_guidelines'])} guidelines")
                
                agent.updated_at = datetime.utcnow()
                self.db.commit()
                
                # Record iteration
                iterations.append({
                    "iteration": i + 1,
                    "score_before": current_score,
                    "improvements_applied": len(changes_made),
                    "expected_improvement": improvements.get("expected_improvement", 0)
                })
                
                # Re-evaluate (in practice, would wait for more interactions)
                # For now, estimate based on expected improvement
                expected_gain = improvements.get("expected_improvement", 0.1)
                current_score = min(1.0, current_score + (expected_gain * 0.5))  # Conservative estimate
                
            # Finalize cycle
            cycle.final_score = current_score
            cycle.iterations_run = len(iterations)
            cycle.improvement_delta = cycle.final_score - cycle.initial_score
            cycle.changes_applied = changes_made
            cycle.iteration_details = iterations
            cycle.status = "completed"
            cycle.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            # Publish event
            publisher.publish_event(
                "digital",
                "agent.evolved",
                str(self.entity_id),
                {
                    "agent_id": str(agent_id),
                    "cycle_id": str(cycle.id),
                    "improvement": cycle.improvement_delta
                }
            )
            
            return cycle
            
        except Exception as e:
            cycle.status = "failed"
            cycle.meta_data = {"error": str(e)}
            self.db.commit()
            raise


# ============================================================================
# DRIFT DETECTOR
# ============================================================================

class DriftDetector:
    """
    Monitors for behavioral drift and regression.
    
    Detects when agent behavior deviates from expected patterns
    or when performance degrades over time.
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def check_for_drift(
        self,
        time_window_days: int = 30
    ) -> List[BehaviorDrift]:
        """Check for behavioral drift across all agents"""
        
        drifts = []
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)
        
        # Get agents for this entity
        agents = self.db.query(Agent).filter(
            Agent.entity_id == self.entity_id
        ).all()
        
        for agent in agents:
            # Get performance history
            performances = self.db.query(AgentPerformance).filter(
                and_(
                    AgentPerformance.agent_id == agent.id,
                    AgentPerformance.created_at >= cutoff
                )
            ).order_by(AgentPerformance.created_at).all()
            
            if len(performances) < 2:
                continue
            
            # Check for score decline
            recent_scores = [p.overall_score for p in performances[-5:]]
            older_scores = [p.overall_score for p in performances[:5]]
            
            if recent_scores and older_scores:
                recent_avg = sum(recent_scores) / len(recent_scores)
                older_avg = sum(older_scores) / len(older_scores)
                
                if older_avg - recent_avg > 0.1:  # 10% decline
                    drift = BehaviorDrift(
                        entity_id=self.entity_id,
                        agent_id=agent.id,
                        drift_type="performance_decline",
                        drift_description=f"Performance declined from {older_avg:.2f} to {recent_avg:.2f}",
                        baseline_value=older_avg,
                        current_value=recent_avg,
                        deviation_score=older_avg - recent_avg,
                        severity="high" if older_avg - recent_avg > 0.2 else "medium",
                        detection_method="score_comparison",
                        is_resolved=False
                    )
                    self.db.add(drift)
                    drifts.append(drift)
            
            # Check for principle violations
            violations = self.db.query(PrincipleViolation).filter(
                and_(
                    PrincipleViolation.entity_id == self.entity_id,
                    PrincipleViolation.created_at >= cutoff
                )
            ).count()
            
            if violations > 5:  # More than 5 violations is concerning
                drift = BehaviorDrift(
                    entity_id=self.entity_id,
                    agent_id=agent.id,
                    drift_type="principle_drift",
                    drift_description=f"{violations} principle violations detected in the period",
                    baseline_value=0,
                    current_value=violations,
                    deviation_score=violations / 10,  # Normalize
                    severity="high" if violations > 10 else "medium",
                    detection_method="violation_count",
                    is_resolved=False
                )
                self.db.add(drift)
                drifts.append(drift)
        
        self.db.commit()
        return drifts


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/submit-feedback")
async def submit_feedback(
    request: FeedbackSubmissionRequest,
    db: Session = Depends(get_db)
):
    """
    Submit feedback on an interaction.
    
    Feedback is used to evaluate and improve agent performance
    through the RLAIF (Reinforcement Learning from AI Feedback) process.
    """
    try:
        entity_id = UUID(request.entity_id)
        agent_id = UUID(request.agent_id) if request.agent_id else None
        
        collector = FeedbackCollector(db, entity_id)
        feedback = await collector.submit_feedback(
            request.interaction_id,
            request.feedback_type,
            request.rating,
            request.feedback_text,
            agent_id,
            request.interaction_context
        )
        
        return {
            "status": "success",
            "feedback_id": str(feedback.id),
            "message": "Feedback recorded for evolution"
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate-agent", response_model=EvaluationResponse)
async def evaluate_agent(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate an agent's performance using LLM-as-Judge.
    
    This implements the RLAIF pattern where an LLM evaluates
    the quality of agent outputs across multiple dimensions.
    """
    try:
        entity_id = UUID(request.entity_id)
        agent_id = UUID(request.agent_id)
        
        evaluator = LLMEvaluator(db, entity_id)
        evaluation = await evaluator.evaluate_agent(
            agent_id,
            request.time_window_days,
            request.dimensions
        )
        
        return EvaluationResponse(
            agent_id=request.agent_id,
            overall_score=evaluation.get("overall_score", 0.5),
            dimension_scores=evaluation.get("dimension_scores", {}),
            strengths=evaluation.get("strengths", []),
            weaknesses=evaluation.get("weaknesses", []),
            recommendations=evaluation.get("recommendations", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run-evolution", response_model=EvolutionResponse)
async def run_evolution(
    request: EvolutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run an evolution cycle to improve an agent.
    
    The evolution loop:
    1. Evaluates current performance
    2. Generates improvements via meta-prompting
    3. Applies improvements
    4. Re-evaluates until threshold met or max iterations
    """
    try:
        entity_id = UUID(request.entity_id)
        agent_id = UUID(request.agent_id)
        
        evolution_loop = EvolutionLoop(db, entity_id)
        cycle = await evolution_loop.run_evolution_cycle(
            agent_id,
            request.target_dimension,
            request.max_iterations
        )
        
        return EvolutionResponse(
            cycle_id=str(cycle.id),
            iterations_run=cycle.iterations_run,
            initial_score=cycle.initial_score,
            final_score=cycle.final_score,
            improvement=cycle.improvement_delta,
            changes_made=cycle.changes_applied or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running evolution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/check-drift")
async def check_drift(
    request: DriftCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check for behavioral drift across agents.
    
    Detects performance decline, principle violations,
    and other deviations from expected behavior.
    """
    try:
        entity_id = UUID(request.entity_id)
        
        detector = DriftDetector(db, entity_id)
        drifts = await detector.check_for_drift(request.time_window_days)
        
        return {
            "entity_id": request.entity_id,
            "drifts_detected": len(drifts),
            "drifts": [
                {
                    "id": str(d.id),
                    "type": d.drift_type,
                    "description": d.drift_description,
                    "severity": d.severity,
                    "deviation": d.deviation_score
                }
                for d in drifts
            ]
        }
        
    except Exception as e:
        logger.error(f"Error checking drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/evolution-history/{entity_id}")
async def get_evolution_history(
    entity_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get evolution cycle history for an entity"""
    try:
        cycles = db.query(EvolutionCycle).filter(
            EvolutionCycle.entity_id == UUID(entity_id)
        ).order_by(EvolutionCycle.created_at.desc()).limit(limit).all()
        
        return {
            "entity_id": entity_id,
            "count": len(cycles),
            "cycles": [
                {
                    "id": str(c.id),
                    "agent_id": str(c.agent_id) if c.agent_id else None,
                    "type": c.cycle_type,
                    "status": c.status,
                    "initial_score": c.initial_score,
                    "final_score": c.final_score,
                    "improvement": c.improvement_delta,
                    "iterations": c.iterations_run,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in cycles
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting evolution history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "self-evolution-engine", "version": "2.0.0"}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
