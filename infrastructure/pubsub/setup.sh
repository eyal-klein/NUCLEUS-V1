#!/bin/bash
# NUCLEUS Pub/Sub Infrastructure Setup
# Run this script to create all required Pub/Sub topics and subscriptions

set -e

PROJECT_ID="${GCP_PROJECT_ID:-thrive-system1}"
REGION="${GCP_REGION:-us-central1}"

echo "🚀 Setting up NUCLEUS Pub/Sub infrastructure..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# ============================================
# Create Topics
# ============================================

echo ""
echo "📨 Creating Pub/Sub Topics..."

# Main event topics
gcloud pubsub topics create nucleus-digital-events \
    --project=$PROJECT_ID \
    --labels=project=nucleus,layer=ingestion,type=events \
    2>/dev/null || echo "Topic nucleus-digital-events already exists"

gcloud pubsub topics create nucleus-health-events \
    --project=$PROJECT_ID \
    --labels=project=nucleus,layer=ingestion,type=events \
    2>/dev/null || echo "Topic nucleus-health-events already exists"

gcloud pubsub topics create nucleus-social-events \
    --project=$PROJECT_ID \
    --labels=project=nucleus,layer=ingestion,type=events \
    2>/dev/null || echo "Topic nucleus-social-events already exists"

# Dead letter topics
gcloud pubsub topics create nucleus-digital-events-dlq \
    --project=$PROJECT_ID \
    --labels=project=nucleus,layer=ingestion,type=dlq \
    2>/dev/null || echo "Topic nucleus-digital-events-dlq already exists"

gcloud pubsub topics create nucleus-health-events-dlq \
    --project=$PROJECT_ID \
    --labels=project=nucleus,layer=ingestion,type=dlq \
    2>/dev/null || echo "Topic nucleus-health-events-dlq already exists"

gcloud pubsub topics create nucleus-social-events-dlq \
    --project=$PROJECT_ID \
    --labels=project=nucleus,layer=ingestion,type=dlq \
    2>/dev/null || echo "Topic nucleus-social-events-dlq already exists"

echo "✅ Topics created!"

# ============================================
# Create Push Subscriptions
# ============================================

echo ""
echo "📬 Creating Push Subscriptions..."

# Note: Replace SERVICE_URL with actual Cloud Run service URL after deployment
# These will be created by the GitHub Actions workflow after service deployment

echo "⚠️  Push subscriptions will be created after consumer service deployment"
echo "   Run setup-subscriptions.sh after deploying ingestion-event-consumer"

# ============================================
# Create Pull Subscriptions (for debugging/monitoring)
# ============================================

echo ""
echo "🔍 Creating Pull Subscriptions (for debugging)..."

gcloud pubsub subscriptions create nucleus-digital-events-debug \
    --topic=nucleus-digital-events \
    --project=$PROJECT_ID \
    --ack-deadline=60 \
    --message-retention-duration=7d \
    --labels=project=nucleus,type=debug \
    2>/dev/null || echo "Subscription nucleus-digital-events-debug already exists"

gcloud pubsub subscriptions create nucleus-health-events-debug \
    --topic=nucleus-health-events \
    --project=$PROJECT_ID \
    --ack-deadline=60 \
    --message-retention-duration=7d \
    --labels=project=nucleus,type=debug \
    2>/dev/null || echo "Subscription nucleus-health-events-debug already exists"

gcloud pubsub subscriptions create nucleus-social-events-debug \
    --topic=nucleus-social-events \
    --project=$PROJECT_ID \
    --ack-deadline=60 \
    --message-retention-duration=7d \
    --labels=project=nucleus,type=debug \
    2>/dev/null || echo "Subscription nucleus-social-events-debug already exists"

echo "✅ Debug subscriptions created!"

# ============================================
# Grant Permissions
# ============================================

echo ""
echo "🔐 Setting up IAM permissions..."

# Get the default compute service account
SA_EMAIL="${PROJECT_ID}@appspot.gserviceaccount.com"

# Grant Pub/Sub Publisher role to service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/pubsub.publisher" \
    --condition=None \
    2>/dev/null || echo "Publisher role already granted"

# Grant Pub/Sub Subscriber role to service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/pubsub.subscriber" \
    --condition=None \
    2>/dev/null || echo "Subscriber role already granted"

echo "✅ IAM permissions configured!"

# ============================================
# Summary
# ============================================

echo ""
echo "============================================"
echo "🎉 NUCLEUS Pub/Sub Infrastructure Ready!"
echo "============================================"
echo ""
echo "Topics created:"
echo "  - nucleus-digital-events (Gmail, Calendar)"
echo "  - nucleus-health-events (Oura, Apple Watch)"
echo "  - nucleus-social-events (LinkedIn)"
echo ""
echo "Dead Letter Topics:"
echo "  - nucleus-digital-events-dlq"
echo "  - nucleus-health-events-dlq"
echo "  - nucleus-social-events-dlq"
echo ""
echo "Debug Subscriptions:"
echo "  - nucleus-digital-events-debug"
echo "  - nucleus-health-events-debug"
echo "  - nucleus-social-events-debug"
echo ""
echo "Next steps:"
echo "  1. Deploy ingestion-event-consumer service"
echo "  2. Run setup-subscriptions.sh to create push subscriptions"
echo "  3. Deploy connector services"
echo ""
