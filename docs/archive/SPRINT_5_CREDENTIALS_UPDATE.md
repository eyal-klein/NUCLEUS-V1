# NUCLEUS V1.2 - Sprint 5 Update: Credentials Management

**Date:** December 9, 2025  
**Status:** ✅ Phase 1 Complete, 🔄 Phase 2 In Progress

---

## 🎯 Overview

Sprint 5 has been updated to include **Credentials Management** as the first priority. This enables NUCLEUS to connect to external services (Gmail, GitHub, Notion, etc.) and learn from the user's digital footprint.

---

## ✅ Phase 1: Credentials Infrastructure (COMPLETED)

### What Was Built

#### 1. Database Layer
**New Table:** `dna.entity_integrations`

- Stores metadata for third-party service integrations
- References credentials in GCP Secret Manager (not stored in DB)
- Tracks sync status, OAuth tokens, and configuration
- **Migration:** `backend/shared/migrations/002_add_entity_integrations.sql`

**Key Fields:**
- `service_name` - gmail, github, notion, etc.
- `secret_path` - Reference to Secret Manager
- `credential_type` - oauth2, api_key, etc.
- `status` - active, inactive, expired, error
- `last_sync_at` - Last successful sync timestamp
- `token_expires_at` - OAuth token expiration

#### 2. Application Layer
**CredentialsManager Class**

- **Location:** `backend/shared/utils/credentials_manager.py`
- **Purpose:** Securely manage credentials in GCP Secret Manager

**Methods:**
- `store_credentials()` - Store new credentials
- `retrieve_credentials()` - Retrieve credentials
- `update_credentials()` - Update existing credentials
- `delete_credentials()` - Delete credentials
- `test_credentials()` - Test if credentials are valid

#### 3. API Layer
**Integrations Router**

- **Location:** `backend/services/orchestrator/routers/integrations.py`
- **Endpoints:**
  - `POST /integrations/` - Create integration
  - `GET /integrations/` - List integrations
  - `GET /integrations/{id}` - Get specific integration
  - `PATCH /integrations/{id}` - Update integration
  - `DELETE /integrations/{id}` - Delete integration
  - `POST /integrations/{id}/test` - Test credentials
  - `POST /integrations/{id}/sync` - Trigger manual sync

#### 4. SQLAlchemy Model
**EntityIntegration Model**

- **Location:** `backend/shared/models/integrations.py`
- **Relationships:** Links to Entity model
- **Methods:** `to_dict()` for safe serialization (no credentials)

#### 5. Documentation
**Credentials Architecture Document**

- **Location:** `docs/CREDENTIALS_ARCHITECTURE.md`
- **Contents:**
  - Complete architecture overview
  - Database schema details
  - API endpoint documentation
  - Security considerations
  - Usage examples
  - Supported services roadmap

---

## 🔄 Phase 2: Deployment (IN PROGRESS)

### Next Steps

#### 1. Apply Database Migration
```bash
# Connect to Cloud SQL
gcloud sql connect nucleus-v12 --user=nucleus --database=nucleus_v12

# Run migration
\i backend/shared/migrations/002_add_entity_integrations.sql

# Verify
SELECT * FROM public.migrations WHERE version = '002';
SELECT COUNT(*) FROM dna.entity_integrations;
```

#### 2. Commit and Deploy
```bash
# Stage all changes
git add .

# Commit with descriptive message
git commit -m "feat: Add credentials management system

- Add entity_integrations table
- Implement CredentialsManager utility
- Create integrations API endpoints
- Update documentation"

# Push to trigger deployment
git push origin main
```

#### 3. Verify Deployment
```bash
# Check GitHub Actions
# https://github.com/eyal-klein/NUCLEUS-V1/actions

# Test health endpoint
curl https://nucleus-orchestrator-<hash>.run.app/health

# Test integrations endpoint
curl https://nucleus-orchestrator-<hash>.run.app/integrations/

# View API docs
open https://nucleus-orchestrator-<hash>.run.app/docs
```

---

## ⏳ Phase 3: Gmail OAuth Integration (PLANNED)

