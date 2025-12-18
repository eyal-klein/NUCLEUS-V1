"""
NUCLEUS V2.0 - Interest Discovery Engine

This engine discovers the entity's authentic interests by:
1. Collecting signals from all data sources (email, calendar, LinkedIn, health)
2. Analyzing patterns using LLM to identify potential interests
3. Scoring candidates based on consistency, depth, and recency
4. Validating interests through user confirmation or behavioral evidence
5. Promoting validated interests to the DNA schema

Based on:
- GI X Document: "זיהוי אינטרסים" - discovering what truly matters
- NUCLEUS Agent Document: "אינטרסים אותנטיים" - authentic vs assumed interests
- Best Practice: Never act on interests that haven't been validated
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import json
from collections import Counter

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field

# Shared imports
import sys
sys.path.insert(0, '/app/shared')

from models.base import get_db
from models.dna import Entity, Interest
from models.memory import EmailMessage, CalendarEvent, HealthMetric
from models.nucleus_core import (
    InterestSignal, InterestCandidate, 
    ProactiveInitiative, BehaviorLog
)
from llm.gateway import get_llm_gateway
from pubsub.publisher import get_publisher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Interest Discovery Engine",
    description="Discovers and validates authentic entity interests",
    version="2.0.0"
)

# Initialize LLM Gateway
llm = get_llm_gateway()

# Initialize Pub/Sub Publisher
publisher = get_publisher()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SignalCollectionRequest(BaseModel):
    """Request to collect signals from data sources"""
    entity_id: str
    sources: List[str] = Field(
        default=["email", "calendar", "linkedin", "health"],
        description="Data sources to analyze"
    )
    time_window_days: int = Field(default=30, description="Days of data to analyze")


class SignalCollectionResponse(BaseModel):
    """Response with collected signals"""
    entity_id: str
    signals_collected: int
    sources_analyzed: List[str]


class InterestAnalysisRequest(BaseModel):
    """Request to analyze signals and discover interests"""
    entity_id: str
    min_signal_count: int = Field(default=3, description="Minimum signals to consider an interest")
    min_confidence: float = Field(default=0.5, description="Minimum confidence score")


class InterestCandidateResponse(BaseModel):
    """Response with discovered interest candidates"""
    entity_id: str
    candidates_discovered: int
    candidates: List[Dict[str, Any]]


class InterestValidationRequest(BaseModel):
    """Request to validate an interest candidate"""
    candidate_id: str
    validation_method: str = Field(
        default="user_confirmed",
        description="How the interest was validated: user_confirmed, user_rejected, auto"
    )
    feedback: Optional[str] = None


# ============================================================================
# SIGNAL COLLECTOR
# ============================================================================

class SignalCollector:
    """
    Collects signals from various data sources that indicate interests.
    
    Signal Types:
    - topic_mention: Topic mentioned in communication
    - time_spent: Time allocated to an activity
    - engagement: Active engagement with content
    - search: Search queries or lookups
    - action: Actions taken related to a topic
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def collect_all_signals(
        self, 
        sources: List[str], 
        time_window_days: int
    ) -> List[InterestSignal]:
        """Collect signals from all specified sources"""
        signals = []
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        
        if "email" in sources:
            signals.extend(await self._collect_email_signals(cutoff_date))
        if "calendar" in sources:
            signals.extend(await self._collect_calendar_signals(cutoff_date))
        if "health" in sources:
            signals.extend(await self._collect_health_signals(cutoff_date))
        if "linkedin" in sources:
            signals.extend(await self._collect_linkedin_signals(cutoff_date))
            
        return signals
    
    async def _collect_email_signals(self, cutoff_date: datetime) -> List[InterestSignal]:
        """Extract interest signals from emails"""
        signals = []
        
        # Get recent emails
        emails = self.db.query(EmailMessage).filter(
            and_(
                EmailMessage.entity_id == self.entity_id,
                EmailMessage.received_at >= cutoff_date
            )
        ).limit(100).all()
        
        if not emails:
            return signals
        
        # Batch analyze emails for topics
        email_texts = [
            f"Subject: {e.subject or 'No subject'}\nSnippet: {e.snippet or ''}"
            for e in emails[:50]  # Limit for API
        ]
        
        analysis_prompt = f"""Analyze these email subjects and snippets to extract topics of interest.

Emails:
{chr(10).join(email_texts)}

Extract topics that appear to be genuine interests (not just routine work).
Focus on:
- Recurring themes
- Topics with emotional engagement
- Professional development interests
- Personal interests mentioned

Respond with JSON:
{{
    "topics": [
        {{"topic": "topic name", "mentions": count, "sentiment": "positive/neutral/negative", "category": "professional/personal/health/social"}}
    ]
}}

Only include topics that appear at least twice or show strong engagement."""

        try:
            response = await llm.complete([
                {"role": "system", "content": "You are an interest analyst. Extract genuine interests from communication patterns."},
                {"role": "user", "content": analysis_prompt}
            ])
            
            analysis = json.loads(response.strip().replace("```json", "").replace("```", ""))
            
            for topic in analysis.get("topics", []):
                signal = InterestSignal(
                    entity_id=self.entity_id,
                    signal_source="email",
                    signal_type="topic_mention",
                    signal_content=f"Topic '{topic['topic']}' mentioned {topic['mentions']} times in emails",
                    extracted_topics=[topic['topic']],
                    sentiment={"positive": 0.8, "neutral": 0.5, "negative": 0.2}.get(topic.get('sentiment', 'neutral'), 0.5),
                    engagement_level=min(topic['mentions'] / 10, 1.0),
                    source_timestamp=datetime.utcnow(),
                    meta_data={
                        "category": topic.get('category'),
                        "mentions": topic['mentions']
                    }
                )
                self.db.add(signal)
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error analyzing emails: {e}")
        
        self.db.commit()
        return signals
    
    async def _collect_calendar_signals(self, cutoff_date: datetime) -> List[InterestSignal]:
        """Extract interest signals from calendar events"""
        signals = []
        
        # Get calendar events
        events = self.db.query(CalendarEvent).filter(
            and_(
                CalendarEvent.entity_id == self.entity_id,
                CalendarEvent.start_time >= cutoff_date
            )
        ).all()
        
        if not events:
            return signals
        
        # Analyze time allocation patterns
        event_categories = Counter()
        total_time = timedelta()
        
        for event in events:
            if event.end_time and event.start_time:
                duration = event.end_time - event.start_time
                total_time += duration
                
                # Categorize event
                title_lower = (event.title or "").lower()
                if any(word in title_lower for word in ["meeting", "call", "sync"]):
                    event_categories["meetings"] += duration.total_seconds()
                elif any(word in title_lower for word in ["workout", "gym", "run", "yoga"]):
                    event_categories["fitness"] += duration.total_seconds()
                elif any(word in title_lower for word in ["learn", "course", "study", "training"]):
                    event_categories["learning"] += duration.total_seconds()
                elif any(word in title_lower for word in ["family", "friend", "dinner", "lunch"]):
                    event_categories["social"] += duration.total_seconds()
                else:
                    event_categories["other"] += duration.total_seconds()
        
        # Create signals for significant time allocations
        total_seconds = total_time.total_seconds() or 1
        for category, seconds in event_categories.items():
            percentage = seconds / total_seconds
            if percentage > 0.1:  # More than 10% of time
                signal = InterestSignal(
                    entity_id=self.entity_id,
                    signal_source="calendar",
                    signal_type="time_spent",
                    signal_content=f"Spends {percentage*100:.1f}% of scheduled time on {category}",
                    extracted_topics=[category],
                    engagement_level=min(percentage * 2, 1.0),
                    source_timestamp=datetime.utcnow(),
                    meta_data={
                        "hours": seconds / 3600,
                        "percentage": percentage
                    }
                )
                self.db.add(signal)
                signals.append(signal)
        
        self.db.commit()
        return signals
    
    async def _collect_health_signals(self, cutoff_date: datetime) -> List[InterestSignal]:
        """Extract interest signals from health tracking behavior"""
        signals = []
        
        # Get health metrics
        metrics = self.db.query(HealthMetric).filter(
            and_(
                HealthMetric.entity_id == self.entity_id,
                HealthMetric.recorded_at >= cutoff_date
            )
        ).all()
        
        if not metrics:
            return signals
        
        # Analyze which metrics are being tracked
        metric_types = Counter(m.metric_type for m in metrics)
        
        # Consistent tracking indicates interest in health
        for metric_type, count in metric_types.items():
            if count >= 7:  # At least weekly tracking
                signal = InterestSignal(
                    entity_id=self.entity_id,
                    signal_source="health",
                    signal_type="engagement",
                    signal_content=f"Consistently tracks {metric_type} ({count} recordings)",
                    extracted_topics=[f"health_{metric_type}", "wellness"],
                    engagement_level=min(count / 30, 1.0),
                    source_timestamp=datetime.utcnow(),
                    meta_data={
                        "metric_type": metric_type,
                        "recording_count": count
                    }
                )
                self.db.add(signal)
                signals.append(signal)
        
        self.db.commit()
        return signals
    
    async def _collect_linkedin_signals(self, cutoff_date: datetime) -> List[InterestSignal]:
        """Extract interest signals from LinkedIn activity"""
        # This would integrate with LinkedIn data when available
        # For now, returning empty - will be enhanced with linkedin-connector data
        return []


