"""
Google Calendar Connector Service

Integrates with Google Calendar API to sync calendar events and publish them to Pub/Sub.
Provides OAuth authentication, event syncing, and webhook handling.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/callback")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "thrive-system1")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC", "nucleus-digital-events")

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

# FastAPI app
app = FastAPI(
    title="Google Calendar Connector",
    description="Syncs Google Calendar events to NUCLEUS via Pub/Sub",
    version="2.0.0"
)

# In-memory credentials store (TODO: persist to database)
credentials_store: Dict[str, Dict[str, Any]] = {}

# Pub/Sub publisher (lazy initialization)
publisher = None


def get_publisher():
    """Get or create Pub/Sub publisher"""
    global publisher
    if publisher is None:
        try:
            from google.cloud import pubsub_v1
            publisher = pubsub_v1.PublisherClient()
            logger.info("Pub/Sub publisher initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Pub/Sub publisher: {e}")
    return publisher


async def publish_to_pubsub(event_data: Dict[str, Any]) -> bool:
    """Publish event to Pub/Sub topic"""
    try:
        pub = get_publisher()
        if pub is None:
            logger.warning("Pub/Sub not available, skipping publish")
            return False
        
        topic_path = pub.topic_path(GCP_PROJECT_ID, PUBSUB_TOPIC)
        message_data = json.dumps(event_data).encode('utf-8')
        
        future = pub.publish(topic_path, message_data)
        message_id = future.result(timeout=10)
        logger.info(f"Published message {message_id} to {PUBSUB_TOPIC}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish to Pub/Sub: {e}")
        return False


# API Models
class SyncRequest(BaseModel):
    entity_id: str = Field(..., description="Entity ID to sync calendar for")
    days_past: int = Field(7, description="Number of days in the past to sync")
    days_future: int = Field(30, description="Number of days in the future to sync")


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "calendar-connector",
        "version": "2.0.0",
        "pubsub_topic": PUBSUB_TOPIC,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/auth")
async def initiate_auth(entity_id: str):
    """Initiate OAuth flow for Google Calendar"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    try:
        from google_auth_oauthlib.flow import Flow
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=entity_id,
            prompt='consent'
        )
        
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error initiating auth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/callback")
async def oauth_callback(code: str, state: str):
    """Handle OAuth callback from Google"""
    try:
        from google_auth_oauthlib.flow import Flow
        
        entity_id = state
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI]
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials
        credentials_store[entity_id] = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else SCOPES
        }
        
        return JSONResponse(content={
            "message": "Successfully authenticated with Google Calendar",
            "entity_id": entity_id,
            "status": "authenticated"
        })
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync")
async def sync_calendar(request: SyncRequest, background_tasks: BackgroundTasks):
    """Manually trigger calendar sync"""
    entity_id = request.entity_id
    
    if entity_id not in credentials_store:
        raise HTTPException(status_code=401, detail=f"No credentials found for entity {entity_id}")
    
    # Run sync in background
    background_tasks.add_task(
        sync_calendar_events,
        entity_id,
        request.days_past,
        request.days_future
    )
    
    return {
        "message": "Calendar sync initiated",
        "entity_id": entity_id,
        "status": "processing"
    }


async def sync_calendar_events(entity_id: str, days_past: int = 7, days_future: int = 30) -> List[Dict[str, Any]]:
    """Sync calendar events for entity"""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    
    token_data = credentials_store.get(entity_id)
    if not token_data:
        logger.error(f"No credentials found for entity {entity_id}")
        return []
    
    credentials = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes")
    )
    
    try:
        # Build Calendar API service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Calculate time range
        now = datetime.utcnow()
        time_min = (now - timedelta(days=days_past)).isoformat() + 'Z'
        time_max = (now + timedelta(days=days_future)).isoformat() + 'Z'
        
        # Fetch events
        logger.info(f"Fetching calendar events for entity {entity_id}")
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        logger.info(f"Found {len(events)} calendar events")
        
        # Process and publish events
        published_events = []
        for event in events:
            event_data = parse_calendar_event(event, entity_id)
            
            # Publish to Pub/Sub
            await publish_to_pubsub(event_data)
            published_events.append(event_data)
        
        return published_events
    
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        return []


def parse_calendar_event(event: Dict[str, Any], entity_id: str) -> Dict[str, Any]:
    """Parse Google Calendar event into standardized format"""
    start = event.get('start', {})
    end = event.get('end', {})
    
    # Handle all-day events
    start_time = start.get('dateTime', start.get('date'))
    end_time = end.get('dateTime', end.get('date'))
    
    # Extract attendees
    attendees = []
    for attendee in event.get('attendees', []):
        attendees.append({
            "email": attendee.get('email'),
            "response_status": attendee.get('responseStatus'),
            "organizer": attendee.get('organizer', False)
        })
    
    return {
        "event_type": "calendar_event",
        "source": "google_calendar",
        "entity_id": entity_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "event_id": event.get('id'),
            "summary": event.get('summary', 'No Title'),
            "description": event.get('description', ''),
            "location": event.get('location', ''),
            "start_time": start_time,
            "end_time": end_time,
            "timezone": start.get('timeZone', 'UTC'),
            "attendees": attendees,
            "organizer": event.get('organizer', {}).get('email'),
            "status": event.get('status', 'confirmed'),
            "html_link": event.get('htmlLink'),
            "created": event.get('created'),
            "updated": event.get('updated')
        }
    }


@app.post("/webhook")
async def handle_webhook(request: Request):
    """Handle Google Calendar webhook notifications"""
    try:
        # Get notification headers
        channel_id = request.headers.get('X-Goog-Channel-ID')
        resource_state = request.headers.get('X-Goog-Resource-State')
        resource_id = request.headers.get('X-Goog-Resource-ID')
        
        logger.info(f"Received webhook: channel={channel_id}, state={resource_state}")
        
        # Handle different resource states
        if resource_state == 'sync':
            return {"status": "acknowledged"}
        
        elif resource_state in ['exists', 'not_exists']:
            logger.info(f"Calendar changed, should trigger sync for resource {resource_id}")
            return {"status": "sync_scheduled"}
        
        return {"status": "ignored"}
    
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{entity_id}")
async def list_events(entity_id: str, days_past: int = 7, days_future: int = 30):
    """List synced calendar events for entity"""
    try:
        events = await sync_calendar_events(entity_id, days_past, days_future)
        return {
            "entity_id": entity_id,
            "event_count": len(events),
            "events": events
        }
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