### Prerequisites
1. Set up Google Cloud OAuth consent screen
2. Create OAuth 2.0 credentials
3. Configure authorized redirect URIs

### Implementation Tasks
- [ ] Create OAuth flow helper
- [ ] Add OAuth start endpoint
- [ ] Add OAuth callback endpoint
- [ ] Test with real Gmail account
- [ ] Fetch sample emails

### OAuth Flow
```
1. User → POST /integrations/gmail/oauth/start
   ← Authorization URL

2. User → Google OAuth consent screen
   → Grants permissions

3. Google → Redirect to callback URL with code

4. System → POST /integrations/gmail/oauth/callback
   → Exchange code for tokens
   → Store in Secret Manager
   → Create integration record

5. System → Test connection
   → Fetch sample emails
   ← Success confirmation
```

---

## ⏳ Phase 4: Data Ingestion Pipeline (PLANNED)

### Components to Build

#### 1. Gmail Fetcher
```python
# backend/services/orchestrator/integrations/gmail_fetcher.py
class GmailFetcher:
    def fetch_messages(self, integration_id: str, max_results: int = 100):
        # 1. Get credentials from Secret Manager
        # 2. Initialize Gmail API client
        # 3. Fetch messages
        # 4. Parse and store in raw_data
        # 5. Update sync status
```

#### 2. Email Parser
```python
# backend/services/orchestrator/integrations/email_parser.py
class EmailParser:
    def parse_email(self, message: dict) -> dict:
        # Extract subject, body, sender, date
        # Clean HTML content
        # Extract attachments metadata
        # Return structured data
```

#### 3. Data Ingestion
```python
# Store in dna.raw_data table
{
    "entity_id": "...",
    "data_type": "email",
    "data_content": "...",
    "meta_data": {
        "subject": "...",
        "from": "...",
        "date": "...",
        "integration_id": "..."
    }
}
```

### Data Flow
```
Gmail API → GmailFetcher → EmailParser → dna.raw_data
    ↓
Orchestrator → Task Manager → DNA Engine
    ↓
Analysis → Insights → Memory System
```

---

## 📊 Architecture Impact

### New Components Added
1. **Database:** `dna.entity_integrations` table (16 total tables now)
2. **Utility:** `CredentialsManager` class
3. **API Router:** `IntegrationsRouter`
4. **Model:** `EntityIntegration`

### Updated Components
1. **Entity Model:** Added `integrations` relationship
2. **Orchestrator Service:** Included integrations router
3. **Project Documentation:** Updated all relevant docs

### Infrastructure Requirements
- **GCP Secret Manager:** Store encrypted credentials
- **OAuth 2.0 Credentials:** For Gmail, GitHub, etc.
- **API Scopes:** Define permissions for each service

---

## 🔐 Security Implementation

### ✅ Implemented
- Credentials stored in GCP Secret Manager (encrypted at rest)
- No plaintext credentials in database
- Separation of metadata (DB) and secrets (Secret Manager)
- Unique constraint per entity/service
- HTTPS/TLS for all API calls

### 🔜 To Implement
- API authentication (future)
- Rate limiting on endpoints
- Audit logging for credential access
- Automatic token refresh
- Expired token handling
- Webhook validation for OAuth callbacks

---

## 📈 Success Metrics

### Phase 1 (Infrastructure) ✅
- ✅ Database table created
- ✅ SQLAlchemy model implemented
- ✅ CredentialsManager utility complete
- ✅ API endpoints functional
- ✅ Documentation complete

### Phase 2 (Deployment) 🔄
- [ ] Migration applied successfully
- [ ] Service deployed without errors
- [ ] API endpoints accessible
- [ ] Health checks passing
- [ ] OpenAPI docs generated

### Phase 3 (Gmail Integration) ⏳
- [ ] OAuth flow working
- [ ] Credentials stored securely
- [ ] Emails fetched successfully
- [ ] Data stored in raw_data
- [ ] DNA analysis triggered

### Phase 4 (Data Ingestion) ⏳
- [ ] Email parser working
- [ ] Data quality validated
- [ ] Sync status tracking
- [ ] Error handling robust
- [ ] Performance acceptable

