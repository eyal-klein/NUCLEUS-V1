# NUCLEUS V1.2 - Credentials Management Architecture

**Version:** 1.1  
**Date:** December 9, 2025  
**Status:** ✅ Implemented

---

## 🎯 Overview

This document defines the architecture for securely storing and managing user credentials and third-party service integrations in NUCLEUS V1.2.

### Purpose
Enable NUCLEUS to:
- Securely store user credentials for external services
- Connect to third-party APIs (Gmail, GitHub, Notion, etc.)
- Fetch data from connected services
- Learn from user's digital footprint

### Security First
- ✅ Credentials stored in GCP Secret Manager (encrypted at rest)
- ✅ Metadata stored in PostgreSQL
- ✅ No plaintext credentials in database
- ✅ Separation of concerns: metadata vs. secrets

---

## 🏗️ Architecture Components

### 1. Database Layer

#### Table: `dna.entity_integrations`

**Location:** `backend/shared/migrations/002_add_entity_integrations.sql`

```sql
CREATE TABLE dna.entity_integrations (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Entity reference
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Integration details
    service_name VARCHAR(100) NOT NULL,      -- 'gmail', 'github', 'notion', 'slack'
    service_type VARCHAR(50) NOT NULL,       -- 'email', 'code', 'docs', 'chat', 'calendar'
    display_name VARCHAR(255),               -- User-friendly name
    description TEXT,                        -- Optional description
    
    -- Credentials reference (NOT the actual credentials!)
    secret_path VARCHAR(255) NOT NULL,       -- Path in GCP Secret Manager
    credential_type VARCHAR(50) NOT NULL,    -- 'oauth2', 'api_key', 'basic_auth', 'bearer_token'
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active',     -- 'active', 'inactive', 'expired', 'error', 'revoked'
    last_sync_at TIMESTAMP WITH TIME ZONE,   -- Last successful data sync
    last_sync_status VARCHAR(50),            -- 'success', 'failed', 'partial'
    sync_error_message TEXT,                 -- Error details if sync failed
    next_sync_at TIMESTAMP WITH TIME ZONE,   -- Scheduled next sync
    
    -- OAuth-specific (if applicable)
    token_expires_at TIMESTAMP WITH TIME ZONE, -- When access token expires
    scopes JSONB,                            -- OAuth scopes granted
    
    -- Configuration
    config JSONB DEFAULT '{}',               -- Service-specific configuration
    sync_settings JSONB DEFAULT '{}',        -- Sync frequency, filters, etc.
    
    -- Metadata
    meta_data JSONB DEFAULT '{}',            -- Additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),                 -- Who created this integration
    
    -- Constraints
    UNIQUE(entity_id, service_name),         -- One integration per service per entity
    CHECK (status IN ('active', 'inactive', 'expired', 'error', 'revoked')),
    CHECK (credential_type IN ('oauth2', 'api_key', 'basic_auth', 'bearer_token'))
);
```

**Indexes:**
- `idx_entity_integrations_entity_id` - Fast lookup by entity
- `idx_entity_integrations_service_name` - Fast lookup by service
- `idx_entity_integrations_status` - Filter by status
- `idx_entity_integrations_next_sync` - Find integrations due for sync

---

### 2. Secret Manager Layer

#### GCP Secret Manager

**Secret Naming Convention:**
```
nucleus-credentials-{entity_id}-{service_name}
```

**Example:**
```
nucleus-credentials-550e8400-e29b-41d4-a716-446655440000-gmail
```

**Secret Structure (JSON):**
```json
{
  "access_token": "ya29.a0AfH6SMBx...",
  "refresh_token": "1//0gK8...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "123456789.apps.googleusercontent.com",
  "client_secret": "GOCSPX-...",
  "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
}
```

**Labels:**
- `entity_id`: Entity UUID
- `service`: Service name
- `managed_by`: "nucleus"
- `created_at`: Timestamp

---

### 3. Application Layer

#### CredentialsManager Class

**Location:** `backend/shared/utils/credentials_manager.py`

**Methods:**
- `store_credentials(entity_id, service_name, credentials)` - Store new credentials
- `retrieve_credentials(entity_id, service_name)` - Retrieve credentials
- `update_credentials(entity_id, service_name, credentials)` - Update credentials
- `delete_credentials(entity_id, service_name)` - Delete credentials
- `test_credentials(entity_id, service_name)` - Test if credentials are valid

**Usage Example:**
```python
from backend.shared.utils import CredentialsManager

creds_manager = CredentialsManager()

# Store Gmail OAuth credentials
creds_manager.store_credentials(
    entity_id="550e8400-e29b-41d4-a716-446655440000",
    service_name="gmail",
    credentials={
        "access_token": "...",
        "refresh_token": "...",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "...",
        "client_secret": "..."
    }
)

# Retrieve credentials
credentials = creds_manager.retrieve_credentials(
    entity_id="550e8400-e29b-41d4-a716-446655440000",
    service_name="gmail"
)
```