# ============================================================================
# INTEREST ANALYZER
# ============================================================================

class InterestAnalyzer:
    """
    Analyzes collected signals to discover and score interest candidates.
    
    Scoring Factors:
    - Signal count: How many signals support this interest
    - Consistency: Does it appear across time periods
    - Depth: Level of engagement (time, actions, emotions)
    - Recency: More recent signals weighted higher
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def analyze_and_discover(
        self,
        min_signal_count: int = 3,
        min_confidence: float = 0.5
    ) -> List[InterestCandidate]:
        """Analyze signals and discover interest candidates"""
        
        # Get unprocessed signals
        signals = self.db.query(InterestSignal).filter(
            and_(
                InterestSignal.entity_id == self.entity_id,
                InterestSignal.is_processed == False
            )
        ).all()
        
        if not signals:
            return []
        
        # Group signals by topic
        topic_signals: Dict[str, List[InterestSignal]] = {}
        for signal in signals:
            for topic in signal.extracted_topics or []:
                topic_lower = topic.lower().strip()
                if topic_lower not in topic_signals:
                    topic_signals[topic_lower] = []
                topic_signals[topic_lower].append(signal)
        
        # Analyze each topic cluster
        candidates = []
        for topic, topic_signal_list in topic_signals.items():
            if len(topic_signal_list) < min_signal_count:
                continue
            
            # Calculate scores
            scores = self._calculate_scores(topic, topic_signal_list)
            
            if scores['confidence'] < min_confidence:
                continue
            
            # Check if candidate already exists
            existing = self.db.query(InterestCandidate).filter(
                and_(
                    InterestCandidate.entity_id == self.entity_id,
                    InterestCandidate.interest_name == topic
                )
            ).first()
            
            if existing:
                # Update existing candidate
                existing.signal_count = len(topic_signal_list)
                existing.confidence_score = scores['confidence']
                existing.consistency_score = scores['consistency']
                existing.depth_score = scores['depth']
                existing.last_signal_at = max(s.detected_at for s in topic_signal_list)
                existing.supporting_signals = [str(s.id) for s in topic_signal_list]
                existing.updated_at = datetime.utcnow()
                candidates.append(existing)
            else:
                # Create new candidate
                candidate = InterestCandidate(
                    entity_id=self.entity_id,
                    interest_name=topic,
                    interest_category=self._infer_category(topic, topic_signal_list),
                    interest_description=f"Interest in {topic} discovered from {len(topic_signal_list)} signals",
                    supporting_signals=[str(s.id) for s in topic_signal_list],
                    signal_count=len(topic_signal_list),
                    first_signal_at=min(s.detected_at for s in topic_signal_list),
                    last_signal_at=max(s.detected_at for s in topic_signal_list),
                    confidence_score=scores['confidence'],
                    consistency_score=scores['consistency'],
                    depth_score=scores['depth'],
                    validation_status="pending"
                )
                self.db.add(candidate)
                candidates.append(candidate)
        
        # Mark signals as processed
        for signal in signals:
            signal.is_processed = True
            signal.processed_at = datetime.utcnow()
        
        self.db.commit()
        return candidates
    
    def _calculate_scores(
        self, 
        topic: str, 
        signals: List[InterestSignal]
    ) -> Dict[str, float]:
        """Calculate confidence, consistency, and depth scores"""
        
        # Confidence: Based on signal count and diversity
        source_diversity = len(set(s.signal_source for s in signals))
        signal_count_score = min(len(signals) / 10, 1.0)
        diversity_score = source_diversity / 4  # Max 4 sources
        confidence = (signal_count_score * 0.6) + (diversity_score * 0.4)
        
        # Consistency: Based on time spread
        if len(signals) > 1:
            timestamps = [s.detected_at for s in signals if s.detected_at]
            if timestamps:
                time_spread = (max(timestamps) - min(timestamps)).days
                consistency = min(time_spread / 30, 1.0)  # Spread over 30 days = 1.0
            else:
                consistency = 0.5
        else:
            consistency = 0.3
        
        # Depth: Based on engagement levels
        engagement_levels = [s.engagement_level for s in signals if s.engagement_level]
        depth = sum(engagement_levels) / len(engagement_levels) if engagement_levels else 0.5
        
        return {
            'confidence': round(confidence, 2),
            'consistency': round(consistency, 2),
            'depth': round(depth, 2)
        }
    
    def _infer_category(
        self, 
        topic: str, 
        signals: List[InterestSignal]
    ) -> str:
        """Infer the category of an interest"""
        # Check signal metadata for categories
        categories = []
        for signal in signals:
            if signal.meta_data and 'category' in signal.meta_data:
                categories.append(signal.meta_data['category'])
        
        if categories:
            return Counter(categories).most_common(1)[0][0]
        
        # Infer from topic name
        topic_lower = topic.lower()
        if any(word in topic_lower for word in ['health', 'fitness', 'wellness', 'sleep', 'exercise']):
            return 'health'
        elif any(word in topic_lower for word in ['work', 'career', 'professional', 'business']):
            return 'professional'
        elif any(word in topic_lower for word in ['family', 'friend', 'social', 'relationship']):
            return 'social'
        elif any(word in topic_lower for word in ['learn', 'study', 'course', 'skill']):
            return 'personal_growth'
        else:
            return 'personal'


# ============================================================================
# INTEREST VALIDATOR
# ============================================================================

class InterestValidator:
    """
    Validates interest candidates before promoting to DNA.
    
    Validation Methods:
    - user_confirmed: User explicitly confirms the interest
    - user_rejected: User explicitly rejects the interest
    - auto: System validates based on continued behavioral evidence
    """
    
    def __init__(self, db: Session, entity_id: UUID):
        self.db = db
        self.entity_id = entity_id
        
    async def validate_candidate(
        self,
        candidate_id: UUID,
        validation_method: str,
        feedback: Optional[str] = None
    ) -> Tuple[InterestCandidate, Optional[Interest]]:
        """Validate an interest candidate"""
        
        candidate = self.db.query(InterestCandidate).filter(
            InterestCandidate.id == candidate_id
        ).first()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        promoted_interest = None
        
        if validation_method == "user_confirmed":
            # Promote to DNA
            promoted_interest = await self._promote_to_dna(candidate)
            candidate.validation_status = "validated"
            candidate.promoted_to_interest_id = promoted_interest.id
            
        elif validation_method == "user_rejected":
            candidate.validation_status = "rejected"
            
        elif validation_method == "auto":
            # Auto-validate if confidence is high enough
            if candidate.confidence_score >= 0.8 and candidate.consistency_score >= 0.7:
                promoted_interest = await self._promote_to_dna(candidate)
                candidate.validation_status = "validated"
                candidate.promoted_to_interest_id = promoted_interest.id
            else:
                candidate.validation_status = "pending"
        
        candidate.validated_at = datetime.utcnow()
        candidate.validation_method = validation_method
        
        if feedback:
            candidate.meta_data = candidate.meta_data or {}
            candidate.meta_data['validation_feedback'] = feedback
        
        self.db.commit()
        
        return candidate, promoted_interest
    
    async def _promote_to_dna(self, candidate: InterestCandidate) -> Interest:
        """Promote a validated candidate to the DNA schema"""
        
        # Check if interest already exists in DNA
        existing = self.db.query(Interest).filter(
            and_(
                Interest.entity_id == self.entity_id,
                Interest.interest_name == candidate.interest_name
            )
        ).first()
        
        if existing:
            # Update existing interest
            existing.interest_level = max(existing.interest_level or 0, candidate.confidence_score)
            existing.updated_at = datetime.utcnow()
            return existing
        
        # Create new interest in DNA
        interest = Interest(
            entity_id=self.entity_id,
            interest_name=candidate.interest_name,
            interest_category=candidate.interest_category,
            interest_description=candidate.interest_description,
            interest_level=candidate.confidence_score,
            first_detected_at=candidate.first_signal_at,
            evidence_count=candidate.signal_count,
            meta_data={
                "discovered_by": "interest_discovery_engine",
                "candidate_id": str(candidate.id),
                "scores": {
                    "confidence": candidate.confidence_score,
                    "consistency": candidate.consistency_score,
                    "depth": candidate.depth_score
                }
            }
        )
        self.db.add(interest)
        self.db.commit()
        
        # Publish event
        publisher.publish_event(
            "digital",
            "interest.discovered",
            str(self.entity_id),
            {
                "interest_id": str(interest.id),
                "interest_name": interest.interest_name,
                "category": interest.interest_category,
                "confidence": candidate.confidence_score
            }
        )
        
        return interest


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/collect-signals", response_model=SignalCollectionResponse)
async def collect_signals(
    request: SignalCollectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Collect interest signals from various data sources.
    
    Analyzes emails, calendar, health data, and LinkedIn to extract
    signals that indicate potential interests.
    """
    try:
        entity_id = UUID(request.entity_id)
        
        # Verify entity exists
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Collect signals
        collector = SignalCollector(db, entity_id)
        signals = await collector.collect_all_signals(
            request.sources,
            request.time_window_days
        )
        
        # Log behavior
        behavior_log = BehaviorLog(
            entity_id=entity_id,
            action_type="signal_collection",
            action_description=f"Collected {len(signals)} signals from {request.sources}",
            action_input={"sources": request.sources, "time_window": request.time_window_days},
            action_output={"signal_count": len(signals)},
            success=True,
            principle_compliance=True
        )
        db.add(behavior_log)
        db.commit()
        
        return SignalCollectionResponse(
            entity_id=request.entity_id,
            signals_collected=len(signals),
            sources_analyzed=request.sources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error collecting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-interests", response_model=InterestCandidateResponse)
async def analyze_interests(
    request: InterestAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze collected signals to discover interest candidates.
    
    Groups signals by topic, calculates confidence scores,
    and creates interest candidates for validation.
    """
    try:
        entity_id = UUID(request.entity_id)
        
        # Analyze signals
        analyzer = InterestAnalyzer(db, entity_id)
        candidates = await analyzer.analyze_and_discover(
            request.min_signal_count,
            request.min_confidence
        )
        
        return InterestCandidateResponse(
            entity_id=request.entity_id,
            candidates_discovered=len(candidates),
            candidates=[
                {
                    "id": str(c.id),
                    "name": c.interest_name,
                    "category": c.interest_category,
                    "signal_count": c.signal_count,
                    "confidence": c.confidence_score,
                    "consistency": c.consistency_score,
                    "depth": c.depth_score,
                    "status": c.validation_status
                }
                for c in candidates
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing interests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate-interest")
async def validate_interest(
    request: InterestValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate an interest candidate.
    
    If validated, the interest is promoted to the DNA schema
    and becomes part of the entity's authentic interest profile.
    """
    try:
        candidate_id = UUID(request.candidate_id)
        
        # Get candidate to find entity_id
        candidate = db.query(InterestCandidate).filter(
            InterestCandidate.id == candidate_id
        ).first()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Validate
        validator = InterestValidator(db, candidate.entity_id)
        updated_candidate, promoted_interest = await validator.validate_candidate(
            candidate_id,
            request.validation_method,
            request.feedback
        )
        
        return {
            "status": "success",
            "candidate_id": str(updated_candidate.id),
            "validation_status": updated_candidate.validation_status,
            "promoted_to_dna": promoted_interest is not None,
            "interest_id": str(promoted_interest.id) if promoted_interest else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating interest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidates/{entity_id}")
async def get_candidates(
    entity_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get interest candidates for an entity"""
    try:
        query = db.query(InterestCandidate).filter(
            InterestCandidate.entity_id == UUID(entity_id)
        )
        
        if status:
            query = query.filter(InterestCandidate.validation_status == status)
        
        candidates = query.order_by(InterestCandidate.confidence_score.desc()).all()
        
        return {
            "entity_id": entity_id,
            "count": len(candidates),
            "candidates": [
                {
                    "id": str(c.id),
                    "name": c.interest_name,
                    "category": c.interest_category,
                    "description": c.interest_description,
                    "signal_count": c.signal_count,
                    "confidence": c.confidence_score,
                    "consistency": c.consistency_score,
                    "depth": c.depth_score,
                    "status": c.validation_status,
                    "first_signal": c.first_signal_at.isoformat() if c.first_signal_at else None,
                    "last_signal": c.last_signal_at.isoformat() if c.last_signal_at else None
                }
                for c in candidates
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/validated-interests/{entity_id}")
async def get_validated_interests(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Get validated interests from DNA for an entity"""
    try:
        interests = db.query(Interest).filter(
            Interest.entity_id == UUID(entity_id)
        ).order_by(Interest.interest_level.desc()).all()
        
        return {
            "entity_id": entity_id,
            "count": len(interests),
            "interests": [
                {
                    "id": str(i.id),
                    "name": i.interest_name,
                    "category": i.interest_category,
                    "level": i.interest_level,
                    "description": i.interest_description,
                    "first_detected": i.first_detected_at.isoformat() if i.first_detected_at else None
                }
                for i in interests
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting validated interests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "interest-discovery-engine", "version": "2.0.0"}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
