# NUCLEUS Event Stream Service

**Phase 3 - Week 1**

The central event bus for all real-time data ingestion in NUCLEUS. Uses NATS JetStream to provide durable, scalable, and decoupled event streaming.

---

## Purpose

The Event Stream service acts as the **nervous system** of NUCLEUS, receiving events from all external sources (Gmail, Calendar, IOT devices) and distributing them to internal processors (Memory Engine, Decision Engines, Agents).

**Key Benefits:**
- **Decoupling**: Connectors and processors don't need to know about each other
- **Durability**: Events are persisted for 7 days
- **Scalability**: Multiple consumers can process the same events
- **Reliability**: Guaranteed delivery with acknowledgments

---

## Architecture

```
[Gmail Connector] ─┐
[Calendar Connector] ─┤
[Oura Connector] ─┤
                  ├──> [Event Stream (NATS)] ──> [Memory Engine]
[LinkedIn Connector] ─┤                      ├──> [Decision Engines]
[Apple Health] ─┘                            └──> [Agents]
```

---

## Event Streams

### 1. **DIGITAL_EVENTS**
- **Subjects**: `digital.email.*`, `digital.calendar.*`, `digital.social.*`
- **Purpose**: Events from digital sources
- **Examples**:
  - `digital.gmail.received` - New email received
  - `digital.calendar.created` - New calendar event
  - `digital.linkedin.posted` - New LinkedIn post

### 2. **PHYSICAL_EVENTS**
- **Subjects**: `physical.sleep.*`, `physical.activity.*`, `physical.health.*`
- **Purpose**: Events from IOT devices
- **Examples**:
  - `physical.oura.sleep_completed` - Sleep session completed
  - `physical.oura.hrv_measured` - HRV measurement
  - `physical.apple_health.workout_completed` - Workout completed

### 3. **SYSTEM_EVENTS**
- **Subjects**: `system.agent.*`, `system.decision.*`, `system.action.*`
- **Purpose**: Internal NUCLEUS events
- **Examples**:
  - `system.agent.created` - New agent spawned
  - `system.decision.made` - Decision recorded
  - `system.action.approved` - Action approved by entity

---

## API Endpoints

### `POST /publish`

Publish an event to the stream.

**Request Body:**
```json
{
  "source": "gmail",
  "type": "received",
  "entity_id": "uuid",
  "payload": {
    "from": "sender@example.com",
    "subject": "Meeting tomorrow",
    "body": "Let's meet at 3pm"
  },
  "metadata": {
    "message_id": "abc123"
  }
}
```

**Response:**
```json
{
  "status": "published",
  "sequence": 12345,
  "stream": "DIGITAL_EVENTS"
}
```

### `GET /streams`

List all streams and their stats.

**Response:**
```json
[
  {
    "name": "DIGITAL_EVENTS",
    "subjects": ["digital.email.*", "digital.calendar.*"],
    "messages": 1523,
    "bytes": 2048576,
    "consumers": 2
  }
]
```

### `GET /health`

Health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "event-stream",
  "version": "3.0.0",
  "nats_connected": true
}
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NATS_URL` | NATS server URL | `nats://localhost:4222` |
| `PORT` | Service port | `8080` |

---

## Deployment

**Cloud Run:**
```bash
gcloud run deploy event-stream \
  --source . \
  --region us-central1 \
  --set-env-vars NATS_URL=nats://nats-server:4222
```

**Note**: This service requires a NATS server. For production, deploy NATS JetStream on Cloud Run or use a managed NATS service.

---

## Event Schema

All events follow this standard schema:

```json
{
  "source": "string",       // Source system (gmail, oura, etc.)
  "type": "string",         // Event type (received, completed, etc.)
  "entity_id": "uuid",      // Entity this event belongs to
  "payload": {},            // Event-specific data
  "timestamp": "ISO8601",   // When the event occurred
  "metadata": {}            // Optional metadata
}
```

---

## Monitoring

**Key Metrics:**
- Event publish rate (events/second)
- Stream size (messages, bytes)
- Consumer lag (how far behind consumers are)
- Error rate

**Logs:**
- All published events are logged with subject and sequence number
- Connection errors are logged with details

---

## Best Practices

1. **Keep payloads small**: Large payloads slow down the stream
2. **Use metadata for IDs**: Store external IDs in metadata for traceability
3. **Set timestamps**: Always include when the event occurred
4. **Handle errors**: Connectors should retry on publish failures
5. **Monitor lag**: Ensure consumers keep up with the stream

---

**Built for NUCLEUS Phase 3 - The Conscious Organism** 🧬
