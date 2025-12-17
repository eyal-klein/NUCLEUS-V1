# NUCLEUS V1.2 - Credentials System Deployment Guide

**Date:** December 9, 2025  
**Commit:** a5339e8  
**Status:** ✅ Code Pushed, ⏳ Awaiting Deployment

---

## 🎯 What Was Just Deployed

### Code Changes
- ✅ **13 files** changed (1,607 insertions)
- ✅ **8 new files** created
- ✅ **5 files** modified
- ✅ Committed and pushed to GitHub

### New Capabilities
1. **Credentials Management System** - Store and manage external service credentials
2. **Integrations API** - Full CRUD for managing integrations
3. **Secret Manager Integration** - Secure credential storage
4. **Database Schema Update** - New `entity_integrations` table

---

## 🚀 Next Steps for Deployment

### Step 1: Monitor GitHub Actions ⏳

The push to `main` will trigger the **Orchestrator Service** workflow automatically.

**Check deployment status:**
```bash
# Open in browser
https://github.com/eyal-klein/NUCLEUS-V1/actions

# Or use GitHub CLI
gh run list --workflow=orchestrator.yml --limit 1
gh run watch
```

**Expected workflow:**
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Run health checks
5. ✅ Success

---

### Step 2: Apply Database Migration 🔄

**IMPORTANT:** The migration must be applied manually to the production database.

#### Option A: Using Cloud SQL Proxy (Recommended)

```bash
# 1. Start Cloud SQL Proxy
cloud_sql_proxy -instances=thrive-system1:us-central1:nucleus-v12=tcp:5432

# 2. In another terminal, run migration
psql -h localhost -p 5432 -U nucleus -d nucleus_v12 \
  -f backend/shared/migrations/002_add_entity_integrations.sql

# 3. Verify migration
psql -h localhost -p 5432 -U nucleus -d nucleus_v12 -c "
  SELECT * FROM public.migrations ORDER BY executed_at DESC LIMIT 5;
"

# 4. Verify table exists
psql -h localhost -p 5432 -U nucleus -d nucleus_v12 -c "
  SELECT COUNT(*) FROM dna.entity_integrations;
"
```

#### Option B: Using gcloud SQL Connect

```bash
# 1. Connect to Cloud SQL
gcloud sql connect nucleus-v12 --user=nucleus --database=nucleus_v12

# 2. Run migration
\i backend/shared/migrations/002_add_entity_integrations.sql

# 3. Verify
SELECT * FROM public.migrations WHERE version = '002';
SELECT COUNT(*) FROM dna.entity_integrations;

# 4. Exit
\q
```

---

### Step 3: Verify Deployment ✅

Once GitHub Actions completes and migration is applied:

#### 1. Test Health Endpoint
```bash
# Get service URL from Cloud Run console or:
SERVICE_URL=$(gcloud run services describe nucleus-orchestrator \
  --region=us-central1 \
  --format='value(status.url)')

# Test health
curl $SERVICE_URL/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "orchestrator",
  "version": "1.0.0"
}
```

#### 2. Test Integrations Endpoint
```bash
# List integrations (should be empty)
curl $SERVICE_URL/integrations/
```

**Expected response:**
```json
[]
```

#### 3. View API Documentation
```bash
# Open in browser
open $SERVICE_URL/docs
```

**Expected:** Interactive Swagger UI with new `/integrations/` endpoints

---

### Step 4: Test Creating an Integration 🧪

#### Prepare Test Data

Create a test file `test_integration.json`:
```json
{
  "entity_id": "YOUR_ENTITY_ID_HERE",
  "service_name": "test_service",
  "service_type": "test",
  "display_name": "Test Integration",
  "description": "Testing credentials system",
  "credential_type": "api_key",
  "credentials": {
    "api_key": "test_key_12345"
  },
  "config": {
    "test_mode": true
  }
}
```

#### Get Your Entity ID

```bash
# Connect to database
psql -h localhost -p 5432 -U nucleus -d nucleus_v12

# Get entity ID
SELECT id, name FROM dna.entity;

# Copy the UUID and update test_integration.json
```

#### Create Test Integration

```bash
# Create integration
curl -X POST $SERVICE_URL/integrations/ \
  -H "Content-Type: application/json" \
  -d @test_integration.json
```

**Expected response:**
```json
{
  "id": "uuid-here",
  "entity_id": "your-entity-id",
  "service_name": "test_service",
  "service_type": "test",
  "status": "active",
  ...
}
```

#### Verify in Database

```bash
# Check database
psql -h localhost -p 5432 -U nucleus -d nucleus_v12 -c "
  SELECT id, service_name, status, created_at 
  FROM dna.entity_integrations;
"
```

#### Verify in Secret Manager

```bash
# List secrets
gcloud secrets list --filter="name:nucleus-credentials"

# View secret metadata (not the actual secret)
gcloud secrets describe nucleus-credentials-YOUR_ENTITY_ID-test_service
```

#### Clean Up Test

```bash
# Get integration ID from response
INTEGRATION_ID="uuid-from-response"

# Delete test integration
curl -X DELETE $SERVICE_URL/integrations/$INTEGRATION_ID
```

---

## 🔐 Set Up Gmail OAuth (Next Phase)

### Prerequisites
1. Google Cloud Console access
2. OAuth consent screen configured
3. OAuth 2.0 credentials created

### Steps

#### 1. Configure OAuth Consent Screen

