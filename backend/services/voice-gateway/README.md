# NUCLEUS Voice Gateway

Real-time voice interface for NUCLEUS using xAI Grok Voice Agent API.

## Overview

The Voice Gateway enables natural voice conversations with NUCLEUS in Hebrew (and other languages). It provides a seamless experience where voice and text interactions share the same brain, memory, and learning.

### Key Features

- **Real-time Voice Conversations**: Low-latency (<1 second) voice interactions
- **Hebrew Language Support**: Native Hebrew understanding and speech
- **Unified Experience**: Same brain, same memory as text chat
- **Tool Calling**: Access to calendar, email, memory, and other NUCLEUS capabilities
- **4 Options Protocol**: Intelligent decision-making with user control

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Web/Mobile)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket (Audio + Text)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Voice Gateway Service                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Session   │  │    xAI      │  │      NUCLEUS            │  │
│  │   Manager   │  │   Bridge    │  │    Integration          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                  │                      │
         │                  │                      │
         ▼                  ▼                      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐
│   Memory    │    │    xAI      │    │   DNA Engine            │
│   Engine    │    │   Grok API  │    │   Orchestrator          │
└─────────────┘    └─────────────┘    └─────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- xAI API Key (from [console.x.ai](https://console.x.ai))
- Running NUCLEUS services (Memory Engine, DNA Engine, Orchestrator)

### Installation

```bash
cd backend/services/voice-gateway
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Required environment variables:

```env
XAI_API_KEY=your-xai-api-key-here
```

### Running

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8090
```

## API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/session` | Create session token |
| GET | `/session/{entity_id}` | Get session status |
| DELETE | `/session/{entity_id}` | End session |
| GET | `/stats` | Gateway statistics |
| GET | `/voices` | List available voices |

### WebSocket Protocol

Connect to `/ws/{entity_id}` for voice conversations.

#### Client → Server Messages

```json
// Audio data (base64 encoded PCM)
{"type": "audio", "data": "<base64>"}

// Text message (hybrid mode)
{"type": "text", "content": "שלום, מה שלומך?"}

// Control commands
{"type": "control", "action": "interrupt"}
{"type": "control", "action": "end_session"}
```

#### Server → Client Messages

```json
// Audio response (base64 encoded PCM)
{"type": "audio", "data": "<base64>"}

// Transcript
{"type": "transcript", "role": "user", "content": "..."}
{"type": "transcript", "role": "assistant", "content": "..."}

// Status updates
{"type": "status", "state": "listening"}
{"type": "status", "state": "thinking"}
{"type": "status", "state": "speaking"}

// Tool execution
{"type": "tool_call", "name": "get_calendar_events", "status": "executing"}
{"type": "tool_call", "name": "get_calendar_events", "status": "completed", "result": "..."}
```

## Available Voices

| Voice | Description | Recommended |
|-------|-------------|-------------|
| **Sal** | Neutral, Smooth, balanced | ✅ Yes |
| Ara | Warm, Expressive | |
| Eve | Clear, Professional | |
| Rex | Deep, Authoritative | |
| Leo | Energetic, Dynamic | |

## Available Tools

The Voice Gateway can execute the following NUCLEUS tools:

| Tool | Description |
|------|-------------|
| `get_calendar_events` | Get upcoming calendar events |
| `create_calendar_event` | Create a new calendar event |
| `get_recent_emails` | Get recent emails |
| `send_email` | Send an email |
| `get_memory_context` | Search user's memory |
| `create_task` | Create a new task |
| `get_contacts` | Search contacts |
| `get_user_preferences` | Get user preferences |
| `web_search` | Search the web (xAI built-in) |
| `x_search` | Search X/Twitter (xAI built-in) |

## Hebrew Language Support

The Voice Gateway is optimized for Hebrew conversations:

```python
HEBREW_INSTRUCTION = """
דבר בעברית באופן טבעי ושוטף.
השתמש בשפה יומיומית ונעימה.
היה קשוב לניואנסים תרבותיים ישראליים.
"""
```

### 4 Options Protocol (Hebrew)

```
1. אוטונומיה מלאה: "אני אעשה את זה עכשיו"
2. המלצה עם אישור: "אני ממליץ לעשות X, מאשר?"
3. בחירה: "הנה האפשרויות: A, B, C - מה אתה מעדיף?"
4. בקשת הבהרה: "אני צריך יותר מידע לפני שאוכל לעזור"
```

## Docker Deployment

```bash
docker build -t nucleus-voice-gateway .
docker run -p 8090:8090 -e XAI_API_KEY=your-key nucleus-voice-gateway
```

## Cost Estimation

xAI Grok Voice Agent API pricing: **$0.05 per minute**

| Usage | Monthly Cost |
|-------|--------------|
| 10 min/day | ~$15 |
| 30 min/day | ~$45 |
| 1 hour/day | ~$90 |

## Troubleshooting

### Common Issues

1. **Connection refused to xAI**
   - Check your API key is valid
   - Verify network connectivity

2. **Hebrew not working**
   - Ensure the voice supports Hebrew (Sal recommended)
   - Check the instructions include Hebrew directive

3. **High latency**
   - Check network connection
   - Consider using a closer region

### Logs

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

## Contributing

This service follows NUCLEUS coding standards:
- Type hints for all functions
- Comprehensive docstrings
- Async/await patterns
- Pydantic models for data validation

## License

Proprietary - NUCLEUS Project
