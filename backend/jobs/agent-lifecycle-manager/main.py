"""
Agent Lifecycle Manager Job
Runs daily to manage agent lifecycle: shutdown weak agents, improve mediocre ones, split successful ones
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

from sqlalchemy import create_engine, select, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from openai import OpenAI

from models.assembly import Agent, AgentHealth, AgentLifecycleEvent
from models.dna import Entity

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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# OpenAI client
client = OpenAI()  # Uses OPENAI_API_KEY from environment


@dataclass
class LifecycleDecision:
    """Decision about an agent's lifecycle"""
    agent_id: str
    action: str  # 'shutdown', 'improve', 'split', 'maintain'
    reason: str
    confidence: float
    recommendations: Dict[str, Any]


class AgentLifecycleManager:
    """Manages agent lifecycle: apoptosis, evolution, mitosis"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Thresholds (configurable via env vars)
        self.shutdown_threshold = float(os.getenv("SHUTDOWN_THRESHOLD", "0.3"))
        self.improve_threshold = float(os.getenv("IMPROVE_THRESHOLD", "0.6"))
        self.split_threshold = float(os.getenv("SPLIT_THRESHOLD", "0.85"))
        
        # Risk thresholds
        self.critical_risk_action = os.getenv("CRITICAL_RISK_ACTION", "shutdown")
        
        logger.info(f"Lifecycle Manager initialized with thresholds: "
                   f"shutdown={self.shutdown_threshold}, "
                   f"improve={self.improve_threshold}, "
                   f"split={self.split_threshold}")
    
    async def run(self):
        """Main execution loop"""
        logger.info("Starting Agent Lifecycle Manager...")
        
        try:
            # 1. Get all active agents with their latest health
            agents_health = self.get_agents_with_health()
            logger.info(f"Found {len(agents_health)} active agents to analyze")
            
            if not agents_health:
                logger.info("No agents to process")
                return
            
            # 2. Analyze each agent and decide action
            decisions = []
            for agent_data in agents_health:
                decision = await self.analyze_agent(agent_data)
                if decision:
                    decisions.append(decision)
            
            logger.info(f"Made {len(decisions)} lifecycle decisions")
            
            # 3. Execute decisions
            for decision in decisions:
                await self.execute_decision(decision)
            
            # 4. Summary
            self.log_summary(decisions)
            
            logger.info("Agent Lifecycle Manager completed successfully")
            
        except Exception as e:
            logger.error(f"Error in lifecycle manager: {e}", exc_info=True)
            raise
    
    def get_agents_with_health(self) -> List[Dict[str, Any]]:
        """Get all active agents with their latest health scores"""
        
        # Query to get agents with their latest health
        query = """
        SELECT 
            a.id as agent_id,
            a.agent_name,
            a.agent_type,
            a.created_at,
            h.health_score,
            h.usage_frequency,
            h.success_rate,
            h.user_satisfaction,
            h.cost_efficiency,
            h.response_time_score,
            h.total_requests,
            h.successful_requests,
            h.failed_requests,
            h.trend,
            h.risk_level,
            h.recommendations,
            h.calculated_at
        FROM assembly.agents a
        LEFT JOIN assembly.agent_health_latest h ON a.id = h.agent_id
        WHERE a.is_active = true
        ORDER BY h.health_score ASC NULLS LAST
        """
        
        result = self.db.execute(query)
        rows = result.fetchall()
        
        agents = []
        for row in rows:
            agents.append({
                'agent_id': str(row[0]),
                'agent_name': row[1],
                'agent_type': row[2],
                'created_at': row[3],
                'health_score': row[4],
                'usage_frequency': row[5],
                'success_rate': row[6],
                'user_satisfaction': row[7],
                'cost_efficiency': row[8],
                'response_time_score': row[9],
                'total_requests': row[10],
                'successful_requests': row[11],
                'failed_requests': row[12],
                'trend': row[13],
                'risk_level': row[14],
                'recommendations': row[15],
                'calculated_at': row[16]
            })
        
        return agents
    
    async def analyze_agent(self, agent_data: Dict[str, Any]) -> Optional[LifecycleDecision]:
        """Analyze an agent and decide on lifecycle action"""
        
        agent_id = agent_data['agent_id']
        agent_name = agent_data['agent_name']
        health_score = agent_data.get('health_score')
        risk_level = agent_data.get('risk_level')
        trend = agent_data.get('trend')
        
        # If no health data, skip for now
        if health_score is None:
            logger.info(f"Agent {agent_name} has no health data yet, skipping")
            return None
        
        logger.info(f"Analyzing {agent_name}: health={health_score:.2f}, "
                   f"risk={risk_level}, trend={trend}")
        
        # Decision logic
        action = 'maintain'
        reason = ''
        confidence = 0.0
        
        # Critical risk - immediate action
        if risk_level == 'critical':
            if self.critical_risk_action == 'shutdown':
                action = 'shutdown'
                reason = f"Critical risk level with health score {health_score:.2f}"
                confidence = 0.95
            else:
                action = 'improve'
                reason = f"Critical risk level requires immediate improvement"
                confidence = 0.90
        
        # Low health - consider shutdown
        elif health_score < self.shutdown_threshold:
            action = 'shutdown'
            reason = f"Health score {health_score:.2f} below shutdown threshold {self.shutdown_threshold}"
            confidence = 0.85
        
        # High health - consider split
        elif health_score >= self.split_threshold:
            # Only split if trending well and high usage
            if trend in ['improving', 'stable'] and agent_data.get('usage_frequency', 0) > 0.7:
                action = 'split'
                reason = f"Excellent health score {health_score:.2f} with high usage"
                confidence = 0.80
            else:
                action = 'maintain'
                reason = f"High health but conditions not optimal for split"
                confidence = 0.70
        
        # Medium health - consider improvement
        elif health_score < self.improve_threshold:
            if trend == 'declining':
                action = 'improve'
                reason = f"Declining health score {health_score:.2f} needs intervention"
                confidence = 0.75
            elif risk_level in ['medium', 'high']:
                action = 'improve'
                reason = f"Medium health with {risk_level} risk level"
                confidence = 0.70
            else:
                action = 'maintain'
                reason = f"Health score {health_score:.2f} is acceptable"
                confidence = 0.65
        
        else:
            action = 'maintain'
            reason = f"Health score {health_score:.2f} is good"
            confidence = 0.80
        
        # Get LLM recommendations if action needed
        recommendations = {}
        if action != 'maintain':
            recommendations = await self.get_llm_recommendations(agent_data, action)
        
        return LifecycleDecision(
            agent_id=agent_id,
            action=action,
            reason=reason,
            confidence=confidence,
            recommendations=recommendations
        )
    
    async def get_llm_recommendations(self, agent_data: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Get LLM-powered recommendations for lifecycle action"""
        
        try:
            prompt = f"""You are an AI agent lifecycle expert. Analyze this agent and provide recommendations for the {action} action.

Agent Data:
- Name: {agent_data['agent_name']}
- Type: {agent_data['agent_type']}
- Health Score: {agent_data.get('health_score', 'N/A')}
- Usage Frequency: {agent_data.get('usage_frequency', 'N/A')}
- Success Rate: {agent_data.get('success_rate', 'N/A')}
- User Satisfaction: {agent_data.get('user_satisfaction', 'N/A')}
- Cost Efficiency: {agent_data.get('cost_efficiency', 'N/A')}
- Total Requests: {agent_data.get('total_requests', 0)}
- Failed Requests: {agent_data.get('failed_requests', 0)}
- Trend: {agent_data.get('trend', 'unknown')}
- Risk Level: {agent_data.get('risk_level', 'unknown')}

Action to take: {action.upper()}

Provide specific recommendations in JSON format:
{{
    "primary_reason": "Main reason for this action",
    "secondary_factors": ["factor1", "factor2"],
    "specific_actions": ["action1", "action2"],
    "expected_outcome": "What we expect to achieve",
    "risks": ["risk1", "risk2"],
    "alternatives": ["alternative1", "alternative2"]
}}"""

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in AI agent lifecycle management. Provide concise, actionable recommendations in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            recommendations = json.loads(content)
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting LLM recommendations: {e}")
            return {
                "primary_reason": f"Automated {action} based on health metrics",
                "specific_actions": [],
                "expected_outcome": "Improved system health",
                "risks": ["Unknown"],
                "alternatives": []
            }
    
    async def execute_decision(self, decision: LifecycleDecision):
        """Execute a lifecycle decision"""
        
        logger.info(f"Executing {decision.action} for agent {decision.agent_id}: {decision.reason}")
        
        try:
            if decision.action == 'shutdown':
                await self.shutdown_agent(decision)
            elif decision.action == 'improve':
                await self.improve_agent(decision)
            elif decision.action == 'split':
                await self.split_agent(decision)
            elif decision.action == 'maintain':
                # Just log, no action needed
                logger.info(f"Maintaining agent {decision.agent_id}")
            
            # Log lifecycle event
            self.log_lifecycle_event(decision)
            
        except Exception as e:
            logger.error(f"Error executing {decision.action} for agent {decision.agent_id}: {e}")
    
    async def shutdown_agent(self, decision: LifecycleDecision):
        """Shutdown (deactivate) an agent"""
        
        # Get agent
        agent = self.db.query(Agent).filter(Agent.id == decision.agent_id).first()
        if not agent:
            logger.error(f"Agent {decision.agent_id} not found")
            return
        
        # Deactivate
        agent.is_active = False
        agent.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Agent {agent.agent_name} shutdown successfully")
    
    async def improve_agent(self, decision: LifecycleDecision):
        """Improve an agent (placeholder for now)"""
        
        # For now, just log the improvement recommendations
        # In the future, this could trigger:
        # - Prompt optimization
        # - Parameter tuning
        # - Training data updates
        # - Model fine-tuning
        
        logger.info(f"Agent {decision.agent_id} marked for improvement")
        logger.info(f"Recommendations: {json.dumps(decision.recommendations, indent=2)}")
        
        # TODO: Implement actual improvement logic
        # This could involve:
        # 1. Analyzing failed requests
        # 2. Generating improved prompts
        # 3. Updating agent configuration
        # 4. Triggering retraining
    
    async def split_agent(self, decision: LifecycleDecision):
        """Split an agent into specialized versions (placeholder for now)"""
        
        # For now, just log the split recommendation
        # In the future, this could:
        # - Analyze agent usage patterns
        # - Identify distinct use cases
        # - Create specialized agent variants
        # - Distribute load across variants
        
        logger.info(f"Agent {decision.agent_id} marked for splitting")
        logger.info(f"Recommendations: {json.dumps(decision.recommendations, indent=2)}")
        
        # TODO: Implement actual split logic
        # This could involve:
        # 1. Analyzing request patterns
        # 2. Clustering similar requests
        # 3. Creating specialized agents
        # 4. Setting up load balancing
    
    def log_lifecycle_event(self, decision: LifecycleDecision):
        """Log a lifecycle event to the database"""
        
        try:
            event = AgentLifecycleEvent(
                agent_id=decision.agent_id,
                event_type=decision.action,
                reason=decision.reason,
                before_state=None,  # Could capture agent state before action
                after_state=None,   # Could capture agent state after action
                triggered_by='lifecycle_manager',
                triggered_by_id=None,
                metadata={
                    'confidence': decision.confidence,
                    'recommendations': decision.recommendations
                },
                occurred_at=datetime.utcnow()
            )
            
            self.db.add(event)
            self.db.commit()
            
            logger.info(f"Lifecycle event logged for agent {decision.agent_id}")
            
        except Exception as e:
            logger.error(f"Error logging lifecycle event: {e}")
            self.db.rollback()
    
    def log_summary(self, decisions: List[LifecycleDecision]):
        """Log summary of lifecycle decisions"""
        
        summary = {
            'total': len(decisions),
            'shutdown': sum(1 for d in decisions if d.action == 'shutdown'),
            'improve': sum(1 for d in decisions if d.action == 'improve'),
            'split': sum(1 for d in decisions if d.action == 'split'),
            'maintain': sum(1 for d in decisions if d.action == 'maintain')
        }
        
        logger.info("=" * 60)
        logger.info("LIFECYCLE MANAGER SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total agents analyzed: {summary['total']}")
        logger.info(f"  - Shutdown: {summary['shutdown']}")
        logger.info(f"  - Improve: {summary['improve']}")
        logger.info(f"  - Split: {summary['split']}")
        logger.info(f"  - Maintain: {summary['maintain']}")
        logger.info("=" * 60)


async def main():
    """Main entry point"""
    logger.info("Agent Lifecycle Manager Job starting...")
    
    db = SessionLocal()
    try:
        manager = AgentLifecycleManager(db)
        await manager.run()
    finally:
        db.close()
    
    logger.info("Agent Lifecycle Manager Job completed")


if __name__ == "__main__":
    asyncio.run(main())