```bash
# Open Google Cloud Console
open https://console.cloud.google.com/apis/credentials/consent?project=thrive-system1
```

**Settings:**
- User Type: Internal (for testing) or External (for production)
- App name: NUCLEUS V1.2
- User support email: Your email
- Developer contact: Your email
- Scopes: 
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/userinfo.email`

#### 2. Create OAuth 2.0 Credentials

```bash
# Open credentials page
open https://console.cloud.google.com/apis/credentials?project=thrive-system1
```

**Create OAuth 2.0 Client ID:**
- Application type: Web application
- Name: NUCLEUS Gmail Integration
- Authorized redirect URIs:
  - `http://localhost:8080/integrations/gmail/oauth/callback` (for testing)
  - `https://YOUR_SERVICE_URL/integrations/gmail/oauth/callback` (for production)

**Save:**
- Client ID
- Client Secret

#### 3. Store OAuth Credentials in Secret Manager

```bash
# Create secret for OAuth client credentials
echo '{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "YOUR_REDIRECT_URI"
}' | gcloud secrets create nucleus-gmail-oauth-client \
  --data-file=- \
  --replication-policy=automatic
```

---

## 📊 Verification Checklist

### Deployment Verification
- [ ] GitHub Actions workflow completed successfully
- [ ] Orchestrator service deployed to Cloud Run
- [ ] Health endpoint returns 200 OK
- [ ] API documentation accessible at `/docs`

### Database Verification
- [ ] Migration 002 applied successfully
- [ ] `public.migrations` table shows version 002
- [ ] `dna.entity_integrations` table exists
- [ ] All indexes created
- [ ] Trigger function created

### Functionality Verification
- [ ] Can create test integration
- [ ] Integration stored in database
- [ ] Credentials stored in Secret Manager
- [ ] Can list integrations
- [ ] Can get specific integration
- [ ] Can update integration
- [ ] Can delete integration
- [ ] Secret deleted when integration deleted

### Security Verification
- [ ] No credentials in database (only secret_path)
- [ ] Secret Manager permissions correct
- [ ] API endpoints accessible
- [ ] No sensitive data in logs

---

## 🐛 Troubleshooting

### Issue: GitHub Actions Fails

**Check:**
```bash
gh run list --workflow=orchestrator.yml --limit 1
gh run view --log
```

**Common issues:**
- Docker build errors → Check Dockerfile
- Permission errors → Check service account permissions
- Import errors → Check Python dependencies

**Fix:**
```bash
# Make code changes
git add .
git commit -m "fix: Your fix description"
git push origin main
```

---

### Issue: Migration Fails

**Check:**
```bash
# View PostgreSQL logs
gcloud sql operations list --instance=nucleus-v12 --limit=10
```

**Common issues:**
- Table already exists → Use `IF NOT EXISTS` (already in migration)
- Permission denied → Check user permissions
- Syntax error → Validate SQL syntax

**Fix:**
```bash
# If migration partially applied, rollback manually
psql -h localhost -p 5432 -U nucleus -d nucleus_v12

# Drop table if needed
DROP TABLE IF EXISTS dna.entity_integrations CASCADE;

# Re-run migration
\i backend/shared/migrations/002_add_entity_integrations.sql
```

---

### Issue: API Endpoints Not Working

**Check:**
```bash
# View service logs
gcloud run services logs read nucleus-orchestrator \
  --region=us-central1 \
  --limit=50
```

**Common issues:**
- Import errors → Check Python imports
- Database connection → Check Cloud SQL connection
- Secret Manager access → Check IAM permissions

**Debug:**
```bash
# SSH into Cloud Run (if possible) or check logs
# Look for Python tracebacks
# Check environment variables
```

---

## 📈 Success Metrics

### Phase 2 Complete When:
- ✅ GitHub Actions deployment successful
- ✅ Database migration applied
- ✅ All API endpoints working
- ✅ Test integration created and deleted successfully
- ✅ Credentials stored in Secret Manager
- ✅ No errors in logs

### Ready for Phase 3 When:
- ✅ OAuth consent screen configured
- ✅ OAuth credentials created
- ✅ OAuth credentials stored in Secret Manager
- ✅ All Phase 2 success criteria met

---

## 🎯 Current Status

### ✅ Completed
- [x] Code implementation
- [x] Documentation
- [x] Git commit
- [x] Git push to GitHub

### 🔄 In Progress
- [ ] GitHub Actions deployment
- [ ] Database migration

### ⏳ Pending
- [ ] Deployment verification
- [ ] Integration testing
- [ ] Gmail OAuth setup

---

## 📞 Need Help?

### Check Logs
```bash
# GitHub Actions
gh run view --log

# Cloud Run
gcloud run services logs read nucleus-orchestrator --region=us-central1 --limit=100

# Cloud SQL
gcloud sql operations list --instance=nucleus-v12

# Secret Manager
gcloud secrets list
```

### Useful Commands
```bash
# Get service URL
gcloud run services describe nucleus-orchestrator --region=us-central1 --format='value(status.url)'

# Get database connection
gcloud sql instances describe nucleus-v12 --format='value(connectionName)'

# List secrets
gcloud secrets list --filter="name:nucleus"

# View API docs
open $(gcloud run services describe nucleus-orchestrator --region=us-central1 --format='value(status.url)')/docs
```

---

**Last Updated:** December 9, 2025  
**Commit:** a5339e8  
**Next Action:** Monitor GitHub Actions deployment