---

### 4. API Layer

#### Integrations Router

**Location:** `backend/services/orchestrator/routers/integrations.py`

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/integrations/` | Create new integration |
| GET | `/integrations/` | List all integrations (with filters) |
| GET | `/integrations/{id}` | Get specific integration |
| PATCH | `/integrations/{id}` | Update integration |
| DELETE | `/integrations/{id}` | Delete integration |
| POST | `/integrations/{id}/test` | Test integration credentials |
| POST | `/integrations/{id}/sync` | Trigger manual sync |

**Example: Create Integration**
```bash
curl -X POST http://localhost:8080/integrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "550e8400-e29b-41d4-a716-446655440000",
    "service_name": "gmail",
    "service_type": "email",
    "display_name": "Eyal Klein Gmail",
    "credential_type": "oauth2",
    "credentials": {
      "access_token": "...",
      "refresh_token": "...",
      "token_uri": "https://oauth2.googleapis.com/token",
      "client_id": "...",
      "client_secret": "..."
    },
    "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
    "token_expires_in": 3600
  }'
```

**Example: List Integrations**
```bash
curl http://localhost:8080/integrations/?entity_id=550e8400-e29b-41d4-a716-446655440000
```

---

## 🔐 Security Considerations

### 1. Encryption
- **At Rest:** GCP Secret Manager encrypts all secrets using Google-managed encryption keys
- **In Transit:** All API calls use HTTPS/TLS
- **In Memory:** Credentials loaded only when needed, not cached

### 2. Access Control
- Only the NUCLEUS service account can access Secret Manager
- Database access controlled via PostgreSQL roles
- API endpoints (future) will require authentication

### 3. Audit Trail
- All credential access logged via Cloud Logging
- Database tracks creation/update timestamps
- Sync status and errors recorded

### 4. Token Refresh
- OAuth tokens automatically refreshed before expiration
- Expired tokens marked in database
- Failed refreshes trigger alerts

---

## 📊 Data Flow

### Creating an Integration

```
User → API → Orchestrator → CredentialsManager → Secret Manager
                ↓
            Database (metadata only)
```

### Using an Integration

```
Service → CredentialsManager → Secret Manager → Credentials
    ↓
External API (Gmail, GitHub, etc.)
    ↓
Raw Data → Database (dna.raw_data)
```

---

## 🔄 Sync Process (Future)

1. **Scheduled Sync:** Cloud Scheduler triggers sync job
2. **Fetch Integrations:** Query active integrations due for sync
3. **Retrieve Credentials:** Get credentials from Secret Manager
4. **Call External API:** Fetch new data
5. **Store Data:** Save to `dna.raw_data` table
6. **Update Status:** Record sync timestamp and status
7. **Error Handling:** Log errors, update integration status

---

## 🛠️ Implementation Status

### ✅ Completed
- [x] Database schema (`entity_integrations` table)
- [x] Migration script (002_add_entity_integrations.sql)
- [x] SQLAlchemy model (`EntityIntegration`)
- [x] CredentialsManager utility class
- [x] API endpoints (full CRUD)
- [x] Integration with Orchestrator service

### 🔜 Next Steps
1. Deploy migration to production database
2. Test with real Gmail OAuth credentials
3. Implement first data sync (Gmail emails)
4. Add GitHub integration
5. Add Notion integration
6. Build automated sync scheduler

---

## 📝 Supported Services

### Planned Integrations

| Service | Type | Auth Method | Priority |
|---------|------|-------------|----------|
| Gmail | Email | OAuth 2.0 | High |
| GitHub | Code | OAuth 2.0 / PAT | High |
| Notion | Docs | OAuth 2.0 | Medium |
| Google Calendar | Calendar | OAuth 2.0 | Medium |
| Slack | Chat | OAuth 2.0 | Low |
| LinkedIn | Social | OAuth 2.0 | Low |

---

## 🧪 Testing

### Manual Testing

1. **Create Integration:**
   ```bash
   curl -X POST http://localhost:8080/integrations/ -H "Content-Type: application/json" -d @integration.json
   ```

2. **List Integrations:**
   ```bash
   curl http://localhost:8080/integrations/
   ```

3. **Test Credentials:**
   ```bash
   curl -X POST http://localhost:8080/integrations/{id}/test
   ```

### Automated Testing (Future)
- Unit tests for CredentialsManager
- Integration tests for API endpoints
- End-to-end tests with mock OAuth flow

---

## 📚 References

- [GCP Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Gmail API OAuth Guide](https://developers.google.com/gmail/api/auth/about-auth)
- [GitHub OAuth Documentation](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
- [Notion API Authentication](https://developers.notion.com/docs/authorization)

---

**Last Updated:** December 9, 2025  
**Author:** NUCLEUS Development Team  
**Version:** 1.1