---

## 🎯 Supported Services Roadmap

### High Priority
1. **Gmail** (Email) - OAuth 2.0
2. **GitHub** (Code) - OAuth 2.0 / Personal Access Token
3. **Google Calendar** (Calendar) - OAuth 2.0

### Medium Priority
4. **Notion** (Docs) - OAuth 2.0
5. **Slack** (Chat) - OAuth 2.0
6. **Google Drive** (Files) - OAuth 2.0

### Low Priority
7. **LinkedIn** (Social) - OAuth 2.0
8. **Twitter/X** (Social) - OAuth 2.0
9. **Spotify** (Music) - OAuth 2.0

---

## 🧪 Testing Plan

### Unit Tests
- `test_credentials_manager.py`
  - Test store/retrieve/update/delete
  - Test Secret Manager integration
  - Test error handling

### Integration Tests
- `test_integrations_api.py`
  - Test all CRUD endpoints
  - Test OAuth flow
  - Test sync trigger

### End-to-End Tests
- `test_gmail_integration.py`
  - Test complete OAuth flow
  - Test email fetching
  - Test data ingestion
  - Test DNA analysis trigger

---

## 📚 Files Created/Modified

### New Files Created
1. `backend/shared/migrations/002_add_entity_integrations.sql`
2. `backend/shared/models/integrations.py`
3. `backend/shared/utils/credentials_manager.py`
4. `backend/shared/utils/__init__.py`
5. `backend/services/orchestrator/routers/integrations.py`
6. `backend/services/orchestrator/routers/__init__.py`
7. `docs/CREDENTIALS_ARCHITECTURE.md`
8. `docs/SPRINT_5_CREDENTIALS_UPDATE.md` (this file)

### Modified Files
1. `backend/shared/models/__init__.py` - Added EntityIntegration import
2. `backend/shared/models/dna.py` - Added integrations relationship
3. `backend/shared/migrations/001_init_schemas.sql` - Added migrations table
4. `backend/services/orchestrator/main.py` - Included integrations router
5. `docs/PROJECT_STATUS_DASHBOARD.md` - Updated table count

---

## 🔄 Integration with Existing Sprint 5 Plan

The original Sprint 5 plan focused on:
1. Integration Testing
2. End-to-End Workflow Testing
3. Performance Testing
4. Quality Assurance
5. Monitoring & Observability

**Updated Priority:**
1. **Credentials Management** (NEW - Highest Priority)
2. Gmail Integration (NEW)
3. Data Ingestion Pipeline (NEW)
4. Integration Testing (Original)
5. End-to-End Testing (Original)

**Rationale:** Before we can test the complete system, we need NUCLEUS to have access to real user data. The credentials management system enables this.

---

## 🚀 Next Actions

### Immediate (Today)
1. ✅ Complete code implementation
2. 🔄 Review and test locally
3. 🔄 Commit and push to GitHub
4. 🔄 Monitor deployment

### Short-term (This Week)
1. ⏳ Apply database migration
2. ⏳ Verify deployment
3. ⏳ Test API endpoints
4. ⏳ Set up Gmail OAuth credentials
5. ⏳ Implement OAuth flow

### Medium-term (Next Week)
1. ⏳ Test with real Gmail account
2. ⏳ Build email fetcher
3. ⏳ Integrate with DNA engine
4. ⏳ Add GitHub integration
5. ⏳ Begin original Sprint 5 testing tasks

---

## 💡 Philosophy Alignment

### Empty Shell ✅
The credentials system enables NUCLEUS to build itself from the user's actual digital footprint, not just conversations.

### Foundation Prompt ✅
- **DNA Distillation:** Learn from emails, code, documents
- **DNA Realization:** Use external data to achieve goals
- **Quality of Life:** Automate data gathering and analysis

### Progressive Autonomy ✅
With access to external services, NUCLEUS can:
- Proactively gather information
- Learn continuously from user's activities
- Suggest actions based on real data

---

**Last Updated:** December 9, 2025  
**Author:** NUCLEUS Development Team  
**Status:** Phase 1 Complete ✅, Phase 2 In Progress 🔄
