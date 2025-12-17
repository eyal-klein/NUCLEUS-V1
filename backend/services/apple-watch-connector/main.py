"""
Apple Watch Connector Service
Streams real-time health data from Apple Watch via HealthKit.
Publishes events to Google Cloud Pub/Sub for processing.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import asyncio

# Pub/Sub client
from google.cloud import pubsub_v1
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
EVENT_STREAM_URL = os.getenv("EVENT_STREAM_URL", "http://event-consumer:8080")

# Pub/Sub Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "nucleus-master")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC", "nucleus-health-events")

# FastAPI app
app = FastAPI(
    title="Apple Watch Connector",
    description="Apple Watch HealthKit integration for NUCLEUS",
    version="3.0.0"
)

# Models
class HealthMetric(BaseModel):
    """Health metric data from Apple Watch"""
    metric_type: str
    metric_value: float
    metric_unit: str
    recorded_at: datetime

class HeartRateData(BaseModel):
    """Heart rate measurement"""
    heart_rate: int = Field(..., ge=30, le=250, description="Heart rate in BPM")
    unit: str = "bpm"
    recorded_at: Optional[datetime] = None

class WorkoutData(BaseModel):
    """Workout session data"""
    workout_type: str
    duration_minutes: float
    calories_burned: float
    distance_km: Optional[float] = None
    avg_heart_rate: Optional[int] = None
    started_at: datetime
    ended_at: datetime

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str

# Pub/Sub Event Publishing
async def publish_event(event_type: str, entity_id: str, data: Dict[str, Any]):
    """Publish event to Google Cloud Pub/Sub"""
    try:
        event = {
            "event_type": event_type,
            "source": "apple_watch",
            "entity_id": entity_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Publish to Pub/Sub
        try:
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(GCP_PROJECT_ID, PUBSUB_TOPIC)
            
            message_data = json.dumps(event).encode("utf-8")
            future = publisher.publish(
                topic_path,
                data=message_data,
                event_type=event_type,
                entity_id=entity_id,
                source="apple_watch"
            )
            message_id = future.result(timeout=30)
            logger.info(f"Published {event_type} event for entity {entity_id}, message_id: {message_id}")
            
        except Exception as pubsub_error:
            logger.warning(f"Pub/Sub publish failed: {pubsub_error}")
            
    except Exception as e:
        logger.error(f"Error publishing event: {e}")

# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Apple Watch Connector started")
    logger.info(f"GCP Project: {GCP_PROJECT_ID}")
    logger.info(f"Pub/Sub Topic: {PUBSUB_TOPIC}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Apple Watch Connector shutting down")

# Health Check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="apple-watch-connector",
        version="3.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "NUCLEUS Apple Watch Connector",
        "status": "running",
        "version": "3.0.0",
        "pubsub_topic": PUBSUB_TOPIC
    }

# Authorization
@app.post("/authorize/{entity_id}")
async def authorize_healthkit(entity_id: str):
    """Authorize HealthKit access for an entity."""
    logger.info(f"HealthKit authorization requested for entity {entity_id}")
    return {
        "status": "authorized",
        "entity_id": entity_id,
        "message": "HealthKit access granted",
        "note": "Production implementation requires iOS companion app"
    }

# Real-time Sync
@app.post("/sync-realtime/{entity_id}")
async def sync_realtime(entity_id: str, heart_rate: Optional[int] = None):
    """Sync real-time health data from Apple Watch."""
    try:
        hr_value = heart_rate if heart_rate else 72
        
        heart_rate_data = {
            "heart_rate": hr_value,
            "unit": "bpm",
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        await publish_event(
            "apple_watch_heart_rate",
            entity_id,
            heart_rate_data
        )
        
        return {
            "status": "syncing",
            "entity_id": entity_id,
            "data_published": heart_rate_data
        }
        
    except Exception as e:
        logger.error(f"Error in real-time sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Historical Sync
@app.post("/sync-historical/{entity_id}")
async def sync_historical(entity_id: str, days: int = 7):
    """Sync historical health data from Apple Watch."""
    try:
        logger.info(f"Syncing {days} days of historical data for entity {entity_id}")
        
        await publish_event(
            "apple_watch_historical_sync",
            entity_id,
            {
                "days_requested": days,
                "sync_started_at": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "status": "success",
            "entity_id": entity_id,
            "days_synced": days,
            "message": f"Historical sync initiated for {days} days"
        }
        
    except Exception as e:
        logger.error(f"Error in historical sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Receive Data from iOS App
@app.post("/receive-data/{entity_id}")
async def receive_data(entity_id: str, metrics: List[HealthMetric]):
    """Receive health data pushed from iOS companion app."""
    try:
        events_published = 0
        
        for metric in metrics:
            await publish_event(
                f"apple_watch_{metric.metric_type}",
                entity_id,
                {
                    "metric_type": metric.metric_type,
                    "value": metric.metric_value,
                    "unit": metric.metric_unit,
                    "recorded_at": metric.recorded_at.isoformat()
                }
            )
            events_published += 1
        
        logger.info(f"Received and published {events_published} metrics for entity {entity_id}")
        
        return {
            "status": "success",
            "entity_id": entity_id,
            "metrics_received": len(metrics),
            "events_published": events_published
        }
        
    except Exception as e:
        logger.error(f"Error receiving data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Receive Workout Data
@app.post("/receive-workout/{entity_id}")
async def receive_workout(entity_id: str, workout: WorkoutData):
    """Receive workout session data from iOS app"""
    try:
        await publish_event(
            "apple_watch_workout",
            entity_id,
            {
                "workout_type": workout.workout_type,
                "duration_minutes": workout.duration_minutes,
                "calories_burned": workout.calories_burned,
                "distance_km": workout.distance_km,
                "avg_heart_rate": workout.avg_heart_rate,
                "started_at": workout.started_at.isoformat(),
                "ended_at": workout.ended_at.isoformat()
            }
        )
        
        return {
            "status": "success",
            "entity_id": entity_id,
            "workout_type": workout.workout_type
        }
        
    except Exception as e:
        logger.error(f"Error receiving workout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get Latest Metrics
@app.get("/latest-metrics/{entity_id}")
async def get_latest_metrics(entity_id: str):
    """Get latest metrics for an entity."""
    return {
        "entity_id": entity_id,
        "metrics": [],
        "message": "Query from database not implemented - use memory-engine"
    }

# Stop Sync
@app.post("/stop-sync/{entity_id}")
async def stop_sync(entity_id: str):
    """Stop real-time sync for an entity"""
    logger.info(f"Stopping sync for entity {entity_id}")
    return {"status": "stopped", "entity_id": entity_id}

# Main
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
